from backend.tools.jobs.tasks.update_database import update_database
from backend.core.logging import setup_logging, tasks_logger

import asyncio


def main():
    setup_logging()
    tasks_logger.info("Starting update_database job...")

    asyncio.run(update_database())

    tasks_logger.info("update_database job finished")


if __name__ == "__main__":
    main()
