import os
from backend.constants.paths import DATA_OUT_PATH
from backend.data_util.db import get_single_db_connection
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.occurrence_tasks import update_observations
from backend.core.logging import setup_logging
from backend.core.logging import tasks_logger
from backend.jobs.tasks.region_tasks import update_observation_regions
from backend.jobs.tasks.taxon_tasks import update_ns_ranks
from backend.jobs.tasks.index_tasks import update_indexes
from backend.jobs.tasks.view_tasks import refresh_materialized_views


async def main():
    conn = None

    try:
        setup_logging()
        tasks_logger.info("Starting update_occurrences job...")

        conn = await get_single_db_connection()

        _, new_row_keys, affected_observation_ids = await update_observations(conn)

        await update_ns_ranks(conn, new_row_keys)

        await update_observation_regions(conn, affected_observation_ids)

        # Refresh the materialized views
        await refresh_materialized_views(conn)

        await update_indexes(conn)

        tasks_logger.info("update_occurrences job finished")

    except Exception as e:
        tasks_logger.exception(f"Update_occurrences task failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
    finally:
        if conn is not None:
            await conn.close()


if __name__ == '__main__':
    run_async(main())
