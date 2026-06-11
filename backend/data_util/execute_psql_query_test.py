import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from psycopg import sql, rows

from backend.data_util.execute_psql_query import execute_psql_query


# Make fake conn/cur for calling functions
@pytest.fixture
def mock_conn():
    # Fake cursor with async methods
    mock_cursor = AsyncMock()

    # conn.cursor() needs to work as `async with conn.cursor(...) as cur`
    mock_cursor_ctx = MagicMock()
    mock_cursor_ctx.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_ctx.__aexit__ = AsyncMock(return_value=None)

    conn = MagicMock()
    conn.cursor = MagicMock(return_value=mock_cursor_ctx)
    return conn, mock_cursor


# Make sure batch=True raises if not given params
@pytest.mark.asyncio
async def test_batch_without_params_raises(mock_conn):
    conn, _ = mock_conn
    query = sql.SQL('')

    with pytest.raises(ValueError, match="Batch operations require params"):
        await execute_psql_query(conn, query, batch=True, params=None)


# Test that dict_cursor=True uses dict_row
@pytest.mark.asyncio
async def test_dict_cursor_uses_dict_row_factory(mock_conn):
    conn, _ = mock_conn
    query = sql.SQL('')

    await execute_psql_query(conn, query, fetch='one', dict_cursor=True)

    conn.cursor.assert_called_once_with(row_factory=rows.dict_row)


# Test that dict_cursor=False uses tuple_row
@pytest.mark.asyncio
async def test_tuple_cursor_uses_tuple_row_factory(mock_conn):
    conn, _ = mock_conn
    query = sql.SQL('')

    await execute_psql_query(conn, query, fetch='one', dict_cursor=False)

    conn.cursor.assert_called_once_with(row_factory=rows.tuple_row)


# Test that fetch='one' uses fetchone
@pytest.mark.asyncio
async def test_fetch_one_calls_fetchone(mock_conn):
    conn, mock_cursor = mock_conn
    query = sql.SQL('')

    await execute_psql_query(conn, query, fetch='one')

    mock_cursor.fetchone.assert_called_once()
    mock_cursor.fetchall.assert_not_called()


# Test that fetch='all' uses fetchall
@pytest.mark.asyncio
async def test_fetch_all_calls_fetchall(mock_conn):
    conn, mock_cursor = mock_conn
    query = sql.SQL('')

    await execute_psql_query(conn, query, fetch='all')

    mock_cursor.fetchall.assert_called_once()
    mock_cursor.fetchone.assert_not_called()


# Test that fetch=None does not fetch
@pytest.mark.asyncio
async def test_fetch_none_fetches_none(mock_conn):
    conn, mock_cursor = mock_conn
    query = sql.SQL('')

    await execute_psql_query(conn, query)

    mock_cursor.fetchall.assert_not_called()
    mock_cursor.fetchone.assert_not_called()
