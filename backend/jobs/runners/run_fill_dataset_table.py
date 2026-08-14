from backend.core.logging import setup_logging, tasks_logger
from backend.data_util.db import get_single_db_connection
from backend.data_util.gbif.observations_request import APPROVED_DATASETS
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.dataset_tasks import fill_dataset_table
from backend.jobs.tasks.table_tasks import initialize_table


async def main():
    """
    Job to create and fill dataset metadata table.
    Calls table initialization and fill_dataset_table functions.
    """

    conn = None
    try:
        setup_logging()
        tasks_logger.info("Starting fill_dataset_table job...")

        conn = await get_single_db_connection()

        await initialize_table(conn, GBIF_DATASET_META)

        await fill_dataset_table(conn, APPROVED_DATASETS)

        tasks_logger.info("fill_dataset_table job finished")
    except Exception as e:
        tasks_logger.exception(f"Fill dataset table task failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
        raise
    finally:
        if conn is not None:
            await conn.close()


if __name__ == '__main__':
    run_async(main())
