# General script for initial Texas Inverts backend setup

import asyncio
import sys
from backend.data_util.db import get_single_db_connection
from backend.tools.jobs.tasks.initialize_db import initialize_all_tables
from backend.constants.map import TEXAS_GEOJSON
from backend.tools.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.tools.jobs.tasks.occurrence import update_observations
import geopandas as gpd
from backend.tools.jobs.tasks.taxa import create_invasives_table
from backend.config.data import DATA_OUT_PATH
from backend.core.logging import setup_logging, tasks_logger, db_logger


# Initial script to create and populate database for Texas Inverts
async def main():
    setup_logging()

    conn = await get_single_db_connection()

    try:
        # Initialize all tables and associated indexes
        await initialize_all_tables(conn, verbose=True, strict=True)
        await conn.commit()

        # TODO: This whole process should be moved to a function
        # Populate geometries (just the Texas shapefile for now)
        texas_gdf = gpd.read_file(TEXAS_GEOJSON)
        # in case it's a MultiPolygon collection
        texas_geom = texas_gdf.geometry.union_all()
        texas_wkt_geom = texas_geom.wkt  # Keep in EPSG:4326

        async with conn.cursor() as cur:
            await cur.execute(
                '''
                    INSERT INTO geometries (geometry_name, geometry)
                    VALUES (%s, ST_GeomFromText(%s, 4326))
                    ON CONFLICT (geometry_name)
                        DO UPDATE SET geometry = EXCLUDED.geometry
                ''',
                ('Texas', texas_wkt_geom)
            )
            db_logger.info('Updating geometries table...')
            await conn.commit()

        # Create invasives table
        await create_invasives_table()

        # Taxonomy table initialization
        await update_backbone()

        # Observations table initialization
        await update_observations(chunk_size=100000)

        # Update ranks stored in db
        await update_ns_ranks(conn)

        # This step could be easier if provided local files
    except Exception as e:
        print(f'Database initialization failed. Exiting. {e}')
        await conn.rollback()
    finally:
        await conn.close()

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    else:
        asyncio.run(main())
