import io
import json
import os
import pandas as pd
import psycopg
import time

from backend.config import get_settings
from backend.config.data import DATA_OUT_PATH
from backend.core.logging import db_logger, data_logger
from backend.data_util.db import get_single_db_connection
from backend.data_util.gbif import (
    gbif_downloads,
    get_latest_record_date,
    observations_request,
    process_observations,
)
from backend.db_schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.models.update_status import UpdateStatus
from backend.tools.jobs.tasks.initialize_db import initialize_table
from backend.tools.jobs.tasks.views import refresh_materialized_views
from psycopg import sql
from typing import List, Optional, Tuple


async def update_observations(
    fp: str = None,
    gbif_request_key: str = None,
    chunk_size: int = 1000000,
    full_replace: bool = False,
    save_cleaned_data: bool = False,
    verbose: bool = False
) -> Tuple[UpdateStatus, Optional[List[int]]]:
    '''
        Perform PARTIAL update of gbif_observations table

        Uses either local file or gbif download to insert new observations
        based on latest 'modified' value in gbif_observations table, as well
        as all records with null 'modified' value (as there is no way to vet these)

        Will overwrite db observation rows which share a gbif_id

        Args:
            fp (str): Filepath to observations csv (if provided, function will NOT make a new GBIF request)
            gbif_request_key (str): Key returned by gbif download request. Can be used if a request was already made.
            chunk_size (int): Chunk size to be used when reading in CSV for data cleaning
            full_replace (bool): If True, operation will replace observations table with new data
            save_cleaned_data (bool): If True, cleaned data will be saved in data/cleaned directory after processing,
            verbose (bool)
    '''

    settings = get_settings()

    conn = await get_single_db_connection()

    # If filepath provided, use local file
    if fp:
        observations_fp = fp
    # Else, use GBIF
    else:
        # If gbif_request_key provided, use this key to get download
        if gbif_request_key:
            key = gbif_request_key

        # Else, create new request
        else:
            kwargs = {'min_date_type': 'modified'}

            if full_replace:
                data_logger.info(
                    'Full replace selected—requesting all records from GBIF...')
            else:
                db_logger.info(
                    'Getting minimum modified date from observations table...')
                min_date = await get_latest_record_date.get_latest_record_date(conn, 'modified')
                kwargs['min_date'] = min_date
                data_logger.info(
                    f'Using min modified date for GBIF request: {min_date}')

            # Request a GBIF download
            request_body = observations_request.build_observations_request(
                **kwargs)

            key = gbif_downloads.gbif_download_request(
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
            time_to_wait=2400
        )
        observations_fp = os.path.join(output_dir, 'occurrence.txt')

    if full_replace:
        db_logger.info(
            'Full replace requested. Truncating observations table...')
        async with conn.cursor() as cur:
            await cur.execute(sql.SQL('TRUNCATE {}').format(
                sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            ))
        backboneUpdateRequired = True  # Probably true in this case, doesn't cost a lot

    try:
        async with conn.cursor() as cur:
            # Create temp table to perform data update/merge
            temp_table_name = 'temp_' + GBIF_OBSERVATIONS_TABLE.name

            # Make sure gbif_observations_table exists
            await initialize_table(conn, GBIF_OBSERVATIONS_TABLE, verbose=True)

            db_logger.info('Creating temp table for insertion...')
            # Create temp table without indexes/constraints for faster COPY
            await cur.execute(sql.SQL('''
                CREATE TEMP TABLE {temp_table}
                (LIKE {observations_table} INCLUDING DEFAULTS)
            ''').format(
                temp_table=sql.Identifier(temp_table_name),
                observations_table=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name)
            ))

            db_logger.info('Adding batch_id columns...')
            # Add batch_id column for batch processing these chunks
            await cur.execute(sql.SQL('''
                ALTER TABLE {temp_table}
                ADD COLUMN IF NOT EXISTS batch_id bigint;
            ''').format(temp_table=sql.Identifier(temp_table_name)))

            db_logger.info('Creating index on batch_id')
            # Create index on batch_id
            await cur.execute(sql.SQL('''
                CREATE INDEX IF NOT EXISTS idx_temp_batch
                ON {temp_table} (batch_id);
            ''').format(temp_table=sql.Identifier(temp_table_name)))

        # TODO: This should return chunks, and the rest of the process should operate in chunks
        # Transform data
        for chunk in process_observations.process_dwc_observations(
            observations_fp,
            chunk_size,
        ):

            # Overwrite species/subspecies with epithet columns if they exist
            for target, source in [('species', 'specificEpithet'), ('subspecies', 'infraspecificEpithet')]:
                if source in chunk.columns:
                    # If target column exists, overwrite with source; else create it
                    chunk[target] = chunk[source]

            # Get rid of lingering 'specific' columns
            chunk = chunk.drop(columns=[c for c in [
                               'specificEpithet', 'infraspecificEpithet'] if c in chunk.columns])

            chunk = GBIF_OBSERVATIONS_TABLE.coerce_dataframe(chunk)
            GBIF_OBSERVATIONS_TABLE.validate_columns(chunk)

            # Set geometry to None for the copy operation as it doesn't cooperate with the COPY FROM method
            chunk['geometry'] = None

            data_logger.info('Converting valid dates to ISO format...')
            for col in ['collection_start_date', 'collection_end_date']:
                # Convert valid dates to ISO strings, leave missing as None
                chunk[col] = pd.to_datetime(chunk[col], errors='coerce').dt.date

            # Get a list of taxon ids that will be affected by this update
            new_row_keys = chunk['accepted_taxon_key'].unique().tolist()

            async with conn.cursor() as cur:
                batch_id = time.time_ns()

                # Use current batch_id in next copy
                await cur.execute(sql.SQL('''
                    ALTER TABLE {temp_table}
                    ALTER COLUMN batch_id SET DEFAULT {batch_id};
                ''').format(
                    batch_id=sql.Literal(batch_id),
                    temp_table=sql.Identifier(temp_table_name)
                ))

                # Write filtered_df to CSV in-memory buffer
                db_logger.info('Copying to temp table...')

                buffer = io.BytesIO()
                chunk.to_csv(buffer, index=False, sep='\t', na_rep='\\N',
                             header=False, encoding='utf-8')
                buffer.seek(0)

                # Sql for copying to table
                copy_sql = sql.SQL('''
                    COPY {temp_table} ({column_order})
                    FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
                ''').format(
                    temp_table=sql.Identifier(temp_table_name),
                    column_order=sql.SQL(", ").join(
                        map(sql.Identifier, GBIF_OBSERVATIONS_TABLE.column_order()))
                )

                # Run copy statement
                async with cur.copy(copy_sql) as copy:
                    while chunk_data := buffer.read(1024 * 1024):
                        await copy.write(chunk_data)

                buffer.close()

                # Populate geometry in temp table
                db_logger.info('Updating geometry column...')
                await cur.execute(
                    sql.SQL('''
                        UPDATE {temp_table}
                        SET geometry = ST_SetSRID(ST_MakePoint(decimal_longitude, decimal_latitude), 4326)
                        WHERE batch_id = {batch_id}
                            AND decimal_latitude IS NOT NULL
                            AND decimal_longitude IS NOT NULL
                    ''').format(
                        temp_table=sql.Identifier(temp_table_name),
                        batch_id=sql.Literal(batch_id)
                    ))

                db_logger.info('Filter by Texas Shapefile...')
                await cur.execute(
                    sql.SQL('''
                        DELETE FROM {temp_table}
                        WHERE batch_id={batch_id}
                            AND NOT ST_Within(
                                geometry,
                                (SELECT geometry FROM geometries WHERE geometry_name = 'Texas')
                            );
                    ''').format(
                        temp_table=sql.Identifier(temp_table_name),
                        batch_id=sql.Literal(batch_id)
                    ))

        db_logger.info('Updating lineage columns in temp table...')
        async with conn.cursor() as cur:

            db_logger.info('Creating necessary indexes on temp table...')
            await cur.execute(sql.SQL('''
                CREATE INDEX ON {temp} (gbif_id);
                CREATE INDEX ON {temp} (accepted_taxon_key);
                CREATE INDEX ON {temp} (taxon_key);
            ''').format(temp=sql.Identifier(temp_table_name)))

            # Drop batch_id from temp table so INSERT matches target
            await cur.execute(sql.SQL('''
                ALTER TABLE {temp_table} DROP COLUMN IF EXISTS batch_id
            ''').format(temp_table=sql.Identifier(temp_table_name)))

            db_logger.info('Creating temp table for lineage...')
            # Create temp table of resolved lineage keys
            await cur.execute(sql.SQL('''
                CREATE TEMP TABLE resolved_keys AS
                    -- Step 1: resolve the true accepted taxon key for each observation
                    SELECT
                        obs.gbif_id,
                        COALESCE(b1.accepted_name_usage_id, b1.taxon_id, b2.accepted_name_usage_id, b2.taxon_id) AS resolved_taxon_key
                    FROM {temp_table} AS obs
                    LEFT JOIN {backbone} AS b1
                        ON obs.accepted_taxon_key = b1.taxon_id
                    LEFT JOIN {backbone} AS b2
                        ON obs.accepted_taxon_key = b2.accepted_name_usage_id
                ;''').format(
                temp_table=sql.Identifier(temp_table_name),
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            ))

            db_logger.info('Creating index on gbif_id...')
            # Index on gbif_id for insert
            await cur.execute(sql.SQL('''
                CREATE INDEX idx_resolved_gbif ON resolved_keys(gbif_id);'''
                                      ))

            db_logger.info('Writing lineages to temp_table...')
            # Apply lineages to temp table
            await cur.execute(sql.SQL('''
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
            ''').format(
                temp_table=sql.Identifier(temp_table_name),
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            ))

        # If full_replace is true, add all observations
        if full_replace:
            db_logger.info(
                'Adding all accepted observations to observations table...')
            async with conn.cursor() as cur:
                await cur.execute(sql.SQL('''
                    INSERT INTO {observations_table}
                    SELECT * FROM {temp_table}
                ''').format(
                    observations_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    temp_table=sql.Identifier(temp_table_name),
                    cols=sql.SQL(', ').join(
                        map(sql.Identifier, GBIF_OBSERVATIONS_TABLE.column_order()))
                ))

        # Else, compare old and new rows, replacing only those with altered information
        else:
            # Compare accepted_taxon_key values to see if backbone needs to be updated
            db_logger.info('Comparing accepted_taxon_keys for changes...')
            async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                await cur.execute(sql.SQL('''
                    SELECT COUNT(*) AS changed_taxa
                    FROM {observations_table} old
                    JOIN {temp_table} new ON old.gbif_id = new.gbif_id
                    WHERE old.accepted_taxon_key IS DISTINCT FROM new.accepted_taxon_key
                    AND old.taxon_key = new.taxon_key
                ''').format(
                    observations_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    temp_table=sql.Identifier(temp_table_name)
                ))
                changed = (await cur.fetchone())['changed_taxa']

                # If updated rows with updated accepted_taxon_keys exist, warn...
                if changed > 0:
                    db_logger.warning(f'''
                        ⚠ Detected {changed} observations with changed accepted_taxon_keys.
                        This suggests the backbone may be outdated and should be updated.
                    ''')
                    backboneUpdateRequired = True
                else:
                    backboneUpdateRequired = False

                await cur.execute(sql.SQL('''
                    SELECT COUNT(*) AS new_row_count FROM {temp_table}
                ''').format(temp_table=sql.Identifier(temp_table_name)))
                new_row_count = (await cur.fetchone())['new_row_count']

                # Now update main table
                db_logger.info(f'Rows to copy: {new_row_count}')

                # Populate observations table with new rows from temp table
                # Replace rows with matching gbif_ids

                # Delete matching rows
                await cur.execute(sql.SQL('''
                    DELETE FROM {observations_table} o
                    USING {temp_table} t
                    WHERE o.gbif_id = t.gbif_id;
                ''').format(
                    observations_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    temp_table=sql.Identifier(temp_table_name)
                ))

                db_logger.info('Inserting new rows...')
                # Insert all rows from temp table
                await cur.execute(sql.SQL('''
                    INSERT INTO {observations_table}
                    SELECT * FROM {temp_table}
                ''').format(
                    observations_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    temp_table=sql.Identifier(temp_table_name),
                    cols=sql.SQL(', ').join(
                        map(sql.Identifier, GBIF_OBSERVATIONS_TABLE.column_order()))
                ))

        # Refresh materialized views
        db_logger.info('Refreshing materialized views...')
        await refresh_materialized_views(conn)

        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Check for missing taxon_ids
            await cur.execute(sql.SQL('''
                SELECT DISTINCT o.accepted_taxon_key
                    FROM {temp_table} o
                LEFT JOIN {backbone} b
                    ON o.accepted_taxon_key = b.taxon_id
                WHERE b.taxon_id IS NULL;
            ''').format(
                temp_table=sql.Identifier(temp_table_name),
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            ))

            missing_taxa = await cur.fetchall()
            missing_keys = [row['accepted_taxon_key'] for row in missing_taxa]
            missing_count = len(missing_keys)

            if missing_count > 0:
                db_logger.warning(f'''
                        ⚠ {missing_count} accepted_taxon_keys not found in backbone. Examples: {missing_keys[:10]}
                        This means the backbone is out of date and needs to be resynced! ⚠
                ''')

            await conn.commit()

            return (backboneUpdateRequired, new_row_keys or None)

    except Exception as e:
        await conn.rollback()
        data_logger.exception(f'Issue with observations update: {e}')
        raise

    finally:
        await conn.close()


