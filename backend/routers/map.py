from http.client import HTTPException
from backend.db_schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.models.api_types import TextData
from fastapi import APIRouter, Request
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql


router = APIRouter()


@router.post("/search_counties")
async def search_counties(data: TextData, request: Request):
    search_term = data.text
    query = sql.SQL('''
        SELECT DISTINCT(county)
        FROM {counties_table}
        WHERE county ~* {search_term}
        LIMIT 10
    ''').format(
        counties_table=sql.Identifier(TEXAS_COUNTIES_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    print(query)

    try:
        async with request.app.state.db_pool.connection() as conn:
            async with execute_psql_query(conn, query, (), 'all', dict_cursor=True) as results:
                results = [dict(row) for row in results]
                return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search_parks")
async def search_parks(data: TextData, request: Request):
    search_term = data.text
    query = sql.SQL('''
        SELECT DISTINCT(park_name)
        FROM {parks_table}
        WHERE park_name ~* {search_term}
        LIMIT 10
    ''').format(
        parks_table=sql.Identifier(TEXAS_PARKS_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower())
    )

    try:
        async with request.app.state.db_pool.connection() as conn:
            async with execute_psql_query(conn, query, (), 'all', dict_cursor=True) as results:
                # end = time.time()
                # api_logger.debug(f'Search suggest took {end-start} seconds)
                results = [dict(row) for row in results]
                return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
