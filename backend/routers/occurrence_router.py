# Occurrence related API endpoints
from datetime import date
from typing import Sequence

from numpy import number
import backend.constants.map as map
from backend.core.exception_handler import TaxonNotFoundError
from backend.data_util.taxa_data import taxon_exists
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from fastapi import APIRouter, Query, Request, HTTPException, Response
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql, rows
from backend.db.queries.occurrence import create_occurrence_filter_sql, create_occurrence_taxon_filter
from backend.models.api import SingleTaxonObsRequestParams
from backend.core.logging import api_logger
from backend.models.occurrence import OccurrenceFilters


occurrence_router = APIRouter()


@occurrence_router.get('/get_datasets')
async def get_datasets(request: Request) -> dict[str, Sequence[rows.DictRow]]:
    """
    Get list of ALL datasets found in dataset_meta table (all datasets in our APPROVED_DATASETS)
    """

    try:
        query = sql.SQL("""
            SELECT * FROM {dataset_table}
        """).format(dataset_table=sql.Identifier(GBIF_DATASET_META.name))

        async with request.app.state.db_pool.connection() as conn:
            result = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)

            if result is None:
                raise HTTPException(
                    status_code=404, detail='Dataset information not retrieved')

            if len(result) == 0:
                raise HTTPException(
                    404, 'No datasets found in datasets table! Have you run setup/fill_dataset_table?')

            return {
                'datasets': result
            }

    except HTTPException:
        raise

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@occurrence_router.post('/get_dataset_counts')
async def get_dataset_counts(params: SingleTaxonObsRequestParams, request: Request) -> dict[str, int] | None:
    """
    Get observation counts for each dataset represented in filtered observation data

    Args:
        params (SingleTaxonObsRequestParams): Params for filtering observation data
        request (fastapi.Request): FastAPI request object

    Returns:
        dict[str, int] | None: Mapping of dataset_key to observation count, ordered by count descending. 
        Returns None if no results are found.

    """

    try:
        pool = request.app.state.db_pool

        async with pool.connection() as conn:

            if not await taxon_exists(conn, params.taxon_id):
                raise TaxonNotFoundError(
                    f'Requested taxon {params.taxon_id} is not found in the backbone')

            filter_payload = OccurrenceFilters(
                taxon_ids=[params.taxon_id],
                include_inat=params.include_inat,
                date_start=params.date_start,
                date_end=params.date_end,
                regions=params.regions,
                coord_uncertainty=params.coord_uncertainty
                # Don't include datasets
            )

            taxon_filter = create_occurrence_taxon_filter(
                filter_payload.taxon_ids)

            occurrence_filter = create_occurrence_filter_sql(filter_payload)

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

    except TaxonNotFoundError as e:
        api_logger.exception(e)
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@occurrence_router.post('/get_observation_dates')
async def get_observation_dates(params: SingleTaxonObsRequestParams, request: Request) -> dict[str, date | None] | None:
    """
    Get min/max dates represented in filtered observation data for single taxon

    Args:
        params (SingleTaxonObsRequestParams): Params for filtering observation data
        request (fastapi.Request): FastAPI request object

    Returns:
        dict[str, date | None] | None: dict of 'min_date' and 'max_date' with corresponding dates or None values. Returns none if no results. 
    """

    try:
        pool = request.app.state.db_pool

        async with pool.connection() as conn:

            if not await taxon_exists(conn, params.taxon_id):
                raise TaxonNotFoundError(
                    f'Requested taxon {params.taxon_id} is not found in the backbone')

            filter_payload = OccurrenceFilters(
                taxon_ids=[params.taxon_id],
                include_inat=params.include_inat,
                date_start=params.date_start,
                date_end=params.date_end,
                datasets=params.datasets,
                regions=params.regions,
                coord_uncertainty=params.coord_uncertainty
            )

            occurrence_filter = create_occurrence_filter_sql(filter_payload)

            query = sql.SQL("""
                SELECT
                    MIN(LEAST(collection_start_date, collection_end_date)) AS min_date,
                    MAX(GREATEST(collection_start_date, collection_end_date)) AS max_date
                FROM {occurrence_table}
                WHERE {occurrence_filter}
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

    except TaxonNotFoundError as e:
        api_logger.exception(e)
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@occurrence_router.post('/get_date_counts')
async def get_date_counts(params: SingleTaxonObsRequestParams, request: Request) -> dict[str, int] | None:
    try:
        async with request.app.state.db_pool.connection() as conn:
            if not await taxon_exists(conn, params.taxon_id):
                raise TaxonNotFoundError(
                    f'Requested taxon {params.taxon_id} is not found in the backbone')

            filter_payload = OccurrenceFilters(
                taxon_ids=[params.taxon_id],
                include_inat=params.include_inat,
                date_start=params.date_start,
                date_end=params.date_end,
                datasets=params.datasets,
                regions=params.regions,
                coord_uncertainty=params.coord_uncertainty
            )

            occurrence_filter = create_occurrence_filter_sql(filter_payload)

            # Aggregate date counts around the middle of each month
            date_query = sql.SQL("""
                WITH filtered AS (
                    SELECT collection_start_date
                    FROM gbif_observations
                    WHERE {occurrence_filter}
                ),
                counts AS (
                    SELECT
                        DATE_TRUNC('month', collection_start_date) AS month_date,
                        COUNT(*) AS observation_count
                    FROM filtered
                    GROUP BY 1
                ),
                bounds AS (
                    SELECT
                        DATE_TRUNC('month', MIN(collection_start_date)) AS min_month,
                        DATE_TRUNC('month', MAX(collection_start_date)) AS max_month
                    FROM filtered
                )
                SELECT
                    TO_CHAR(months.month_date, 'YYYY-MM-15') AS agg_event_date,
                    COALESCE(counts.observation_count, 0) AS observation_count
                FROM bounds
                CROSS JOIN LATERAL generate_series(
                    bounds.min_month,
                    bounds.max_month,
                    '1 month'
                ) AS months(month_date)
                LEFT JOIN counts USING (month_date)
                ORDER BY months.month_date;
            """).format(
                occurrence_filter=occurrence_filter
            )

            result = await execute_psql_query(
                conn, date_query, fetch='all', dict_cursor=True)

            result = {row['agg_event_date']: row['observation_count']
                      for row in result} if result else None
            return result
    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@occurrence_router.get('/tiles/{z}/{x}/{y}.mvt', response_class=Response)
async def get_tile(
    z: int, x: int, y: int,
    request: Request,
    taxon_id: int = Query(),
    include_inat: bool = Query(default=True),
    datasets: list[str] = Query(default=[]),
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
    coord_uncertainty: int | None = Query(default=None)
):
    """
    Get map tiles for observations data as Mapbox Vector Tiles
    Returns clustered heatmap tiles at zoom levels below 10, and individual point observation at zoom level 10 and above.

    Args:
        include_inat (bool): Whether or not to include iNaturalist records
        taxon_id (int): GBIF Taxon ID of desired taxon
        datasets (list[str]): List of desired dataset IDs
        date_start (str): Minimum desired date
        date_end (str): Maximum desired date
        coord_uncertainty (int): Maximum desired coordinate uncertainty in meters
        x (int): X value of tile
        y (int): Y value of tile
        z (int): Z value of tile (zoom)
        request (fastapi.Request): FastAPI request object

    Returns:
        A protobuf-encoded MVT tile. Returns an empty response if no
            observations fall within the requested tile bounds.
    """

    try:
        filter_payload = OccurrenceFilters(
            taxon_ids=[taxon_id],
            include_inat=include_inat,
            date_start=date_start,
            date_end=date_end,
            datasets=datasets,
            coord_uncertainty=coord_uncertainty,
        )

        occurrence_filter = create_occurrence_filter_sql(filter_payload)

        # Get grid size in meters at a given zoom level
        grid_size = map.get_meters_per_pixel(z) * map.PIXELS_PER_GRID

        if z < 10:
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
