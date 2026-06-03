from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.taxa import update_ns_ranks
from backend.core.logging import setup_logging, tasks_logger
from backend.data_util.db import get_single_db_connection


async def main():
    conn = None
    try:
        setup_logging()
        tasks_logger.info("Starting update_ns_ranks...")
        conn = await get_single_db_connection()

        await update_ns_ranks(conn)

        tasks_logger.info("update_ns_ranks finished")
    except Exception as e:
        tasks_logger.exception(f'Update NS ranks task failed. Exiting. {e}')
        if conn is not None:
            await conn.rollback()
    finally:
        if conn is not None:
            await conn.close()

if __name__ == "__main__":
    run_async(main())
