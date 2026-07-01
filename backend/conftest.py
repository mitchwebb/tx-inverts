# Make fake conn/cur for calling functions
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

import psycopg
from psycopg import sql
import pytest

from backend.db.schema import ALL_TABLES
from backend.jobs.tasks.tables import initialize_all_tables


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Mock connection for unit tests that don't need real DB operations
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


# Make test connection for local test_inverts db
@pytest.fixture
async def conn():
    conn = await psycopg.AsyncConnection.connect(
        host='localhost',
        dbname='test_inverts',
        port=5432,
        user='test_user',
        password='test_pass',
    )
    await conn.set_autocommit(True)

    async with conn.cursor() as cur:
        for t in ALL_TABLES:
            try:
                await cur.execute(
                    sql.SQL('TRUNCATE {table} RESTART IDENTITY CASCADE').format(
                        table=sql.Identifier(t.name)
                    )
                )
            except Exception:
                pass

    yield conn

    await conn.close()


@pytest.fixture
async def setup_gbif_schema(conn):
    await initialize_all_tables(conn)

    yield
