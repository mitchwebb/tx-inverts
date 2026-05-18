from typing import List
import uuid
from backend.constants.shapefiles import GEOMETRY_TABLE_CONFIGS
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.base import DBTable
from shapely import MultiPolygon
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.tools.jobs.tasks.database import update_index
from backend.tools.jobs.tasks.views import refresh_materialized_view
from psycopg import sql
from backend.core.logging import db_logger
import geopandas as gpd


# Helper to get row geometry, cast to MultiPolygon if Polygon
def _to_multipolygon_wkt(geom) -> str:
    if geom.geom_type == 'Polygon':
        return MultiPolygon([geom]).wkt
    return geom.wkt


async def fill_geometry_table(fp: str, table: DBTable, col_map: dict, conn, truncate: bool = False):
    """
    Using a shapefile path, table definition, and column map, creates or updates shapefile table in database.
    Ends process by updating regions matview.

    Args:
        fp (str): Filepath to shapefile
        table (DBTable): Table definition
        col_map (dict): Map from shapefile column names to database column names
        truncate (bool): If yes, table will be truncated at the start of the process

    Returns:
        None

    """

    try:
        # Read in shapefile
        gdf = gpd.read_file(fp)
        # Change CRS to 4326 (WGS 84)
        gdf = gdf.to_crs(epsg=4326)
        # Rename columns using column map
        gdf = gdf.rename(columns=col_map)[list(col_map.values())]

        # Pre-process dataframe
        # Set id and geometry in df
        gdf['geometry'] = gdf['geometry'].apply(_to_multipolygon_wkt)
        gdf['id'] = [uuid.uuid4() for _ in range(len(gdf))]

        # Get column order and match with values
        cols = list(gdf.columns)
        col_idents = sql.SQL(', ').join(sql.Identifier(c) for c in cols)

        # On conflict, update all columns except primary key
        update_str = sql.SQL(', ').join(
            sql.SQL('{col} = EXCLUDED.{col}').format(
                col=sql.Identifier(c))
            for c in cols if c != table.primary_key
        )

        if truncate:
            truncate_query = sql.SQL('TRUNCATE {table}').format(
                table=sql.Identifier(table.name))
            await execute_psql_query(conn, truncate_query)
            db_logger.info(f'Truncated {table.name} table')

        # Build placeholders, handling geometry column specially
        values = sql.SQL(', ').join(
            sql.SQL('ST_GeomFromText(%s, 4326)') if c == 'geometry' else sql.SQL('%s')
            for c in cols
        )

        insert_query = sql.SQL("""
            INSERT INTO {table} ({cols})
            VALUES ({values})
            ON CONFLICT ({primary_key}) DO UPDATE SET {update_str}
        """).format(
            table=sql.Identifier(table.name),
            cols=col_idents,
            values=values,
            primary_key=sql.Identifier(table.primary_key),
            update_str=update_str,
        )

        # Build params list (tuples)
        row_params = [
            tuple(row[c] for c in cols)
            for _, row in gdf.iterrows()
        ]

        await execute_psql_query(conn, insert_query, row_params, batch=True)

        await conn.commit()

        # Refresh regions view
        await refresh_materialized_view(conn, 'regions')
        db_logger.info(f'Updated {table.name} table...')
    except Exception as e:
        db_logger.error(f'Failed to fill geometry table: {e}')
        await conn.rollback()
        raise


async def fill_all_geometry_tables(conn, truncate: bool = False):
    for config in GEOMETRY_TABLE_CONFIGS:
        await fill_geometry_table(config.path, config.table, config.col_map, conn, truncate=truncate)
    await conn.commit()
    db_logger.info('Updated all geometry tables')


async def update_observation_regions(conn, new_observation_ids: List[int] = None, replace_all: bool = False):

    try:
        # Make sure indexes are in place
        await update_index(conn, 'idx_obs_regions_id')
        await update_index(conn, 'idx_regions_geometry')

        # If replace_all or no ids provided, truncate table and recompute all
        if replace_all or new_observation_ids is None:
            db_logger.info('Truncating observation_regions table...')
            truncate_query = sql.SQL('TRUNCATE {table}').format(
                table=sql.Identifier(OBSERVATION_REGIONS_TABLE.name)
            )
            await execute_psql_query(conn, truncate_query)

            insert_query = sql.SQL("""
                INSERT INTO {observation_regions_table} (observation_id, region_id, region_type)
                SELECT o.gbif_id, r.id, r.region_type
                FROM {observations_table} o
                JOIN regions r ON ST_Intersects(o.geometry, r.geometry)
            """).format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            )
            await execute_psql_query(conn, insert_query)
        # Else, replace/add only those ids found in new_observation_ids
        else:
            db_logger.info(
                f'Updating observation_regions for {len(new_observation_ids)} observations...')
            # Delete any preexisting records
            delete_query = sql.SQL("""
                DELETE FROM {observation_regions_table}
                WHERE observation_id = ANY({ids})
            """).format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                ids=sql.Literal(new_observation_ids)
            )
            await execute_psql_query(conn, delete_query)

            # Insert new records for new observations
            insert_query = sql.SQL("""
                INSERT INTO {observation_regions_table} (observation_id, region_id, region_type)
                SELECT o.gbif_id, r.id, r.region_type
                FROM {observations_table} o
                JOIN regions r ON ST_Intersects(o.geometry, r.geometry)
                WHERE o.gbif_id = ANY({ids})
            """).format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                ids=sql.Literal(new_observation_ids)
            )
            await execute_psql_query(conn, insert_query)

        await conn.commit()
        db_logger.info('Updated observations_regions table')
    except Exception as e:
        db_logger.error(f'Failed to update observation_regions: {e}')
        await conn.rollback()
        raise
