from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.occurrence import update_observations
from backend.core.logging import setup_logging
from backend.core.logging import tasks_logger
import asyncio


async def main():
    setup_logging()
    tasks_logger.info("Starting update_occurrences job...")

    await update_observations()

    tasks_logger.info("update_occurrences job finished")


if __name__ == "__main__":
    run_async(main())
