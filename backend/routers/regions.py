from pydantic import BaseModel
from backend.db_schema.regions import REGIONS_VIEW
from fastapi import APIRouter, Request, HTTPException
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.core.logging import api_logger


regions_router = APIRouter()


class RegionParams(BaseModel):
    region_id: str


@regions_router.post("/get_region_info")
async def get_region_info(data: RegionParams, request: Request):
    try:
        region_id = data.region_id
        print(region_id)
        query = sql.SQL('''
            SELECT id, region_type, name
            FROM {regions_view}
            WHERE id = {region_id}
        ''').format(
            regions_view=sql.Identifier(REGIONS_VIEW.name),
            region_id=sql.Literal(region_id)
        )

        async with request.app.state.db_pool.connection() as conn:
            async with execute_psql_query(conn, query, (), 'one', dict_cursor=True) as results:
                return results
    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
