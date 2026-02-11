# General script for initial Texas Inverts backend setup

import asyncio
import sys
from backend.data_util.db import get_single_db_connection
from backend.data_util.invasives import get_invasives_dataset
from backend.tools.initialize_db import initialize_all_tables
from backend.constants.map import TEXAS_GEOJSON
from backend.tools.jobs.database import update_backbone
from backend.tools.jobs.occurrence import update_observations
import geopandas as gpd
from backend.tools.jobs.database import update_indexes
from backend.tools.jobs.taxa import create_invasives_table


# Initial script to create and populate database for Texas Inverts
async def main():
    conn = await get_single_db_connection()

    try:
        await initialize_all_tables(conn, verbose=True, strict=True)
        await conn.commit()

        # Populate geometries
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
            print('Updating geometries table...')
            await conn.commit()

        # Create invasives table
        await create_invasives_table()

        # Taxonomy table initialization
        await update_backbone()

        # Observations table initialization
        await update_observations()

        await update_indexes()

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
