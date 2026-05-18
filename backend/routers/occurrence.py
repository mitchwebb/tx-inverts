import time
import backend.constants.map as map

from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from fastapi import APIRouter, Request, HTTPException, Response
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.models.api_types import ObservationsRequestParams
from backend.db.queries.occurrence import create_occurrence_filter, create_occurrence_taxon_filter
from backend.models.sql import OccurrenceFilter, SingleTaxonOccurrenceFilter
from backend.core.logging import api_logger
import re


occurrence_router = APIRouter()


# Get list of all datasets currently found in observations
@occurrence_router.get('/get_datasets')
async def get_datasets(request: Request):
    try:
        query = sql.SQL("""
            SELECT * FROM {dataset_table}
        """).format(dataset_table=sql.Identifier(GBIF_DATASET_META.name))

        async with request.app.state.db_pool.connection() as conn:
            result = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)
            if not result:
                raise HTTPException(
                    status_code=404, detail='Dataset information not retrieved')

            datasets = result

            return {
                'datasets': datasets
            }

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@occurrence_router.post('/get_dataset_counts')
async def get_dataset_counts(params: ObservationsRequestParams, request: Request):
    pool = request.app.state.db_pool

    async with pool.connection() as conn:

        filter_payload = OccurrenceFilter(
            taxon_ids=params.taxon_ids,
            include_inat=params.include_inat,
            date_start=params.date_start,
            date_end=params.date_end
        )

        taxon_filter = create_occurrence_taxon_filter(filter_payload.taxon_ids)
        occurrence_filter = create_occurrence_filter(filter_payload)

        query = sql.SQL("""
            WITH datasets_with_taxon AS (
                SELECT DISTINCT dataset_key
                FROM gbif_observations
                WHERE {taxon_filter}
            ),
            counts AS (
                SELECT
                    dataset_key,
                    COUNT(*) as COUNT
                FROM {occurrence_table}
                WHERE
                    {occurrence_filter}
                GROUP BY dataset_key
            )
            SELECT
                p.dataset_key,
                COALESCE(counts.count, 0) AS count
            FROM datasets_with_taxon p
            LEFT JOIN counts
                ON counts.dataset_key = p.dataset_key
            ORDER BY count DESC;
        """).format(
            occurrence_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter,
            taxon_filter=taxon_filter
        )

        result = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)
        if result:
            institution_counts = {
                item['dataset_key']: item['count'] for item in result}
            return institution_counts
        else:
            return None


@occurrence_router.post('/get_observation_dates')
async def get_observation_dates(params: ObservationsRequestParams, request: Request):
    pool = request.app.state.db_pool

    async with pool.connection() as conn:

        filter_payload = OccurrenceFilter(
            taxon_ids=params.taxon_ids,
            include_inat=params.include_inat
        )

        occurrence_filter = create_occurrence_filter(filter_payload)

        query = sql.SQL("""
            SELECT MIN(collection_start_date) as min_date, MAX(collection_end_Date) as max_date
            FROM {occurrence_table}
            WHERE
                {occurrence_filter}
        """).format(
            occurrence_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter
        )

        result = await execute_psql_query(
            conn, query, fetch='one', dict_cursor=True)
        if result:
            return result
        else:
            return None


# @occurrence_router.post('/get_observations')
# async def get_observations(params: TaxaRequestParams, request: Request):
#     taxon_id = params.taxon_id

#     query = """
#         WITH bounds AS (
#             SELECT ST_SetSRID(ST_Extent(geometry) AS bbox
#             FROM gbif_observations
#             WHERE accepted_taxon_key = %s
#         ),
#         grid AS (
#             SELECT ST_SetSRID((ST_SquareGrid(0.2, bbox)).geom, 4326) AS cell
#             FROM bounds
#         ),
#         joined AS (
#             SELECT g.cell, COUNT(o.*) AS count
#             FROM grid g
#             LEFT JOIN gbif_observations o
#                 ON ST_Contains(g.cell, ST_SetSRID(geometry))
#                 AND o.accepted_taxon_key = %s
#             GROUP BY g.cell
#         )
#         SELECT jsonb_build_object(
#             'type', 'FeatureCollection',
#             'features', jsonb_agg(
#                 jsonb_build_object(
#                     'type', 'Feature',
#                     'geometry', ST_AsGeoJSON(cell)::jsonb,
#                     'properties', jsonb_build_object('count', count)
#                 )
#             )
#         )
#         FROM joined;
#         """
#     async with request.app.state.db_pool.connection() as conn:
#         result = await execute_psql_query(
#             conn, query, [taxon_id, taxon_id], fetch='one'
#         )
#         return result[0] if result else {
#             'type': 'FeatureCollection', 'features': []
#         }


