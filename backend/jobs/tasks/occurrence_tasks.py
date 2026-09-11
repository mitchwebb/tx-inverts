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
    observations_request,
    process_observations,
)
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.table_tasks import initialize_table
from backend.jobs.tasks.view_tasks import refresh_materialized_view, refresh_materialized_views
from psycopg import sql, AsyncConnection
from typing import List, Optional, Tuple


# Helper function to build gbif download request, perform request,
# download the resulting data, unzip, and return fp for occurrences.txt
async def get_gbif_inverts_file(
    gbif_request_key: str | None = None,
    test: bool = False
) -> str:
    """
        Build GBIF inverts request, retrieve, and unzip, returning fp for resulting occurrences.txt.
        If gbif_request_key provided, function will skip the request step.

        Args:
            gbif_request_key (str): Key returned by gbif download request. Can be used if a request was previously made
            test (bool = False): If True, request builder will use a subset of data

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
            data_logger.info(
                "Requesting all inverts records from GBIF...")

            # Build GBIF request
            # Pylance has a tough time with kwarg types, and this is local, so we're just ignoring
            request_body = observations_request.build_observations_request(
                user=settings.gbif.user,
                email=settings.gbif.email,
                test=test
            )

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
            FROM STDIN WITH (
                FORMAT CSV, 
                DELIMITER E'\t', 
                NULL '\\N'
            )
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
    db_logger.info(
        "Updating geometry column and filtering by Texas shapefile...")
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


async def update_observations(
    conn: AsyncConnection,
    fp: str | None = None,
    gbif_request_key: str | None = None,
    chunk_size: int = 100000,
    delete_file=False
):
    """
        Orchestration function to fully update gbif_observations table.

        Uses either local file or gbif download to fully replace observations.

        Args:
            conn(psycopg.AsyncConnection): Active psycopg async database connection
            fp(str | None=None): Filepath to observations csv(if provided, function will NOT make a new GBIF request)
            gbif_request_key(str | None=None): Key returned by gbif download request. Can be used if a request was already made.
            chunk_size(int=100000): Chunk size to be used when reading in CSV for data cleaning
            delete_file(bool=False): If True, observations file will not be kept
    """

    try:
        # If no fp to observations file is provided, create GBIF request and download new data
        if fp is None:
            fp = await get_gbif_inverts_file(gbif_request_key)

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
            # Create batch_id for this chunk
            batch_id = time.time_ns()

            # Copy chunk to temp table
            await _load_chunk_into_temp_table(conn, chunk, temp_table_name, batch_id)

            # Filter chunk in temp table by Texas Shapefile
            await _filter_temp_table_chunk(conn, temp_table_name, batch_id)

        # Create a few important indexes on temp table
        db_logger.info("Creating necessary indexes on temp table...")
        for col in ('gbif_id', 'accepted_taxon_key', 'taxon_key'):
            await execute_psql_query(
                conn,
                sql.SQL("CREATE INDEX ON {temp} ({col})").format(
                    temp=sql.Identifier(temp_table_name),
                    col=sql.Identifier(col)
                )
            )

        # Drop batch_id from temp table so INSERT matches target
        drop_column_query = sql.SQL("""
            ALTER TABLE {temp_table} DROP COLUMN IF EXISTS batch_id
        """).format(temp_table=sql.Identifier(temp_table_name))
        await execute_psql_query(conn, drop_column_query)

        ### Insert Operations ###

        # Truncate the old observations table as well as the observations_regions table, as it is a materialized view
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

        # Warn about backbone update
        db_logger.warning(
            "Observations table is being fully replaced—it is safest to accompany this with a backbone update.")

        db_logger.info(
            "Adding all accepted observations to observations table. For a full replacement, this can take around 25 minutes...")
        insert_query = sql.SQL("""
            INSERT INTO {observations_table}
            SELECT * FROM {temp_table}
        """).format(
            observations_table=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name),
            temp_table=sql.Identifier(temp_table_name)
        )
        await execute_psql_query(conn, insert_query)

        # Refresh dependant materialized views
        db_logger.info("Refreshing materialized views...")
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
        await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)

        await conn.commit()

        # If delete_file is True, delete the file
        if delete_file:
            os.remove(fp)
            # If parent is empty, remove parent directory as well
            parent_directory = os.path.dirname(os.path.abspath(fp))
            if not os.listdir(parent_directory):
                os.rmdir(parent_directory)

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

        # Check for taxon_keys in gbif_observations with NO match in backbone
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
