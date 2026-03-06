from backend.tools.jobs.tasks.occurrence import update_observations
from backend.core.logging import setup_logging
from backend.core.logging import tasks_logger
import asyncio

def main():
    setup_logging()
    tasks_logger.info("Starting update_occurrences job...")

    asyncio.run(update_observations())

    tasks_logger.info("update_occurrences job finished")


if __name__ == "__main__":
    main()