@occurrence_router.get('/tiles/{include_inat}/{taxon_id}/{datasets}/{date_start}/{date_end}/{z}/{x}/{y}.mvt', response_class=Response)
async def get_tile(include_inat: bool, taxon_id: int, datasets: str, date_start: str, date_end: str, z: int, x: int, y: int, request: Request):
    try:
        filter_payload = SingleTaxonOccurrenceFilter(
            taxon_id=taxon_id,
            include_inat=include_inat,
            datasets=datasets,
            date_start=date_start,
            date_end=date_end,
        )

        occurrence_filter = create_occurrence_filter(filter_payload)

        # Get grid size in meters at a given zoom level
        grid_size = map.get_meters_per_pixel(z) * map.PIXELS_PER_GRID

        async with request.app.state.db_pool.connection() as conn:

            # result = await execute_psql_query(conn, exists_query, {'species_ids': descendant_ids, 'z': z}, fetch='one', dict_cursor=True)
            # if result['exists']:
            #     api_logger.info('Getting cached tiles...')
            #     params = {
            #         'include_inat': include_inat,
            #         'taxon_id': taxon_id,
            #         'x': x,
            #         'y': y,
            #         'z': z,
            #         'grid_size': grid_size
            #     }
            #     cache_query = """
            #         WITH bbox AS (
            #             SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            #         ),
            #         bin_aggregates AS (
            #             SELECT
            #                 ST_MakeEnvelope(
            #                     c.x_bin * {grid_size},
            #                     c.y_bin * {grid_size},
            #                     (c.x_bin + 1) * {grid_size},
            #                     (c.y_bin + 1) * {grid_size},
            #                     3857
            #                 ) AS geom,
            #                 SUM(c.observation_count)::integer AS observation_count
            #             FROM taxon_tile_cache c
            #             JOIN taxon_descendant_cache t
            #                 ON t.descendant_key = c.taxon_id
            #             WHERE t.ancestor_key = {taxon_id}
            #                 AND c.zoom = {z}
            #                 AND ({include_inat} OR c.publisher != 'iNaturalist')
            #             GROUP BY c.x_bin, c.y_bin
            #         ),
            # 		mvt_geom AS (
            # 			SELECT ST_AsMVTGeom(ba.geom, bbox.geom, 4096, 64, true) AS geom,
            # 				ba.observation_count
            # 			FROM bin_aggregates ba, bbox
            # 			WHERE ST_Intersects(ba.geom, bbox.geom)
            # 		)
            # 		SELECT ST_AsMVT(mvt_geom, 'observations-tiles', 4096, 'geom')
            # 		FROM mvt_geom;
            #     """

            #     result = await execute_psql_query(conn, cache_query, params, fetch='one', dict_cursor=False)
            #         tile = result[0] if result else None
            #     return Response(content=tile, media_type='application/x-protobuf') if tile else Response(content=b'', media_type='application/x-protobuf')

            # If not in cache, fall back to raw generation of tiles
            # else:
            # Return binned results

            if z < 10:
                api_logger.debug(
                    'Cache not found! Generating raw tiles (slow).')
                query = sql.SQL("""
                        WITH
                        bbox AS (
                            SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
                        ),
                        obs AS (
                            SELECT ST_Transform(geometry, 3857) AS geom
                            FROM {occurrence_table}
                            WHERE
                                {occurrence_filter}
                        ),
                        bins AS (
                            SELECT
                                ST_SnapToGrid(obs.geom, {grid_size}) AS grid_geom,
                                COUNT(*) AS count
                            FROM obs
                            GROUP BY grid_geom
                        ),
                        bins_geom AS (
                            SELECT
                                ST_SetSRID(
                                ST_MakeEnvelope(
                                    ST_X(bins.grid_geom) - ({grid_size} / 2),
                                    ST_Y(bins.grid_geom) - ({grid_size} / 2),
                                    ST_X(bins.grid_geom) + ({grid_size} / 2),
                                    ST_Y(bins.grid_geom) + ({grid_size} / 2)
                                ),
                                3857
                                ) AS geom,
                                bins.count as observation_count
                            FROM bins
                        ),
                        mvt_geom AS (
                            SELECT
                                ST_AsMVTGeom(bins_geom.geom, bbox.geom, 4096, 64, true) AS geom,
                                bins_geom.observation_count
                            FROM bins_geom, bbox
                        )
                        SELECT ST_AsMVT(mvt_geom, 'observations-heatmap', 4096, 'geom') FROM mvt_geom;
                    """).format(
                    include_inat=sql.Literal(include_inat),
                    taxon_id=sql.Literal(taxon_id),
                    x=sql.Literal(x),
                    y=sql.Literal(y),
                    z=sql.Literal(z),
                    grid_size=sql.Literal(grid_size),
                    occurrence_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    occurrence_filter=occurrence_filter
                )
            # Return point observations if zoomed in
            else:
                query = sql.SQL("""
                        WITH
                        bbox AS (
                            SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
                        ),
                        obs AS (
                            SELECT 
                                publisher,
                                "references",
                                county,
                                locality,
                                decimal_latitude,
                                decimal_longitude,
                                accepted_scientific_name,
                                gbif_id,
                                collection_start_date,
                                collection_end_date,
                                ST_Transform(geometry, 3857) AS geom
                            FROM {occurrence_table}
                            WHERE
                            {occurrence_filter}
                        ),
                        mvt_geom AS (
                            SELECT ST_AsMVTGeom(obs.geom, bbox.geom, 4096, 64, true) AS geom,
                                obs.*
                            FROM obs, bbox
                            WHERE ST_Intersects(obs.geom, bbox.geom)
                        )
                        SELECT ST_AsMVT(mvt_geom, 'observations-circles', 4096, 'geom') FROM mvt_geom;
                    """).format(
                    include_inat=sql.Literal(include_inat),
                    taxon_id=sql.Literal(taxon_id),
                    x=sql.Literal(x),
                    y=sql.Literal(y),
                    z=sql.Literal(z),
                    occurrence_table=sql.Identifier(
                        GBIF_OBSERVATIONS_TABLE.name),
                    occurrence_filter=occurrence_filter
                )
            async with request.app.state.db_pool.connection() as conn:
                result = await execute_psql_query(conn, query, fetch='one', dict_cursor=False)
                tile = result[0] if result else None
                return Response(content=tile, media_type='application/x-protobuf') if tile else Response(content=b'', media_type='application/x-protobuf')
    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
