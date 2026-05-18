from backend.constants.paths import DATA_OUT_PATH
from backend.data_util.db import get_single_db_connection
from backend.data_util.download_large_file import download_large_file
from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.extract_zip import extract_zip_files
from backend.data_util.invasives import get_invasives_dataset, prep_invasives_dataset
import backend.data_util.natureserve as ns
from backend.data_util.taxa import build_lineages_numpy
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.tools.jobs.tasks.initialize_db import initialize_table
from backend.tools.jobs.tasks.views import refresh_materialized_view
from backend.core.logging import data_logger, db_logger
import csv
import os
import io
import pandas as pd
from psycopg import sql, AsyncConnection
from typing import List, Optional
from backend.models.sql import SingleTaxonOccurrenceFilter


# TODO: This might as well be included in taxonomic updates, given that if
# the backbone is updated, the taxonIDs for these species will be as well
# TODO: Should I run a truncate? Or allow it, at least?
async def create_invasives_table():
    conn = None
    try:
        fp = await get_invasives_dataset()

        df = await prep_invasives_dataset(fp)

        df = US_INVASIVES_TABLE.coerce_dataframe(df)
        US_INVASIVES_TABLE.validate_columns(df)

        columns = US_INVASIVES_TABLE.column_order()

        buffer = io.StringIO()
        df.to_csv(buffer, index=False, sep='\t', header=False, na_rep='\\N')
        buffer.seek(0)

        conn = await get_single_db_connection()

        # Sql for copying to table
        copy_sql = sql.SQL("""
            COPY {invasives_table} ({column_order})
            FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
        """).format(
            invasives_table=sql.Identifier(US_INVASIVES_TABLE.name),
            column_order=sql.SQL(', ').join(map(sql.Identifier, columns))
        )

        # Using raw cursor for copy
        async with conn.cursor() as cur:
            async with cur.copy(copy_sql) as copy:
                await copy.write(buffer.getvalue())

        await conn.commit()
    except Exception as e:
        if conn is not None:
            await conn.rollback()
        db_logger.error(f'Failed to create invasives table: {e}')
    finally:
        if conn is not None:
            await conn.close()


async def update_invasives(conn):
    # Mark invasive species
    flag_invasives_query = sql.SQL("""
            UPDATE {backbone} b
            SET us_invasive = TRUE
            FROM {invasives_table} i
            WHERE i.taxon_id = COALESCE(b.accepted_name_usage_id, b.taxon_id);
        """).format(
        backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
        invasives_table=sql.Identifier(US_INVASIVES_TABLE.name)
    )

    await execute_psql_query(conn, flag_invasives_query)

    # Correct any incorrectly marked species (from previous lists)
    unflag_invasives_query = sql.SQL("""
            UPDATE {backbone} b
            SET us_invasive = FALSE
            WHERE us_invasive = TRUE
            AND NOT EXISTS (
                SELECT 1
                FROM {invasives_table} i
                WHERE i.taxon_id = COALESCE(b.accepted_name_usage_id, b.taxon_id)
            );
        """).format(
        backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
        invasives_table=sql.Identifier(US_INVASIVES_TABLE.name)
    )

    await execute_psql_query(conn, unflag_invasives_query)

    await conn.commit()


# Helper for truncating/replacing backbone rows
async def _replace_backbone(conn, temp_table_name: str):
    # Truncate backbone
    truncate_query = sql.SQL("TRUNCATE TABLE {backbone_table}").format(
        backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
    )
    await execute_psql_query(conn, truncate_query)
    # Insert rows
    insert_query = sql.SQL('INSERT INTO {backbone_table} SELECT * FROM {temp_table}').format(
        backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
        temp_table=sql.Identifier(temp_table_name)
    )
    await execute_psql_query(conn, insert_query)
    # Update invasives information in new table
    await update_invasives(conn)
    # Refresh materialized views dependent on table
    await refresh_materialized_view(conn, 'tx_taxa')
    await refresh_materialized_view(conn, 'taxon_region_presence')
    await conn.commit()


