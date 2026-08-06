from datetime import date
import io
import json
import os
import pandas as pd
import time

from pandas import DataFrame
from backend.constants.paths import DATA_OUT_PATH
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.config import get_settings
from backend.core.logging import db_logger, data_logger
from backend.data_util.gbif import (
    gbif_downloads,
    get_latest_record_date,
    observations_request,
    process_observations,
)
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.jobs.tasks.table_tasks import initialize_table
from backend.jobs.tasks.view_tasks import refresh_materialized_views
from psycopg import sql, AsyncConnection
from typing import List, Optional, Tuple


# Helper function to build gbif download request, perform request,
# download the resulting data, unzip, and return fp for occurrences.txt
async def get_gbif_inverts_file(
    conn: AsyncConnection,
    gbif_request_key: str | None = None,
    get_all: bool = False
) -> str:
    """
        Build GBIF inverts request, retrieve, and unzip, returning fp for resulting occurrences.txt.
        If gbif_request_key provided, function will skip the request step.

        Args:
            conn (psycopg.AsyncConnection): AsyncConnection used for db call
            gbif_request_key (str): Key returned by gbif download request. Can be used if a request was previously made
            get_all (bool = False): If True, records will not be filtered by date

        Returns:
            (str) occurrences.txt filepath
    """
    settings = get_settings()

    try:
        # If gbif_request_key provided, use this key to get download
        if gbif_request_key:
            key = gbif_request_key

        # Else, create new request
        else:
            min_date = None
            kwargs: dict[str, str | date] = {'min_date_type': 'modified'}

            # If get_all is True, run a full request for Texas inverts
            if get_all:
                data_logger.info(
                    "Full replace selected—requesting all records from GBIF...")
            # TODO: As GBIF forums have revealed, this is not a trustworthy date—it's not reviewed by GBIF
            # TODO: This can also result in duplicates and stale records, as GBIF doesn't track removed records.
            # TODO: For now, a full replace seems to be the most sensible option, although it feels wasteful
            # Else, filter by latest 'modified' date in observations database
            else:
                db_logger.info(
                    "Getting minimum modified date from observations table...")
                min_date = await get_latest_record_date.get_latest_record_date(conn, 'modified')

                if min_date is not None:
                    kwargs['min_date'] = min_date
                    data_logger.info(
                        f"Using min modified date for GBIF request: {min_date}")

            # Build GBIF request
            # Pylance has a tough time with kwarg types, and this is local, so we're just ignoring
            request_body = observations_request.build_observations_request(
                user=settings.gbif.user,
                email=settings.gbif.email,
                ** kwargs)  # type: ignore[arg-type]

            # Request download and get download key
            key = await gbif_downloads.gbif_download_request(
                request_body=json.dumps(request_body),
                pwd=settings.gbif.password,
                username=settings.gbif.user
            )

        if not key:
            raise RuntimeError("Failed to get GBIF download key")

        # Download and extract data
        output_dir = await gbif_downloads.get_gbif_download(
            key,
            output_fp=DATA_OUT_PATH,
            target_files=['occurrence.txt'],
        )
        observations_fp = os.path.join(output_dir, 'occurrence.txt')

        return observations_fp

    except RuntimeError:
        raise
    except Exception:
        raise


# Helper process for taking processed observations chunk and copying to temp table
async def _load_chunk_into_temp_table(conn: AsyncConnection, df_chunk: DataFrame, table_name: str, batch_id: int):
    # Use current batch_id in next copy (doesn't affect previously inserted values)
    batch_id_query = sql.SQL("""
        ALTER TABLE {temp_table}
        ALTER COLUMN batch_id SET DEFAULT {batch_id};
    """).format(
        batch_id=sql.Literal(batch_id),
        temp_table=sql.Identifier(table_name)
    )
    await execute_psql_query(conn, batch_id_query)

    # Write processed chunk to CSV in-memory buffer
    db_logger.info("Copying to temp table...")
    buffer = io.BytesIO()
    df_chunk.to_csv(buffer, index=False, sep='\t', na_rep='\\N',
                    header=False, encoding='utf-8')
    buffer.seek(0)

    # Copy to table using raw cursor for copy
    async with conn.cursor() as cur:
        copy_sql = sql.SQL("""
            COPY {temp_table} ({column_order})
            FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
        """).format(
            temp_table=sql.Identifier(table_name),
            column_order=sql.SQL(', ').join(
                map(sql.Identifier, GBIF_OBSERVATIONS_TABLE.column_order()))
        )

        # Run copy statement
        async with cur.copy(copy_sql) as copy:
            while chunk_data := buffer.read(1024 * 1024):
                await copy.write(chunk_data)

        buffer.close()
    return


