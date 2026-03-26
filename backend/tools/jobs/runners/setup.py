# General script for initial Texas Inverts backend setup

import asyncio
import sys
from backend.constants.shapefiles import GEOMETRY_TABLE_CONFIGS
from backend.data_util.db import get_single_db_connection
from backend.db_schema.base import DBTable
from backend.db_schema.geometries import TexasParksTable
from backend.tools.jobs.tasks.initialize_db import initialize_all_tables
from backend.constants.map import TEXAS_GEOJSON
from backend.tools.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.tools.jobs.tasks.occurrence import update_observations
import geopandas as gpd
from backend.tools.jobs.tasks.taxa import create_invasives_table
from backend.core.logging import setup_logging, db_logger
from shapely.geometry import MultiPolygon
from psycopg import sql


# Initial script to create and populate database for Texas Inverts
async def main():
    setup_logging()

    conn = await get_single_db_connection()

    try:
        # Initialize all tables and associated indexes
        await initialize_all_tables(conn, verbose=True, strict=True)
        await conn.commit()

        # TODO: Move to separate file
        # Fill geometry tables with information from geojson files (mapped to new names)
        async def fill_geometry_table(fp: str, table: DBTable, col_map: dict, conn):
            gdf = gpd.read_file(fp)
            async with conn.cursor() as cur:
                for _, row in gdf.iterrows():
                    geom = row.geometry
                    if geom.geom_type == 'Polygon':
                        geom = MultiPolygon([geom])
                    wkt_geom = geom.wkt

                    table_cols = list(col_map.values()) + ['geometry']
                    shapefile_vals = [row[shp_col]
                                      for shp_col in col_map.keys()] + [wkt_geom]

                    table_ident = sql.Identifier(table.name)
                    primary_key_ident = sql.Identifier(table.primary_key)
                    col_idents = sql.SQL(', ').join(
                        sql.Identifier(c) for c in table_cols)
                    placeholders = sql.SQL(', ').join(
                        [sql.Placeholder()] * (len(table_cols) - 1) +
                        [sql.SQL('ST_GeomFromText(') +
                         sql.Placeholder() + sql.SQL(', 4326)')]
                    )
                    update_str = sql.SQL(', ').join(
                        sql.SQL('{col} = EXCLUDED.{col}').format(
                            col=sql.Identifier(c))
                        for c in table_cols if c != table.primary_key
                    )

                    query = sql.SQL('''
                        INSERT INTO {table} ({cols})
                        VALUES ({placeholders})
                        ON CONFLICT ({primary_key})
                            DO UPDATE SET {update_str}
                    ''').format(
                        table=table_ident,
                        cols=col_idents,
                        placeholders=placeholders,
                        primary_key=primary_key_ident,
                        update_str=update_str,
                    )

                    await cur.execute(query, shapefile_vals)
                await conn.commit()
                db_logger.info(f'Updated {table.name} table...')

        for fp, table, col_map in GEOMETRY_TABLE_CONFIGS:
            await fill_geometry_table(fp, table, col_map, conn)

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
        db_logger.exception(f'Database initialization failed. Exiting. {e}')
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