# Perform a full update of the gbif_backbone in local database
async def update_backbone(fp=None):
    """
    Updates the gbif_inverts_backbone table
    """

    conn = None

    try:
        # If no filepath provided, download and extract
        if fp is None:
            data_logger.info('Downloading backbone from gbif...')
            zip_path = download_large_file(
                'https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip',
                output_fp=os.path.join(DATA_OUT_PATH, 'backbone_test.zip')
            )
            extract_dir = DATA_OUT_PATH

            # Extract Taxon.tsv from backbone
            extract_zip_files(zip_path, extract_dir, target_files=[
                'Taxon.tsv'], delete_zip=True)

            fp = os.path.join(extract_dir, 'Taxon.tsv')

        data_logger.info('Reading backbone...')
        df = pd.read_csv(
            fp,
            delimiter='\t',
            # no quoting expected (this was causing our parsing errors)
            quoting=csv.QUOTE_NONE,
            on_bad_lines='warn',
            low_memory=True
        )

        # List of exceptional chordate invertebrates
        chordate_inverts = ['Thaliacea', 'Ascidiacea',
                            'Appendicularia', 'Leptocardii']

        # Create filter mask
        mask = (
            (df['kingdom'] == 'Animalia') &
            (
                (df['phylum'] != 'Chordata') |
                (df['class'].isin(chordate_inverts))
            )
        )

        data_logger.info('Filtering to inverts...')
        # Apply mask
        df = df[mask]

        # Add empty ns_rank_state column
        df['ns_rank_state'] = pd.NA

        # Fit dataframe to table definition
        data_logger.info('Formatting table...')
        df = df.rename(
            columns={'specificEpithet': 'species',
                     'infraspecificEpithet': 'subspecies'}
        )

        df = GBIF_INVERTS_BACKBONE.coerce_dataframe(df)

        conn = await get_single_db_connection()

        # Build taxonomic lineages and insert rank ids into dataframe
        data_logger.info(
            'Building taxonomic lineages to fill rank id columns...')
        df = build_lineages_numpy(df)

        data_logger.info('Verifying format...')
        GBIF_INVERTS_BACKBONE.validate_columns(df)

        df.to_csv(os.path.join(
            DATA_OUT_PATH, 'taxa_cleaned.csv'), sep="\t", index=False)

        temp_table_name = "temp_" + GBIF_INVERTS_BACKBONE.name

        # Make sure table exists
        await initialize_table(conn, GBIF_INVERTS_BACKBONE, verbose=True)

        db_logger.info('Creating temp table for insertion...')
        # Create temp table without indexes/constraints for faster COPY
        create_query = sql.SQL('CREATE TEMP TABLE {temp_table} (LIKE {backbone_table} INCLUDING DEFAULTS)').format(
            temp_table=sql.Identifier(temp_table_name),
            backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
        await execute_psql_query(conn, create_query)

        # Copy to temp table
        # Using raw cursor for copy
        async with conn.cursor() as cur:
            db_logger.info('Copying to temp table...')
            copy_sql = sql.SQL("""
                COPY {temp_table} FROM STDIN
                WITH (
                    FORMAT csv,
                    DELIMITER E'\t',
                    HEADER true,
                    NULL '')
            """).format(temp_table=sql.Identifier(temp_table_name))

            with open(os.path.join(DATA_OUT_PATH, 'taxa_cleaned.csv'), "r", encoding="utf8") as f:
                async with cur.copy(copy_sql) as copy:
                    while chunk := f.read(1024*1024):
                        await copy.write(chunk)

        # Replace backbone
        db_logger.info('Replacing backbone...')

        await _replace_backbone(conn, temp_table_name)

        await conn.commit()

    except Exception as e:
        db_logger.error(f'Error updating backbone: {e}')
        if conn is not None:
            await conn.rollback()
        raise


async def update_ns_ranks(conn: AsyncConnection, taxon_keys: Optional[List[int]] = None) -> None:
    """
    Update NatureServe ranks for selected (or all) taxa

    conn (AsyncConnection): Active async DB connection
    taxon_keys (int[]): List of taxon_keys to update (if None, updates all)
    """

    try:
        columns_to_check = ['ns_rank_state', 'ns_rank_state_no_inat']

        # Check for both relevant columns and add them if they don't exist
        db_logger.info('Checking for rank columns...')
        for col_name in columns_to_check:
            # Check if the column exists
            check_col_query = sql.SQL("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = {backbone} AND column_name = {col_name}
            """).format(
                backbone=sql.Literal(GBIF_INVERTS_BACKBONE.name),
                col_name=sql.Literal(col_name)
            )

            result = await execute_psql_query(conn, check_col_query, fetch='one')

            # If column missing
            if result is None:
                # Add the missing column
                add_col_query = sql.SQL(
                    'ALTER TABLE {backbone} ADD COLUMN {col} TEXT'
                ).format(
                    backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                    col=sql.Identifier(col_name)
                )

                await execute_psql_query(conn, add_col_query)
                db_logger.info(
                    f'Added blank {col_name} column to {GBIF_INVERTS_BACKBONE.name}')

        # Commit possible column changes
        await conn.commit()

        # Refreshing tx_taxa materialized view to make sure we're getting full list of taxa
        await refresh_materialized_view(conn, 'tx_taxa')
        # Refresh taxon_lineage view to help with speed
        await refresh_materialized_view(conn, 'taxon_lineage')

        # If taxon_keys are provided, selected only those for update (from tx_taxa table)
        if taxon_keys is not None:
            query = sql.SQL("""
                SELECT taxon_id
                FROM {tx_taxa}
                WHERE taxon_id = ANY({taxon_keys}) AND taxon_rank = 'species'
            """).format(
                tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
                taxon_keys=sql.Literal(taxon_keys)
            )

        # Else, select all taxon_ids (from tx_taxa table)
        else:
            query = sql.SQL("""
                SELECT taxon_id
                FROM {tx_taxa}
                WHERE taxon_rank = 'species'
            """).format(
                tx_taxa=sql.Identifier(TX_TAXA_TABLE.name)
            )

        # Get taxon_ids
        rows = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)
        taxa_to_update: List[int] = [row['taxon_id'] for row in rows]

        if not taxa_to_update:
            data_logger.info("No taxa to update for NatureServe ranks.")
            return

        total = len(taxa_to_update)

        data_logger.info(f"Updating NatureServe ranks for {total} taxa...")

        # Get list of taxon_ids and ranks for batch update
        rank_assignments: List[tuple[int, str, str]] = []

        # Calcuate ranks for all taxa (with and without inat)
        for index, taxon_id in enumerate(taxa_to_update):
            # Update every 100 taxa or at the beginning and end
            if index % 100 == 0 or index == total - 1:
                data_logger.info(
                    f"Processing taxon {index + 1}/{total} (id={taxon_id})")

            ranks = []

            # Calculate values for taxa with inat observations and without
            for include_inat in [True, False]:

                filters = SingleTaxonOccurrenceFilter(
                    taxon_id=taxon_id,
                    include_inat=include_inat,
                )

                values = await ns.calculate_ns_values(conn, filters)
                # If there are no occurrences, rank uncertain
                rank = (
                    ns.calculate_rank(
                        values['number_of_occurrences'],
                        values['range_extent_km2'],
                        values['area_of_occupancy_4km2_bins']
                    ) if values else 'U'
                )
                ranks.append(rank)

            # Append tuple: (taxon_id, rank_with, rank_without)
            rank_assignments.append((taxon_id, ranks[0], ranks[1]))

        # Bulk update all ranks
        # Avoid setting rank if the taxon is not for a species
        query = sql.SQL("""
            UPDATE {backbone_table}
            SET ns_rank_state = %s,
                ns_rank_state_no_inat = %s
            WHERE taxon_id = %s AND taxon_rank = 'species'
        """).format(
            backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name))

        await execute_psql_query(
            conn,
            query,
            params=[(rank_with, rank_without, taxon_id)
                    for taxon_id, rank_with, rank_without in rank_assignments],
            batch=True
        )

        # Refreshing tx_taxa materialized view to add ranks from backbone_table
        await refresh_materialized_view(conn, 'tx_taxa')
        await conn.commit()

        data_logger.info("NatureServe rank updates complete.")
    except Exception as e:
        data_logger.exception(f"Failed to update NS ranks: {e}")
        await conn.rollback()
        raise