async def sync_observations_to_backbone():
    '''
        Resync observations table to current backbone

        This will take the current gbif_inverts_backbone table and,
        using the taxon_id -> accepted_name_usage_id relationship, alter taxon_key
        values in gbif_observations to reflect the current relationships
    '''

    conn = await get_single_db_connection()
    updated_count = 0
    orphaned_keys: list[int] = []

    db_logger.info('Syncing observations to current backbone...')
    try:
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Create temp table of accepted_taxon_keys that need changing
            db_logger.info('Checking for affected observations...')
            await cur.execute(sql.SQL('''
                CREATE TEMP TABLE tmp_update AS
                SELECT o.gbif_id, b.accepted_name_usage_id
                FROM {gbif_observations} o
                JOIN {backbone} b
                    ON o.taxon_key = b.taxon_id
                WHERE NOT (o.accepted_taxon_key = b.taxon_id
                        OR o.accepted_taxon_key = b.accepted_name_usage_id)
            ''').format(
                gbif_observations=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name),
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            ))

            await cur.execute("SELECT COUNT(*) AS n FROM tmp_update;")
            row = await cur.fetchone()
            db_logger.info(f"Rows that actually need updating: {row['n']}")

            # Make a cheeky index to speed up next operation
            await cur.execute("CREATE INDEX ON tmp_update (gbif_id);")

            # Update affected observations rows in gbif_observations
            db_logger.info('Updating affected observations...')
            await cur.execute(sql.SQL('''
                UPDATE {gbif_observations} o
                SET accepted_taxon_key = t.accepted_name_usage_id
                FROM tmp_update t
                WHERE o.gbif_id = t.gbif_id;
            ''').format(gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
                        ))

            updated_count = cur.rowcount
            db_logger.info(f'Updated {updated_count} rows in gbif_observations')

            # Check for taxon_keys in gbif_obseravations with NO match in backbone
            db_logger.info('Checking for orphaned taxa...')
            await cur.execute(sql.SQL('''
                SELECT DISTINCT o.taxon_key as orphaned_keys
                FROM {gbif_observations} o
                LEFT JOIN {backbone} b
                    ON o.taxon_key = b.taxon_id
                WHERE b.taxon_id is NULL
            ''').format(
                gbif_observations=sql.Identifier(
                    GBIF_OBSERVATIONS_TABLE.name),
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
            ))

            rows = await cur.fetchall()
            orphaned_keys = [row['orphaned_keys'] for row in rows]

            if len(orphaned_keys) > 0:
                db_logger.warning(
                    f'Orphaned taxa found in occurrences! Examples: {orphaned_keys[:10]}')

            await conn.commit()

    except Exception as e:
        # Rollback on error
        await conn.rollback()
        db_logger.exception(f'Error during resync: {e}')
        raise

    finally:
        await conn.close()

    return {
        "updated_rows": updated_count,
        "orphaned_keys": orphaned_keys,
    }
