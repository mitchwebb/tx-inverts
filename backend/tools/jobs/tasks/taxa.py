from backend.config.data import DATA_OUT_PATH
from backend.data_util.db import get_single_db_connection
from backend.data_util.download_large_file import download_large_file
from backend.data_util.extract_zip import extract_zip_files
from backend.data_util.invasives import get_invasives_dataset, prep_invasives_dataset
import backend.data_util.natureserve as ns
from backend.data_util.taxa import build_lineages_numpy
from backend.db_schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db_schema.tx_taxa import TX_TAXA_TABLE
from backend.db_schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.models.update_status import UpdateStatus
from backend.tools.jobs.tasks.initialize_db import initialize_table
from backend.tools.jobs.tasks.views import refresh_materialized_view
from backend.core.logging import data_logger, db_logger
import csv
import os
import io
import pandas as pd
import psycopg
from psycopg import sql, AsyncConnection
from typing import List, Optional
from backend.models.sql import SingleTaxonOccurrenceFilter


# TODO: This might as well be included in taxonomic updates, given that if
# the backbone is updated, the taxonIDs for these species will be as well
# TODO: Should I run a truncate? Or allow it, at least?
async def create_invasives_table():
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
    copy_sql = sql.SQL('''
        COPY {invasives_table} ({column_order})
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
    ''').format(
        invasives_table=sql.Identifier(US_INVASIVES_TABLE.name),
        column_order=sql.SQL(', ').join(map(sql.Identifier, columns))
    )

    async with conn.cursor() as cur:
        async with cur.copy(copy_sql) as copy:
            await copy.write(buffer.getvalue())


async def update_invasives(conn):
    async with conn.cursor() as cur:
        # Mark invasive species
        await cur.execute(sql.SQL('''
            UPDATE {backbone} b
            SET us_invasive = TRUE
            FROM {invasives_table} i
            WHERE i.taxon_id = COALESCE(b.accepted_name_usage_id, b.taxon_id);
        ''').format(
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            invasives_table=sql.Identifier(US_INVASIVES_TABLE.name)
        ))

        # Unmark species marked TRUE that should not be
        await cur.execute(sql.SQL('''
            UPDATE {backbone} b
            SET us_invasive = FALSE
            WHERE us_invasive = TRUE
            AND NOT EXISTS (
                SELECT 1
                FROM {invasives_table} i
                WHERE i.taxon_id = COALESCE(b.accepted_name_usage_id, b.taxon_id)
            );
        ''').format(
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            invasives_table=sql.Identifier(US_INVASIVES_TABLE.name)
        ))


# Perform a full update of the gbif_backbone in local database

# TODO: This script is used to update the backbone taxonomy in the database.
# TODO: This will need to update indexes, materialized views, and I need to
# TODO: Consider whether and updated backbone will require a full update of
# TODO: the GBIF observations table. Perhaps this is a reason to use last_interpreted?

# TODO: Takes about 10 minutes with the GBIF backbone
async def update_backbone(fp=None, force_refresh: bool = False) -> UpdateStatus:
    """
    Updates the gbif_inverts_backbone table if there are changes in the GBIF backbone.

    Returns:
        True if the backbone was updated (and ns_rank_state should be recalculated),
        False if no changes were detected.
    """

    # If no filepath provided, download and extract
    if fp == None:
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
    data_logger.info('Building taxonomic lineages to fill rank id columns...')
    df = build_lineages_numpy(df)

    data_logger.info('Verifying format...')
    GBIF_INVERTS_BACKBONE.validate_columns(df)

    df.to_csv(os.path.join(
        DATA_OUT_PATH, 'taxa_cleaned.csv'), sep="\t", index=False)

    # Clear memory immediately (probably unnecessary)
    del df
    import gc
    gc.collect()

    temp_table_name = "temp_" + GBIF_INVERTS_BACKBONE.name

    async with conn.cursor() as cur:
        # Make sure table exists
        await initialize_table(conn, GBIF_INVERTS_BACKBONE, verbose=True)

        db_logger.info('Creating temp table for insertion...')
        # Create temp table without indexes/constraints for faster COPY
        await cur.execute(
            sql.SQL('CREATE TEMP TABLE {temp_table} (LIKE {backbone_table} INCLUDING DEFAULTS)').format(
                temp_table=sql.Identifier(temp_table_name),
                backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            )
        )

        copy_sql = sql.SQL('''
            COPY {temp_table} FROM STDIN 
            WITH (
                FORMAT csv, 
                DELIMITER E'\t', 
                HEADER true, 
                NULL '')
        ''').format(temp_table=sql.Identifier(temp_table_name))

        # Copying to temp table
        with open(os.path.join(DATA_OUT_PATH, 'taxa_cleaned.csv'), "r", encoding="utf8") as f:
            async with cur.copy(copy_sql) as copy:
                while chunk := f.read(1024*1024):
                    await copy.write(chunk)

        # If force_refresh, skip comparison and replace directly
        # Flag UpdateStatus as ALL
        if force_refresh:
            db_logger.info(
                'force_refresh is TRUE. Overwriting previous table...')
            await cur.execute(sql.SQL("TRUNCATE TABLE {backbone_table}").format(
                backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            ))
            await cur.execute(
                sql.SQL('INSERT INTO {backbone_table} SELECT * FROM {temp_table}').format(
                    backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                    temp_table=sql.Identifier(temp_table_name)
                )
            )

            # Update invasives column in backbone
            await update_invasives(conn)

            # TODO: We should have a step that checks on/initializes all relevant indexes before this next step

            await refresh_materialized_view(conn, 'tx_taxa')
            await refresh_materialized_view(conn, 'taxon_region_presence')

            await conn.commit()

            return True

        # TODO: This isn't useful. It's simply slowing the process. However, if we can compare the tables BEFORE the lineage work is done, this would save time.
        # Check if temp differs from main table (EXCEPT)
        db_logger.info('Comparing new and old backbones...')
        await cur.execute(
            sql.SQL('''
                SELECT EXISTS (
                    SELECT 1 FROM (
                        SELECT * FROM {main_table}
                        EXCEPT
                        SELECT * FROM {temp_table}
                        UNION
                        SELECT * FROM {temp_table}
                        EXCEPT
                        SELECT * FROM {main_table}
                    ) AS diffs
                )
            ''').format(
                main_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                temp_table=sql.Identifier(temp_table_name),
            )
        )
        (changed,) = await cur.fetchone()

        # If there are no changes, skip update
        if not changed:
            db_logger.info('No changes found, update skipped.')
            # No changes, skip update
            return False

        # Else if changes found, replace table
        else:
            db_logger.info('Changes found in backbone, replacing backbone...')
            await cur.execute(sql.SQL('TRUNCATE TABLE {backbone_table}').format(
                backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            ))
            await cur.execute(sql.SQL('INSERT INTO {backbone_table} SELECT * FROM {temp_table}').format(
                backbone_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                temp_table=sql.Identifier(temp_table_name)
            ))

            # Update invasives column
            await update_invasives(conn)

            # Refresh materialized view
            await refresh_materialized_view(conn, 'tx_taxa')
            await refresh_materialized_view(conn, 'taxon_region_presence')

            await conn.commit()

            return True


