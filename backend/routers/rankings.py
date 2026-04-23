from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.geometries import TEXAS_GEOMETRY_TABLE
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from backend.data_util.execute_psql_query import execute_psql_query
from backend.routers.occurrence import ObservationsRequestParams
from backend.data_util.natureserve import calculate_ns_values
from backend.routers.taxa import get_taxon_rank
from psycopg import sql
from backend.core.sql import create_occurrence_filter
from backend.models.sql import OccurrenceFilter, SingleTaxonOccurrenceFilter
from backend.core.logging import api_logger

import json
import psycopg


rankings_router = APIRouter()


@rankings_router.post('/get_ns_metrics', response_class=Response)
async def get_ns_metrics(params: ObservationsRequestParams, request: Request):
    """
    Get NatureServe metrics (occurrences, range extent, and area of occupancy) 
    for a given (single) taxon_id with filters

    Args:
        params (ObservationsRequestParams): Collection of filters to filter occurrence records
        request (Request)

    Returns:
        TODO: Sort out typing and finish this docstring
    """

    filters = SingleTaxonOccurrenceFilter(
        taxon_id=params.taxon_ids,
        include_inat=params.include_inat,
        date_start=params.date_start,
        date_end=params.date_end,
        datasets=params.datasets
    )

    rank_col = 'ns_rank_state' if filters.include_inat else 'ns_rank_state_no_inat'

    pool = request.app.state.db_pool

    try:
        async with pool.connection() as conn:
            taxon_rank = await get_taxon_rank(conn, filters.taxon_id)
            ns_result = await calculate_ns_values(conn, filters, taxon_rank)
            if not ns_result:
                return JSONResponse(content={'result': None}, status_code=200)

            rank_query = sql.SQL("""
                SELECT {rank_col}
                    FROM tx_taxa
                WHERE taxon_id = {taxon_id}
            """).format(
                taxon_id=sql.Literal(filters.taxon_id),
                rank_col=sql.Identifier(rank_col)
            )

            async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                await cur.execute(rank_query, ())
                rank_result = await cur.fetchone()

            api_logger.info(f'Retrieved NS values {ns_result}')
            return JSONResponse(content={
                'result': {
                    'number_of_occurrences': ns_result['number_of_occurrences'],
                    'range_extent_km2': ns_result['range_extent_km2'],
                    'observation_count': ns_result['observation_count'],
                    'area_of_occupancy_4km2_bins': ns_result['area_of_occupancy_4km2_bins'],
                    'area_of_occupancy_1km2_bins': ns_result['area_of_occupancy_1km2_bins'],
                    'ns_rank_state': rank_result[rank_col]
                }
            })
        return
    except Exception as e:
        api_logger.exception(e)
        raise


@rankings_router.post('/get_range_extent_geom', response_class=Response)
async def get_range_extent_geom(params: ObservationsRequestParams, request: Request):

    filters = OccurrenceFilter(
        taxon_ids=params.taxon_ids,
        include_inat=params.include_inat,
        date_end=params.date_end,
        date_start=params.date_start,
        datasets=params.datasets
    )

    occurrence_filter = create_occurrence_filter(filters)

    pool = request.app.state.db_pool

    try:
        async with pool.connection() as conn:
            query = sql.SQL('''
                WITH region AS (
                    SELECT geometry
                    FROM {tx_table}
                    WHERE state = 'Texas'
                ),
                hull AS (
                    SELECT ST_ConvexHull(ST_Collect(
                        ST_SetSRID(ST_MakePoint(decimal_longitude, decimal_latitude), 4326)
                    )) AS geom
                    FROM {occurrence_table}
                    WHERE
                        {occurrence_filter}
                )
                SELECT ST_AsGeoJSON(
                    ST_Transform(
                        ST_Intersection(hull.geom, region.geometry),
                        4326
                    )
                ) AS range_extent_geom
                FROM hull, region;
            ''').format(
                tx_table=sql.Identifier(TEXAS_GEOMETRY_TABLE.name),
                occurrence_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                occurrence_filter=occurrence_filter
            )

            async with execute_psql_query(
                conn, query, (), fetch='one', dict_cursor=True
            ) as result:
                if not result:
                    return JSONResponse(content={'result': None}, status_code=200)

                geom_json = result['range_extent_geom']
                return JSONResponse(content={
                    'result': {
                        'range_extent_geom': json.loads(geom_json) if geom_json else None
                    }
                })
    except Exception as e:
        api_logger.exception(e)
        raise
