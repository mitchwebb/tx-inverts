from http.client import HTTPException
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.models.api_types import TextData
from fastapi import APIRouter, Request
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
import re


map_router = APIRouter()


@map_router.post("/search_counties")
async def search_counties(data: TextData, request: Request):
    search_term = data.text
    query = sql.SQL("""
        SELECT county, id
        FROM {counties_table}
        WHERE county ~* {search_term}
        LIMIT 10
    """).format(
        counties_table=sql.Identifier(TEXAS_COUNTIES_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    try:
        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)
            results = [dict(row) for row in results]
            return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@map_router.post("/search_parks")
async def search_parks(data: TextData, request: Request):
    search_term = data.text
    query = sql.SQL("""
        SELECT prop_name, alt_prop_name, prop_class, owner, id
        FROM {parks_table}
        WHERE prop_name ~* {search_term}
        LIMIT 10
    """).format(
        parks_table=sql.Identifier(TEXAS_PARKS_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    try:
        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='all', dict_cursor=True)
            results = [format_park(dict(row)) for row in results]
            return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_park(row: dict) -> dict:
    if row.get('owner'):
        row['owner'] = format_owner_name(row['owner'])
    return row


# Format 'Austin, City of' type text, as well as 'Unknown' and 'Public; unknown'
def format_owner_name(name: str) -> str:
    name = re.sub(r';\s*unknown$', '', name, flags=re.IGNORECASE).strip()
    match = re.match(r'^(.+),\s*(.+?)\s+of$', name, re.IGNORECASE)
    if match:
        return f"{match.group(2)} of {match.group(1)}"
    return name
