import uuid

from backend.constants.shapefiles import GEOMETRY_TABLE_CONFIGS
from backend.db_schema.base import DBTable
from shapely import MultiPolygon
from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.tools.jobs.tasks.database import update_index
from backend.tools.jobs.tasks.views import refresh_materialized_view
from psycopg import sql
from backend.core.logging import db_logger
import geopandas as gpd


async def fill_geometry_table(fp: str, table: DBTable, col_map: dict, conn, truncate: bool = False):
    gdf = gpd.read_file(fp)
    gdf = gdf.to_crs(epsg=4326)
    # Rename columns using column map
    gdf = gdf.rename(columns=col_map)[list(col_map.values())]

    async with conn.cursor() as cur:
        if truncate:
            await cur.execute(sql.SQL('TRUNCATE {table}').format(table=sql.Identifier(table.name)))
            db_logger.info(f'Truncated {table.name} table')
        for _, row in gdf.iterrows():
            # Get row geometry, cast to MultiPolygon if Polygon
            geom = row.geometry
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon([geom])
            wkt_geom = geom.wkt

            # Set id and geometry in row
            row['id'] = uuid.uuid4()
            row['geometry'] = wkt_geom

            # Get column order and match with values
            cols = list(row.index)
            col_idents = sql.SQL(', ').join(
                sql.Identifier(c) for c in cols)
            values = sql.SQL(', ').join(
                sql.SQL('ST_GeomFromText(') + sql.Literal(row[c]) + sql.SQL(', 4326)') if c == 'geometry'
                else sql.Literal(row[c])
                for c in cols
            )
            # On conflict, update all columns except primary key
            # TODO: but why?
            update_str = sql.SQL(', ').join(
                sql.SQL('{col} = EXCLUDED.{col}').format(
                    col=sql.Identifier(c))
                for c in cols if c != table.primary_key
            )
            query = sql.SQL('''
                    INSERT INTO {table} ({cols})
                    VALUES ({values})
                ''').format(
                table=sql.Identifier(table.name),
                cols=col_idents,
                values=values,
                primary_key=sql.Identifier(table.primary_key),
                update_str=update_str,
            )
            await cur.execute(query)

        await conn.commit()
        await refresh_materialized_view(conn, 'regions')
        db_logger.info(f'Updated {table.name} table...')


async def fill_all_geometry_tables(conn, truncate: bool = False):
    for [shapefile, table, map] in GEOMETRY_TABLE_CONFIGS:
        await fill_geometry_table(shapefile, table, map, conn, truncate=truncate)
    await conn.commit()
    db_logger.info(f'Updated all geometry tables')


async def update_observation_regions(conn, new_observation_ids=None, replace_all: bool = False):

    # Make sure indexes are in place
    await update_index(conn, 'idx_obs_regions_id')
    await update_index(conn, 'idx_regions_geometry')

    # If exists
    async with conn.cursor() as cur:
        # If replace_all or no ids provided, truncate table and recompute all
        if replace_all or not new_observation_ids:
            db_logger.info('Truncating observation_regions table...')
            await cur.execute(sql.SQL('TRUNCATE {table}').format(
                table=sql.Identifier(OBSERVATION_REGIONS_TABLE.name)
            ))
            query = sql.SQL('''
                INSERT INTO {observation_regions_table} (observation_id, region_id, region_type)
                SELECT o.gbif_id, r.id, r.region_type
                FROM {observations_table} o
                JOIN regions r ON ST_Intersects(o.geometry, r.geometry)
            ''').format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            )
        # Else, replace/add only those ids found in new_observation_ids
        else:
            db_logger.info(
                f'Updating observation_regions for {len(new_observation_ids)} observations...')
            await cur.execute(sql.SQL('''
                DELETE FROM {observation_regions_table}
                WHERE observation_id = ANY({ids})
            ''').format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                ids=sql.Literal(new_observation_ids)
            ))
            query = sql.SQL('''
                INSERT INTO {observation_regions_table} (observation_id, region_id, region_type)
                SELECT o.gbif_id, r.id, r.region_type
                FROM {observations_table} o
                JOIN regions r ON ST_Intersects(o.geometry, r.geometry)
                WHERE o.gbif_id = ANY({ids})
            ''').format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                ids=sql.Literal(new_observation_ids)
            )
        await cur.execute(query)
    await conn.commit()
    db_logger.info('Updated observations_regions table')
