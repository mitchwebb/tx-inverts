from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.update_database import update_database
from backend.core.logging import setup_logging, tasks_logger


async def main():
    setup_logging()
    tasks_logger.info("Starting update_database job...")

    await update_database()

    tasks_logger.info("update_database job finished")


if __name__ == "__main__":
    run_async(main())
