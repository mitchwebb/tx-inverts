from contextlib import asynccontextmanager
from fastapi import Request
from psycopg.rows import dict_row, tuple_row
from psycopg import AsyncConnection
from typing import Literal


@asynccontextmanager  # Guarantees cursor is closed after use, even on error
async def execute_psql_query(
    conn: AsyncConnection,
    query: str,
    params: tuple = None,
    fetch: Literal['one', 'all'] | None = None,
    batch: bool = False,
    dict_cursor=False
):
    """
    Execute a SQL query from API using the shared DB connection.

    Args:
        conn (AsyncConnection): psycopg connection
        query (str): SQL query string.
        params (tuple or list of tuple, optional): Query parameters.
        fetch (str, optional): 'one' to fetchone(), 'all' to fetchall(), or None.
        batch (bool, optional): If True, use execute_batch for bulk operations.
        dict_cursor (bool, optional): If True, use dict_row/row_factory to return dicts

    Returns:
        Query result if fetch is specified, else None.
    """

    row_factory_type = dict_row if dict_cursor else tuple_row
    async with conn.cursor(row_factory=row_factory_type) as cur:

        # If batch request, use execute_batch
        if batch:
            await cur.executemany(cur, query, params)
        else:
            await cur.execute(query, params)
        # Depending on fetch type, return result(s), or simply commit
        if fetch == 'one':
            result = await cur.fetchone()
        elif fetch == 'all':
            result = await cur.fetchall()
        await conn.commit()
        yield result
