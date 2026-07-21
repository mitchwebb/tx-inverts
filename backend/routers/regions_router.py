# Region tables related SQL endpoints
from uuid import UUID

from pydantic import BaseModel

from backend.db.schema.regions import REGIONS_VIEW
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.core.logging import api_logger
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from fastapi import APIRouter, HTTPException, Request
import re

from backend.models.regions import County, Park


regions_router = APIRouter()


class RegionInfo(BaseModel):
    id: str | UUID
    region_type: str
    name: str


@regions_router.get("/get_region_info", response_model=RegionInfo)
async def get_region_info(region_id: str, request: Request) -> RegionInfo:
    """
    Get basic region information from region_id

    Args:
        region_id: The database ID of the region to look up.

    Returns:
        A dict with keys: id, region_type, name.
    """

    try:
        query = sql.SQL('''
            SELECT id, region_type, name
            FROM {regions_view}
            WHERE id = {region_id}
        ''').format(
            regions_view=sql.Identifier(REGIONS_VIEW.name),
            region_id=sql.Literal(region_id)
        )

        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='one', dict_cursor=True)

    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

    if results is None:
        raise HTTPException(
            status_code=404, detail=f'Region {region_id} not found')

    return RegionInfo(**dict(results))


@regions_router.get("/search_counties")
async def search_counties(request: Request, search_term: str) -> dict[str, list[County]]:
    """
    Using a search term, search through counties table by county name (case insensitive)
    """

    query = sql.SQL('''
        SELECT county, id
        FROM {counties_table}
        WHERE county ~* {search_term}
        LIMIT 10
    ''').format(
        counties_table=sql.Identifier(TEXAS_COUNTIES_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    try:
        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='all', dict_cursor=True) or []
            results = [County(**dict(row)) for row in results]
            return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@regions_router.get("/search_parks")
async def search_parks(request: Request, search_term: str) -> dict[str, list[Park]]:
    """
    Using a search term, search through parks table by park name (case insensitive)
    """

    query = sql.SQL('''
        SELECT prop_name, alt_prop_name, prop_class, owner, id
        FROM {parks_table}
        WHERE prop_name ~* {search_term}
        LIMIT 10
    ''').format(
        parks_table=sql.Identifier(TEXAS_PARKS_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    try:
        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='all', dict_cursor=True) or []
            results = [format_park(dict(row)) for row in results]
            return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_park(row: dict) -> Park:
    """
    Helper for formatting park information returned in search
    """

    if row.get('owner'):
        row['owner'] = format_owner_name(row['owner'])
    return Park(**dict(row))


# Format 'Austin, City of' type text, as well as 'Unknown' and 'Public; unknown'
def format_owner_name(name: str) -> str:
    """
    Helper for formatting known patterns and values in park['owner_name'] column
    """

    name = re.sub(r';\s*unknown$', '', name, flags=re.IGNORECASE).strip()
    match = re.match(r'^(.+),\s*(.+?)\s+of$', name, re.IGNORECASE)
    if match:
        return f"{match.group(2)} of {match.group(1)}"
    return name