async def _filter_temp_table_chunk(conn: AsyncConnection, table_name: str, batch_id: int):

    # This process is chunked to keep our temp_table slim
    # Populate geometry in temp table
    db_logger.info("Updating geometry column...")
    update_geometry_query = sql.SQL("""
            UPDATE {temp_table}
            SET geometry = ST_SetSRID(ST_MakePoint(decimal_longitude, decimal_latitude), 4326)
            WHERE batch_id = {batch_id}
                AND decimal_latitude IS NOT NULL
                AND decimal_longitude IS NOT NULL
        """).format(
        temp_table=sql.Identifier(table_name),
        batch_id=sql.Literal(batch_id)
    )
    await execute_psql_query(conn, update_geometry_query)

    # We could do this locally, but using the DB ensures that these operations
    # and the frontend operations use the same shape/filtering
    db_logger.info("Filtering by Texas Shapefile...")
    filter_query = sql.SQL("""
            DELETE FROM {temp_table}
            WHERE batch_id={batch_id}
                AND NOT ST_Within(
                    geometry,
                    (SELECT geometry FROM {tx_table} WHERE state = 'Texas')
                );
        """).format(
        tx_table=sql.Identifier(TEXAS_GEOMETRY_TABLE.name),
        temp_table=sql.Identifier(table_name),
        batch_id=sql.Literal(batch_id)
    )
    await execute_psql_query(conn, filter_query)


async def _resolve_taxon_lineage(conn: AsyncConnection, table_name: str):
    # Create a few important indexes on temp table
    db_logger.info("Creating necessary indexes on temp table...")
    for col in ('gbif_id', 'accepted_taxon_key', 'taxon_key'):
        await execute_psql_query(
            conn,
            sql.SQL("CREATE INDEX ON {temp} ({col})").format(
                temp=sql.Identifier(table_name),
                col=sql.Identifier(col)
            )
        )

    # Create indexes on temp table for better traversing ids
    db_logger.info("Updating lineage columns in temp table...")
    # Drop batch_id from temp table so INSERT matches target
    drop_column_query = sql.SQL("""
        ALTER TABLE {temp_table} DROP COLUMN IF EXISTS batch_id
    """).format(temp_table=sql.Identifier(table_name))
    await execute_psql_query(conn, drop_column_query)

    # Create temp table of resolved lineage keys
    db_logger.info("Creating temp table for lineage...")
    create_temp_query = sql.SQL("""
        CREATE TEMP TABLE resolved_keys AS
            SELECT
                obs.gbif_id,
                COALESCE(b1.accepted_name_usage_id, b1.taxon_id, b2.accepted_name_usage_id, b2.taxon_id) AS resolved_taxon_key
            FROM {temp_table} AS obs
            -- Get observation's matching taxon_id from backbone
            LEFT JOIN {backbone} AS b1
                ON obs.accepted_taxon_key = b1.taxon_id
            -- As fallback, get observation's matching accepted_name_usage_id from backbone
            LEFT JOIN {backbone} AS b2
                ON obs.accepted_taxon_key = b2.accepted_name_usage_id
        ;""").format(
        temp_table=sql.Identifier(table_name),
        backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
    )
    await execute_psql_query(conn, create_temp_query)

    db_logger.info("Creating index on gbif_id...")
    # Index on gbif_id for insert
    create_index_query = sql.SQL("""
        CREATE INDEX idx_resolved_gbif ON resolved_keys(gbif_id);
    """)
    await execute_psql_query(conn, create_index_query)

    db_logger.info("Writing lineages to temp_table...")
    # Apply lineages to temp table
    update_lineage_query = sql.SQL("""
        UPDATE {temp_table} t
        SET
            accepted_taxon_key = r.resolved_taxon_key,
            kingdom_id = b.kingdom_id,
            phylum_id = b.phylum_id,
            class_id = b.class_id,
            order_id = b.order_id,
            family_id = b.family_id,
            genus_id = b.genus_id,
            species_id = b.species_id,
            subspecies_id = b.subspecies_id
        FROM resolved_keys r
        JOIN {backbone} b ON b.taxon_id = r.resolved_taxon_key
        WHERE t.gbif_id = r.gbif_id;
    """).format(
        temp_table=sql.Identifier(table_name),
        backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
    )
    await execute_psql_query(conn, update_lineage_query)


