# Conservation rank related API endpoints
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.natureserve import calculate_ns_values
from psycopg import sql
from backend.db.queries.occurrence import create_occurrence_filter
from backend.models.api import ObservationsRequestParams
from backend.models.occurrence import OccurrenceFilter, SingleTaxonOccurrenceFilter
from backend.core.logging import api_logger
import json


rankings_router = APIRouter()


@rankings_router.post('/get_ns_metrics', response_class=JSONResponse)
async def get_ns_metrics(params: ObservationsRequestParams, request: Request) -> JSONResponse:
    """
    Get NatureServe metrics (occurrences, range extent, and area of occupancy) 
    for a given (single) taxon_id with filters

    Args:
        params (ObservationsRequestParams): Collection of filters to filter occurrence records
        request (fastapi.Request): FastAPI request object

    Returns:
        JSON response containing NS metrics and current state rank for the taxon,
        or {'result': None} if no NS values could be calculated.
    """

    pool = request.app.state.db_pool

    try:
        # Make SingleTaxonOccurrenceFilter Object
        filters = SingleTaxonOccurrenceFilter(
            taxon_id=params.taxon_ids,
            include_inat=params.include_inat,
            date_start=params.date_start,
            date_end=params.date_end,
            datasets=params.datasets,
        )

        async with pool.connection() as conn:
            # Calculate various ns_values using filtered observation data
            ns_result = await calculate_ns_values(conn, filters, params.taxon_rank)
            # Protect against failed ns_result
            if not ns_result:
                return JSONResponse(content={'result': None}, status_code=200)
            api_logger.info(f'Retrieved NS values {ns_result}')

            # Return results
            return JSONResponse(content=ns_result)

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@rankings_router.post('/get_range_extent_geom', response_class=JSONResponse)
async def get_range_extent_geom(params: ObservationsRequestParams, request: Request) -> JSONResponse:
    """
    Get hull geometry representing range extent for a given species' filtered observation data

    Args:
        params (ObservationsRequestParams): Collection of filters to filter occurrence records
        request (fastapi.Request): FastAPI request object

    Returns:
        JSON response containing range extent geometry, or {'result': None} if no geometry could be calculated.
    """

    pool = request.app.state.db_pool

    try:
        # Make OccurrenceFilter Object
        filters = OccurrenceFilter(
            taxon_ids=params.taxon_ids,
            include_inat=params.include_inat,
            date_end=params.date_end,
            date_start=params.date_start,
            datasets=params.datasets
        )

        # Make occurrence_filter SQL fragment
        occurrence_filter = create_occurrence_filter(filters)

        async with pool.connection() as conn:
            # Get range extent geometry via SQL using filtered occurrences
            query = sql.SQL("""
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
            """).format(
                tx_table=sql.Identifier(TEXAS_GEOMETRY_TABLE.name),
                occurrence_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                occurrence_filter=occurrence_filter
            )
            result = await execute_psql_query(conn, query, fetch='one', dict_cursor=True)
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
        raise HTTPException(status_code=500, detail=str(e))
