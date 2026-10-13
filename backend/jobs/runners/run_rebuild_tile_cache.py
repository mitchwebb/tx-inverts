import asyncio

from backend.data_util.db import get_single_db_connection
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.tiles_cache_tasks import rebuild_tile_cache
from backend.core.logging import setup_logging, tasks_logger


async def main():
    """
    Wipes and re-warms large taxa tiles in the taxon_tile_cache
    """

    conn = None
    try:
        setup_logging()
        tasks_logger.info(
            "Starting rebuild_tile_cache job (this can take 30+ minutes)...")

        conn = await get_single_db_connection()
        await rebuild_tile_cache(conn)

        tasks_logger.info("Tile cache rebuild complete")

    except asyncio.CancelledError:
        tasks_logger.warning("Tile cache rebuild cancelled")
        raise
    except Exception as e:
        tasks_logger.exception(f"Tile cache rebuild task failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
        raise
    finally:
        if conn is not None:
            await conn.close()


if __name__ == '__main__':
    run_async(main())
