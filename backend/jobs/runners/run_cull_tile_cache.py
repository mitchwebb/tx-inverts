import asyncio

from backend.constants.tiles import TILE_CACHE_MAX_BYTES, TILE_CACHE_TARGET_BYTES
from backend.data_util.db import get_single_db_connection
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.tiles_cache_tasks import cull_tile_cache
from backend.core.logging import setup_logging, tasks_logger


async def main():
    """
    Culls tile cache to a specified limit if over a specified max.
    """

    conn = None
    try:
        setup_logging()
        tasks_logger.info(
            "Starting cull_tile_cache job...")

        conn = await get_single_db_connection()
        await cull_tile_cache(conn, target_bytes=TILE_CACHE_TARGET_BYTES, max_bytes=TILE_CACHE_MAX_BYTES)

        tasks_logger.info("Tile cache culling complete")

    except asyncio.CancelledError:
        tasks_logger.warning("Tile cache culling cancelled")
        raise
    except Exception as e:
        tasks_logger.exception(f"Tile cache culling task failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
        raise
    finally:
        if conn is not None:
            await conn.close()


if __name__ == '__main__':
    run_async(main())
