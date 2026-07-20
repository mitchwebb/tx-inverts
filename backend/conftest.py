# Make fake conn/cur for calling functions
import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient
import psycopg
from psycopg import sql
import pytest
import pytest_asyncio

from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema import ALL_TABLES
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from backend.jobs.tasks.tables import initialize_all_tables

from backend.main import app


# Don't show logging messages while testing
logging.disable(logging.CRITICAL)


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
@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
async def setup_gbif_schema(conn):
    """Fixture to initialize test db tables"""

    await initialize_all_tables(conn)

    yield


@pytest_asyncio.fixture
async def test_pool(conn):
    """Fake pool fixture for test app"""

    class FakePool:
        def connection(self):
            return _ConnCtx(conn)

    class _ConnCtx:
        def __init__(self, conn):
            self.conn = conn

        async def __aenter__(self):
            return self.conn

        async def __aexit__(self, *exc):
            pass  # don't close — conn fixture owns lifecycle

    return FakePool()


@pytest_asyncio.fixture
async def test_app(test_pool):
    """Test app for test client"""

    app.state.db_pool = test_pool
    yield app


@pytest_asyncio.fixture
async def client(test_app):
    """Test app client for making endpoint calls"""

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        yield c


@pytest.mark.asyncio
async def insert_rows(rows, table_name: str, conn: psycopg.AsyncConnection):
    """
    Insert rows into testing tables. 
    Infers column names from row objects.
    As a result, each row must contain the same columns.
    """
    columns = list(rows[0].keys())
    query = sql.SQL('''
        INSERT INTO {table} ({fields})
        VALUES ({placeholders})
    ''').format(
        table=sql.Identifier(table_name),
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )

    for row in rows:
        await execute_psql_query(conn, query, tuple(row.values()))


@pytest_asyncio.fixture
async def tx_bounding_box(setup_gbif_schema, conn):
    """Fill texas geometry table"""
    rows = [{
        'id': '939f959a-b5c2-4908-9ae1-6ab9ab2b3ae0',
        'state': 'Texas',
        'geometry': 'MULTIPOLYGON(((-106.65 25.8, -93.5 25.8, -93.5 36.5, -106.65 36.5, -106.65 25.8)))'
    }]
    await insert_rows(rows, TEXAS_GEOMETRY_TABLE.name, conn)
