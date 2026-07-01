# Region tables related SQL endpoints
from uuid import UUID

from pydantic import BaseModel

from backend.db.schema.regions import REGIONS_VIEW
from fastapi import APIRouter, Request, HTTPException
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.core.logging import api_logger


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
        query = sql.SQL("""
            SELECT id, region_type, name
            FROM {regions_view}
            WHERE id = {region_id}
        """).format(
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
