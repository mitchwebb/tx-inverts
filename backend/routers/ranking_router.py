# Conservation rank related API endpoints
from typing import cast

from backend.constants.taxa import TaxonomicRank
from backend.core.exception_handler import TaxonNotFoundError
from backend.data_util.taxa import taxon_exists
from backend.db.queries.taxa import get_taxon_rank
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.ranking import calculate_ns_values
from psycopg import sql
from backend.db.queries.occurrence import create_occurrence_filter_sql
from backend.models.api import SingleTaxonObsRequestParams
from backend.models.occurrence import OccurrenceFilters
from backend.core.logging import api_logger
import json


ranking_router = APIRouter()


@ranking_router.post('/get_ns_metrics', response_class=JSONResponse)
async def get_ns_metrics(params: SingleTaxonObsRequestParams, request: Request) -> JSONResponse:
    """
    Get conservation metrics (occurrences, range extent, and area of occupancy) 
    for a given (single) taxon_id with filters

    Args:
        params (SingleTaxonObsRequestParams): Collection of filters to filter occurrence records
        request (fastapi.Request): FastAPI request object

    Returns:
        JSON response containing NS metrics and current state rank for the taxon,
        or {'result': None} if no NS values could be calculated.
    """

    pool = request.app.state.db_pool

    try:
        # Make SingleTaxonOccurrenceFilter Object
        filters = OccurrenceFilters(
            taxon_ids=[params.taxon_id],
            include_inat=params.include_inat,
            date_start=params.date_start,
            date_end=params.date_end,
            datasets=params.datasets,
            coord_uncertainty=params.coord_uncertainty
        )

        async with pool.connection() as conn:

            if not await taxon_exists(conn, params.taxon_id):
                raise TaxonNotFoundError(
                    f'Requested taxon {params.taxon_id} is not found in the backbone')

            # Occurrences is only a useful metric for species and subspecies
            # We'll include genus as well, because why not
            taxon_rank = await get_taxon_rank(conn, params.taxon_id)
            compute_occurrences = taxon_rank in {
                'genus', 'species', 'subspecies'} or taxon_rank is None

            # Calculate various ns_values using filtered observation data
            ns_result = await calculate_ns_values(conn, filters, compute_occurrences)

            # Protect against failed ns_result
            if not ns_result:
                return JSONResponse(content={'result': None}, status_code=200)
            api_logger.info(f"Retrieved NS values {ns_result}")

            # Return results
            return JSONResponse(content=ns_result)

    except TaxonNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@ranking_router.post('/get_texas_range_extent_geom', response_class=JSONResponse)
async def get_texas_range_extent_geom(params: SingleTaxonObsRequestParams, request: Request) -> JSONResponse:
    """
    Get hull geometry representing range extent for a given species' filtered observation data, always filtered to Texas

    Args:
        params (SingleTaxonObsRequestParams): Collection of filters to filter occurrence records
        request (fastapi.Request): FastAPI request object

    Returns:
        JSON response containing range extent geometry, or {'result': None} if no geometry could be calculated.
    """

    pool = request.app.state.db_pool

    try:

        # Make OccurrenceFilters Object
        filters = OccurrenceFilters(
            taxon_ids=[params.taxon_id],
            include_inat=params.include_inat,
            date_end=params.date_end,
            date_start=params.date_start,
            datasets=params.datasets,
            coord_uncertainty=params.coord_uncertainty,
            regions=params.regions
        )

        async with pool.connection() as conn:
            if not await taxon_exists(conn, params.taxon_id):
                raise TaxonNotFoundError(
                    f'Requested taxon {params.taxon_id} is not found in the backbone')

            # Make occurrence_filter SQL fragment
            occurrence_filter = create_occurrence_filter_sql(filters)

            # Get range extent geometry via SQL using filtered occurrences
            query = sql.SQL("""
                WITH region AS (
                    SELECT geometry
                    FROM {tx_table}
                    WHERE state = 'Texas'
                ),
                hull AS (
                    SELECT ST_ConvexHull(ST_Collect(geometry)) AS geom
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
                return JSONResponse(content={'range_extent_geom': None}, status_code=200)

            geom_json = result['range_extent_geom']
            return JSONResponse(content={
                'range_extent_geom': json.loads(geom_json) if geom_json else None
            })

    except TaxonNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
