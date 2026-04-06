from backend.tools.jobs.runners.run_async import run_async
from backend.tools.jobs.tasks.taxa import update_ns_ranks
from backend.core.logging import setup_logging, tasks_logger
from backend.data_util.db import get_single_db_connection


async def main():
    setup_logging()

    tasks_logger.info("Starting update_ns_ranks...")

    conn = await get_single_db_connection()

    await update_ns_ranks(conn)

    tasks_logger.info("update_ns_ranks finished")

if __name__ == "__main__":
    run_async(main())