async def update_observations(
    conn: AsyncConnection,
    fp: str | None = None,
    gbif_request_key: str | None = None,
    chunk_size: int = 100000,
    full_replace: bool = False,
    delete_file=True
) -> Tuple[bool, Optional[List[int]], Optional[List[int]]]:
    """
        Orchestration function to update gbif_observations table

        Uses either local file or gbif download to insert new observations
        based on latest 'modified' value in gbif_observations table, as well
        as all records with null 'modified' value(as there is no way to vet these)

        Will overwrite db observation rows which share a gbif_id

        Args:
            conn(psycopg.AsyncConnection): Active psycopg async database connection
            fp(str | None=None): Filepath to observations csv(if provided, function will NOT make a new GBIF request)
            gbif_request_key(str | None=None): Key returned by gbif download request. Can be used if a request was already made.
            chunk_size(int=100000): Chunk size to be used when reading in CSV for data cleaning
            full_replace(bool=False): If True, operation will replace observations table with new data
            delete_download(bool=True): If True, downloaded observations file will not be kept


        Returns:
            (backbone_update_suggested, new_row_keys, affected_observation_ids)
    """

    try:
        # Track whether or not we're using a local file or a downloaded file
        using_download = fp is None

        # If no fp to observations file is provided, create GBIF request and download new data
        if fp is None:
            fp = await get_gbif_inverts_file(conn, gbif_request_key, full_replace)

        backbone_update_suggested = False
        affected_observation_ids = []
        new_row_keys = []

        if full_replace:
            # If fully replacing observations, we much first truncate the old table as well as
            # the observations_regions table, as it is a materialized view
            db_logger.info(
                "Full replace requested. Truncating observations (and observations_regions) table...")
            truncate_query = sql.SQL("""
                TRUNCATE {obs_table}, {obs_regions_table}
            """).format(
                obs_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                obs_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name)
            )
            await execute_psql_query(conn, truncate_query)

            # When fully replacing the observations table, it is safest to update the backbone as well
            # Although the backbone doesn't often actually change
            backbone_update_suggested = True

        # Make sure gbif_observations_table exists
        await initialize_table(conn, GBIF_OBSERVATIONS_TABLE, verbose=True)

        # Create temp table to perform data update/merge
        temp_table_name = 'temp_' + GBIF_OBSERVATIONS_TABLE.name
        db_logger.info("Creating temp table for insertion...")
        # No indexes/constraints for faster COPY
        create_query = sql.SQL("""
            CREATE TEMP TABLE {temp_table}
            (LIKE {observations_table} INCLUDING DEFAULTS)
        """).format(
            temp_table=sql.Identifier(temp_table_name),
            observations_table=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name)
        )
        await execute_psql_query(conn, create_query)

        # Add batch_id column for batch processing these chunks
        db_logger.info("Adding batch_id columns...")
        add_col_query = sql.SQL("""
            ALTER TABLE {temp_table}
            ADD COLUMN IF NOT EXISTS batch_id bigint;
        """).format(
            temp_table=sql.Identifier(temp_table_name)
        )
        await execute_psql_query(conn, add_col_query)

        # Create index on batch_id
        db_logger.info("Creating index on batch_id")
        index_query = sql.SQL("""
            CREATE INDEX IF NOT EXISTS idx_temp_batch
            ON {temp_table} (batch_id);
        """).format(temp_table=sql.Identifier(temp_table_name))
        await execute_psql_query(conn, index_query)

        ### Processing, Copying, and Lineage Operations ###

        # Process and transform data in chunks
        for chunk in process_observations.process_dwc_observations(
            fp,
            chunk_size,
        ):
            # Add to list of taxon ids that will be affected by this update (to feed to compiled list)
            new_row_keys.extend(chunk['accepted_taxon_key'].unique().tolist())

            # Create batch_id for this chunk
            batch_id = time.time_ns()

            # Copy chunk to temp table
            await _load_chunk_into_temp_table(conn, chunk, temp_table_name, batch_id)

            # Filter chunk in temp table by Texas Shapefile
            await _filter_temp_table_chunk(conn, temp_table_name, batch_id)

        # Deduplicate new row keys in compiled table
        new_row_keys = list(set(new_row_keys))

        # Resolve and assign taxonomic lineage in complete temp table (for each observation)
        await _resolve_taxon_lineage(conn, temp_table_name)

        ### Insert Operations ###

        # If full_replace is true, add all observations
        if full_replace:
            db_logger.info(
                "Adding all accepted observations to observations table...")
            insert_query = sql.SQL("""
                INSERT INTO {observations_table}
                SELECT * FROM {temp_table}
            """).format(
                observations_table=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name),
                temp_table=sql.Identifier(temp_table_name)
            )
            await execute_psql_query(conn, insert_query)

        # Else, compare old and new rows, replacing only those with altered information
        else:
            # Compare accepted_taxon_key values to see if backbone needs to be updated
            db_logger.info("Comparing accepted_taxon_keys for changes...")
            changed_query = sql.SQL("""
                SELECT COUNT(*) AS changed_taxa
                FROM {observations_table} old
                JOIN {temp_table} new ON old.gbif_id = new.gbif_id
                WHERE old.accepted_taxon_key IS DISTINCT FROM new.accepted_taxon_key
                AND old.taxon_key = new.taxon_key
            """).format(
                observations_table=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name),
                temp_table=sql.Identifier(temp_table_name)
            )
            result = await execute_psql_query(conn, changed_query, fetch='one', dict_cursor=True)
            changed_count = result['changed_taxa'] if result is not None else 0

            # If updated rows with updated accepted_taxon_keys exist, warn...
            if changed_count > 0:
                db_logger.warning(f"""
                    ⚠ Detected {changed_count} observations with changed accepted_taxon_keys.
                    This suggests the backbone may be outdated and should be updated.
                """)
                backbone_update_suggested = True
            else:
                backbone_update_suggested = False

            new_row_query = sql.SQL("""
                SELECT COUNT(*) AS new_row_count FROM {temp_table}
            """).format(temp_table=sql.Identifier(temp_table_name))
            result = await execute_psql_query(conn, new_row_query, fetch='one', dict_cursor=True)
            new_row_count = result['new_row_count'] if result is not None else 0

            # Now update main table
            db_logger.info(f"Rows to copy: {new_row_count}")

            columns = GBIF_OBSERVATIONS_TABLE.column_order()
            update_cols = [c for c in columns if c != 'gbif_id']

            # Populate observations table with new rows from temp table
            # Replace rows with matching gbif_ids
            db_logger.info(
                f"Replacing pre-existing rows and adding new to observations_table...")
            insert_query = sql.SQL("""
                INSERT INTO {observations_table}
                SELECT * FROM {temp_table}
                ON CONFLICT (gbif_id) DO UPDATE SET {updates}
            """).format(
                observations_table=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name),
                temp_table=sql.Identifier(temp_table_name),
                updates=sql.SQL(', ').join(
                    sql.SQL('{col} = EXCLUDED.{col}').format(
                        col=sql.Identifier(c))
                    for c in update_cols
                )
            )
            await execute_psql_query(conn, insert_query)

        # Get list of altered occurrence record ids for updating observations regions table
        db_logger.info("Getting altered occurrence ids...")
        # Get list of new observation ids
        updated_ids_query = sql.SQL("""
                SELECT gbif_id FROM {temp_table}
            """).format(
            temp_table=sql.Identifier(temp_table_name)
        )
        result = await execute_psql_query(
            conn, updated_ids_query, fetch='all', dict_cursor=True)
        affected_observation_ids = [row['gbif_id'] for row in result or []]

        # Refresh materialized views
        db_logger.info("Refreshing materialized views...")
        await refresh_materialized_views(conn)

        # Check occurrence records with missing taxon_id values
        # If any are missing, there's an issue with the backbone!
        missing_id_query = sql.SQL("""
            SELECT DISTINCT o.accepted_taxon_key
                FROM {temp_table} o
            LEFT JOIN {backbone} b
                ON o.accepted_taxon_key = b.taxon_id
            WHERE b.taxon_id IS NULL;
        """).format(
            temp_table=sql.Identifier(temp_table_name),
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )

        missing_taxa = await execute_psql_query(conn, missing_id_query, fetch='all', dict_cursor=True)
        missing_keys = [row['accepted_taxon_key'] for row in missing_taxa or []]
        missing_count = len(missing_keys)

        if missing_count > 0:
            db_logger.warning(f"""
                    ⚠ {missing_count} accepted_taxon_keys not found in backbone. Examples: {missing_keys[:10]}
                    This means the backbone is out of date and needs to be resynced! ⚠
            """)
            backbone_update_suggested = True

        await conn.commit()

        # If we've downloaded a file and delete_file is True, delete it
        if using_download and delete_file:
            os.remove(fp)
            # If parent is empty, remove parent directory as well
            parent_directory = os.path.dirname(os.path.abspath(fp))
            os.rmdir(parent_directory)

        return (backbone_update_suggested, new_row_keys or None, affected_observation_ids or None)

    except Exception as e:
        data_logger.exception(f"Issue with observations update: {e}")
        raise