async def update_normalized_names(conn: AsyncConnection):
    async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("""
            ALTER TABLE gbif_inverts_backbone
            ADD COLUMN IF NOT EXISTS normalized_name text;

            UPDATE gbif_inverts_backbone
            SET normalized_name = LOWER(canonical_name)
            WHERE canonical_name IS NOT NULL
                AND (normalized_name IS NULL OR normalized_name = '');
        """)


# TODO: This needs to be updated to only work on taxa that are shared between tables
async def update_ns_ranks(conn: AsyncConnection, taxon_keys: Optional[List[int]] = None) -> None:
    """
    Update NatureServe ranks for selected (or all) taxa

    conn (AsyncConnection): Active async DB connection
    taxon_keys (int[]): List of taxon_keys to update (if None, updates all)
    """

    try:
        columns_to_check = ['ns_rank_state', 'ns_rank_state_no_inat']

        # Check for both relevant columns and add them if they don't exist
        async with conn.cursor() as cur:
            db_logger.info('Checking for rank columns...')
            for col_name in columns_to_check:
                # Check if the column exists
                await cur.execute(sql.SQL('''
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = {backbone} AND column_name = {col_name}
                ''').format(
                    backbone=sql.Literal(GBIF_INVERTS_BACKBONE.name),
                    col_name=sql.Literal(col_name)
                ))

                if await cur.fetchone() is None:
                    # Add the missing column
                    await cur.execute(sql.SQL(
                        'ALTER TABLE {} ADD COLUMN {} TEXT'
                    ).format(
                        sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                        sql.Identifier(col_name)
                    ))
                    db_logger.info(
                        f'Added blank {col_name} column to {GBIF_INVERTS_BACKBONE.name}')

        # Refreshing tx_taxa materialized view to make sure we're getting full list of taxa
        await refresh_materialized_view(conn, 'tx_taxa')
        # Refresh taxon_lineage view to help with speed
        await refresh_materialized_view(conn, 'taxon_lineage')

        # If taxon_keys are provided, selected only those for update (from tx_taxa table)
        if taxon_keys:
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
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
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
        async with conn.cursor() as cur:
            # Avoid setting rank if the taxon is not for a species
            await cur.executemany(
                sql.SQL("""
                    UPDATE {}
                    SET ns_rank_state = %s,
                        ns_rank_state_no_inat = %s
                    WHERE taxon_id = %s AND taxon_rank = 'species'
                """).format(sql.Identifier(GBIF_INVERTS_BACKBONE.name)),
                [(rank_with, rank_without, taxon_id)
                 for taxon_id, rank_with, rank_without in rank_assignments]
            )

        # Refreshing tx_taxa materialized view to add ranks from backbone_table
        await refresh_materialized_view(conn, 'tx_taxa')
        await conn.commit()

        data_logger.info("NatureServe rank updates complete.")
    except Exception as e:
        data_logger.exception(f"Failed to update NS ranks: {e}")
        await conn.rollback()
        raise
