from backend.core.logging import setup_logging, tasks_logger
from backend.data_util.db import get_single_db_connection
from backend.tools.jobs.runners import run_async
from backend.tools.jobs.tasks.datasets import fill_dataset_table


async def main():
    setup_logging()
    tasks_logger.info("Starting fill_dataset_table job...")

    conn = await get_single_db_connection()

    await fill_dataset_table(conn)

    tasks_logger.info("fill_dataset_table job finished")


if __name__ == "__main__":
    run_async(main())
