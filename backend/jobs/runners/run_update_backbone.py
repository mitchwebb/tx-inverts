from backend.data_util.db import get_single_db_connection
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.taxa import create_invasives_table, update_backbone, update_ns_ranks
from backend.core.logging import setup_logging, tasks_logger


# Run full update of backbone, starting from scratch download
# Also replaces invasives table
async def main():

    conn = await get_single_db_connection()

    try:
        setup_logging()
        tasks_logger.info("Starting update_backbone job...")

        await create_invasives_table(truncate=True)
        await update_backbone()
        await update_ns_ranks(conn)

        tasks_logger.info("update_backbone job finished")

    except Exception as e:
        tasks_logger.exception(f'Update_backbone task failed. Exiting. {e}')
        if conn is not None:
            await conn.rollback()
    finally:
        if conn is not None:
            await conn.close()

if __name__ == "__main__":
    run_async(main())
