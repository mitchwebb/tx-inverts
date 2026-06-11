from backend.data_util.db import get_single_db_connection
from backend.jobs.tasks.database import update_indexes
from backend.jobs.tasks.initialize_db import initialize_all_tables
from backend.jobs.tasks.regions import update_observation_regions
from backend.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.jobs.tasks.occurrence import update_observations
from backend.jobs.tasks.views import refresh_materialized_views
from backend.core.logging import tasks_logger
import os


# Automatically update observations table from GBIF
# This function grabs new records (determined by latest modified date value currently in table)
# and ALSO grabs all records with no modified date (as there is no way to vet these)
async def update_database():
    conn = None
    try:
        # Insert to database
        conn = await get_single_db_connection()

        # Quick check to make sure tables are created
        await initialize_all_tables(conn)

        # Make sure indexes are ready
        await update_indexes(conn)
        await conn.commit()

        # Update observations, returning new taxon_keys and row_ids
        backbone_update_required, new_row_keys, new_row_ids = await update_observations()

        await update_observation_regions(conn, new_row_ids)

        if backbone_update_required:
            await update_backbone()
            # A bit deceptive, but new_row_keys == None means update ALL rows
            new_row_keys = None

        # Update conservation ranks
        await update_ns_ranks(conn, new_row_keys)

        # Refresh the materialized views
        await refresh_materialized_views(conn)

        await update_indexes(conn)

        await conn.commit()

    except Exception as e:
        tasks_logger.exception(f'Update database task failed. Exiting. {e}')
        if conn is not None:
            await conn.rollback()
    finally:
        if conn is not None:
            await conn.close()
