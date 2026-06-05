from psycopg.rows import dict_row, tuple_row, DictRow, TupleRow
from psycopg import AsyncConnection, sql
from typing import Literal, Sequence, overload


# Fetch one tuple overload
@overload
async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = ...,
    fetch: Literal['one'] = ...,
    batch: bool = ...,
    dict_cursor: Literal[False] = ...,
) -> TupleRow | None: ...


# Fetch one dict overload
@overload
async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = ...,
    fetch: Literal['one'] = ...,
    batch: bool = ...,
    dict_cursor: Literal[True] = ...,
) -> DictRow | None: ...


# Fetch all tuples overload
@overload
async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = ...,
    fetch: Literal['all'] = ...,
    batch: bool = ...,
    dict_cursor: Literal[False] = ...
) -> Sequence[TupleRow] | None: ...


# Fetch all dicts overload
@overload
async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = ...,
    fetch: Literal['all'] = ...,
    batch: bool = ...,
    dict_cursor: Literal[True] = ...
) -> Sequence[DictRow] | None: ...


# Fetch None overload
@overload
async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = ...,
    fetch: None = ...,
    batch: bool = ...,
    dict_cursor: bool = ...
) -> None: ...


async def execute_psql_query(
    conn: AsyncConnection,
    query: sql.Composed | sql.SQL,
    params: tuple | list[tuple] | None = None,
    fetch: Literal['one', 'all'] | None = None,
    batch: bool = False,
    dict_cursor: bool = False
) -> DictRow | TupleRow | Sequence[DictRow | TupleRow] | None:
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
