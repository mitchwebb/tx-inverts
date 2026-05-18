from contextlib import asynccontextmanager
from psycopg.rows import dict_row, tuple_row
from psycopg import AsyncConnection, sql
from typing import Literal


async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | str,
    params: tuple | list[tuple] | None = None,
    fetch: Literal['one', 'all'] | None = None,
    batch: bool = False,
    dict_cursor: bool = False
):
    """
    Execute a SQL query from API using the shared DB connection. Does not commit.

    Args:
        conn (AsyncConnection): psycopg connection
        query (str): SQL query string.
        params (tuple or list of tuple, optional): Query parameters.
        fetch (str, optional): "one" to fetchone(), "all" to fetchall(), or None.
        batch (bool, optional): If True, use execute_batch for bulk operations.
        dict_cursor (bool, optional): If True, use dict_row/row_factory to return dicts

    Returns:
        Query result if fetch is specified, else None.
    """

    row_factory_type = dict_row if dict_cursor else tuple_row
    async with conn.cursor(row_factory=row_factory_type) as cur:
        # If batch request, use execute_batch
        if batch:
            if params is None:
                raise ValueError('Batch operations require params.')
            await cur.executemany(query, params)
        else:
            if params is not None:
                await cur.execute(query, params)
            else:
                await cur.execute(query)
        # Depending on fetch type, return result(s), or simply commit
        if fetch == 'one':
            result = await cur.fetchone()
        elif fetch == 'all':
            result = await cur.fetchall()
        else:
            result = None

        return result
