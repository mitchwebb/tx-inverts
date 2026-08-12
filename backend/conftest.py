# Make fake conn/cur for calling functions
import asyncio
import logging
import sys
from typing import List
import uuid
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient
import psycopg
from psycopg import sql
import pytest
import pytest_asyncio

from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema import ALL_TABLES
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.table_tasks import initialize_all_tables

from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.main import app


# Don't show logging messages while testing
logging.disable(logging.CRITICAL)


if sys.platform == 'win32':
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
async def insert_rows(rows: List[dict], table_name: str, conn: psycopg.AsyncConnection):
    """
    Insert rows into testing tables.
    Infers column names from row objects.
    As a result, each row must contain the same columns.
    """

    columns = list(rows[0].keys())
    query = sql.SQL("""
        INSERT INTO {table} ({fields})
        VALUES ({placeholders})
    """).format(
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


# Larger, filters-ready occurrence fixture for testing various endpoint behaviors

# Region UUIDs — fixed and readable so test assertions can reference them
# without recomputing anything at read time
REGION_A_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
REGION_B_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')

taxa = [
    {
        # non-invasive species, matches family 4342 for lineage/ancestor tests
        'scientific_name': 'Atta texana',
        'canonical_name': 'Atta texana',
        'taxon_id': 5035741,
        'accepted_name_usage_id': 5035741,
        'parent_name_usage_id': 4342,
        'taxon_rank': 'species',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1323108,
        'species_id': 5035741,
    },
    {
        # family row — required for taxon_lineage to resolve ancestor_id=4342
        # when a test filters by family-level taxon_id
        'scientific_name': 'Formicidae',
        'canonical_name': 'Formicidae',
        'taxon_id': 4342,
        'accepted_name_usage_id': 4342,
        'parent_name_usage_id': 1,
        'taxon_rank': 'family',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': None,
        'species_id': None,
    },
    {
        # invasive species, same family — exercises include_invasives branches
        'scientific_name': 'Solenopsis invicta',
        'canonical_name': 'Solenopsis invicta',
        'taxon_id': 9999001,
        'accepted_name_usage_id': 9999001,
        'parent_name_usage_id': 4342,
        'taxon_rank': 'species',
        'us_invasive': True,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 9999000,
        'species_id': 9999001,
    },
]

occ = [
    {
        # baseline row — passes every filter at defaults
        'gbif_id': 1, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2020-03-04', 'collection_end_date': '2020-03-05',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',  # Austin, TX
    },
    {
        # iNaturalist origin — tests include_inat=False exclusion
        'gbif_id': 2, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2021-03-04', 'collection_end_date': '2021-03-05',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-b', 'institution_code': 'iNaturalist',
        'coordinate_uncertainty_in_meters': 50,
        # Dallas, TX — far enough to swing extent if included
        'geometry': 'POINT(-96.7970 32.7767)',
    },
    {
        # collection_start_date NULL — tests hardcoded IS NOT NULL clause
        'gbif_id': 3, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': None, 'collection_end_date': None,
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # second dataset_key, distinct date, tagged to REGION_B_ID
        'gbif_id': 4, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2019-03-04', 'collection_end_date': '2019-03-05',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': None,  # tests "IS NULL OR <=" branch
        'geometry': 'POINT(-95.3698 29.7604)',  # Houston, TX
    },
    {
        # coordinate_uncertainty_in_meters == 0 — tests `is None` vs falsy bug
        'gbif_id': 5, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2022-01-01', 'collection_end_date': '2022-01-02',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-b', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 0,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # invasive taxon — tests include_invasives true/false branches
        'gbif_id': 6, 'taxon_key': 9999001, 'accepted_taxon_key': 9999001,
        'collection_start_date': '2022-06-01', 'collection_end_date': '2022-06-02',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 9999000, 'species_id': 9999001,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
]

observation_regions = [
    {'observation_id': 1, 'region_id': REGION_A_ID},
    {'observation_id': 4, 'region_id': REGION_B_ID},
]


@pytest_asyncio.fixture()
async def occurrence_filter_data(conn):
    """
    Minimal shared dataset covering every branch in
    create_occurrence_filter_sql and create_occurrence_taxon_filter.
    """
    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)
    await insert_rows(observation_regions, OBSERVATION_REGIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
    await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)

    return conn