async def sync_observations_to_backbone(conn: AsyncConnection):
    """
        Resync observations table to current backbone

        This will take the current gbif_inverts_backbone table and,
        using the taxon_id -> accepted_name_usage_id relationship, alter taxon_key
        values in gbif_observations to reflect the current relationships
    """

    updated_count = 0
    orphaned_keys: list[int] = []

    db_logger.info("Syncing observations to current backbone...")
    try:
        # Create temp table of accepted_taxon_keys that need changing
        db_logger.info("Checking for affected observations...")
        create_table_query = sql.SQL("""
            CREATE TEMP TABLE tmp_update AS
            SELECT o.gbif_id, b.accepted_name_usage_id
            FROM {gbif_observations} o
            JOIN {backbone} b
                ON o.taxon_key = b.taxon_id
            WHERE NOT (o.accepted_taxon_key = b.taxon_id
                    OR o.accepted_taxon_key = b.accepted_name_usage_id)
        """).format(
            gbif_observations=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name),
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
        await execute_psql_query(conn, create_table_query)

        # Get count of rows that need changing
        row_count = await execute_psql_query(
            conn,
            query=sql.SQL("SELECT COUNT(*) AS n FROM tmp_update;"),
            fetch='one',
            dict_cursor=True
        )

        db_logger.info(
            f"Rows that actually need updating: {row_count['n'] if row_count is not None else 0}")

        # Make a cheeky index to speed up next operation
        await execute_psql_query(conn, sql.SQL("CREATE INDEX ON tmp_update (gbif_id);"))

        # Update affected observations rows in gbif_observations
        db_logger.info("Updating affected observations...")
        # Using raw cursor here to access rowcount
        async with conn.cursor() as cur:
            await cur.execute(sql.SQL("""
                UPDATE {gbif_observations} o
                SET accepted_taxon_key = t.accepted_name_usage_id
                FROM tmp_update t
                WHERE o.gbif_id = t.gbif_id;
            """).format(gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)))

            updated_count = cur.rowcount
            db_logger.info(
                f"Updated {updated_count} rows in gbif_observations")

        # Check for taxon_keys in gbif_obseravations with NO match in backbone
        db_logger.info("Checking for orphaned taxa...")
        orphans_query = sql.SQL("""
            SELECT DISTINCT o.taxon_key as orphaned_keys
            FROM {gbif_observations} o
            LEFT JOIN {backbone} b
                ON o.taxon_key = b.taxon_id
            WHERE b.taxon_id is NULL
        """).format(
            gbif_observations=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name),
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
        rows = await execute_psql_query(conn, orphans_query, fetch='all', dict_cursor=True) or []
        orphaned_keys = [row['orphaned_keys'] for row in rows]

        if len(orphaned_keys) > 0:
            db_logger.warning(
                f"Orphaned taxa found in occurrences! Examples: {orphaned_keys[:10]}")

        await conn.commit()

    except Exception as e:
        if conn is not None:
            # Rollback on error
            await conn.rollback()
        db_logger.exception(f"Error during resync: {e}")
        raise

    return {
        'updated_rows': updated_count,
        'orphaned_keys': orphaned_keys,
    }
