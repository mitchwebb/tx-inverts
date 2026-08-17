import uuid

import pytest
import pytest_asyncio
from psycopg import sql

from backend.conftest import insert_rows
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.regions import REGIONS_VIEW
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view, refresh_materialized_views, check_for_mat_view
from backend.db.schema.index_definitions import MATERIALIZED_VIEWS

REGION_A_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
REGION_B_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')

# Minimal data — one taxon, one occurrence — enough for tx_taxa/lineage/presence
# to have something real to select from. These tests
# are about the refresh mechanics, not query correctness.
MINIMAL_TAXA = [
    {
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
]

MINIMAL_OCC = [
    {
        'gbif_id': 1, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2020-03-04', 'collection_end_date': '2020-03-05',
        'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035741,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
]

# All four real matviews this codebase actually refreshes, in the order
# occurrence_filter_data refreshes them — treated as the expected dependency order.
REAL_VIEW_NAMES = [TX_TAXA_TABLE.name, REGIONS_VIEW.name, TAXON_PRESENCE_TABLE.name,
                   TAXON_LINEAGE_TABLE.name]


async def _drop_view(conn, view_name: str) -> None:
    async with conn.cursor() as cur:
        await cur.execute(
            sql.SQL("DROP MATERIALIZED VIEW IF EXISTS {} CASCADE").format(
                sql.Identifier(view_name)
            )
        )


@pytest_asyncio.fixture
async def clean_matviews(conn):
    """Drop all real matviews before AND after each test."""
    for name in REAL_VIEW_NAMES:
        await _drop_view(conn, name)
    yield
    for name in REAL_VIEW_NAMES:
        await _drop_view(conn, name)


@pytest_asyncio.fixture
async def base_data(conn, setup_gbif_schema):
    """Just enough real rows for tx_taxa/lineage/presence to build against."""
    await insert_rows(MINIMAL_TAXA, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(MINIMAL_OCC, GBIF_OBSERVATIONS_TABLE.name, conn)
    return conn


class TestCheckForMatView:
    @pytest.mark.asyncio
    async def test_check_for_mat_view_false_when_absent(self, conn, clean_matviews):
        assert await check_for_mat_view(conn, TX_TAXA_TABLE.name) is False

    @pytest.mark.asyncio
    async def test_check_for_mat_view_true_after_create(self, conn, clean_matviews, base_data):
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
        assert await check_for_mat_view(conn, TX_TAXA_TABLE.name) is True

    @pytest.mark.asyncio
    async def test_check_for_mat_view_does_not_match_substring(self, conn, clean_matviews, base_data):
        """Guards against a LIKE-style query accidentally matching partial names."""
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
        assert await check_for_mat_view(conn, TX_TAXA_TABLE.name + "_extra") is False


class RefreshMaterializedView:
    @pytest.mark.asyncio
    async def test_refresh_unknown_view_raises_value_error(self, mock_conn):
        conn, _ = mock_conn
        with pytest.raises(ValueError):
            await refresh_materialized_view(conn, "definitely_not_a_configured_view")

    @pytest.mark.asyncio
    async def test_refresh_creates_view_when_missing(self, conn, clean_matviews, base_data):
        await _drop_view(conn, TX_TAXA_TABLE.name)
        assert await check_for_mat_view(conn, TX_TAXA_TABLE.name) is False

        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

        assert await check_for_mat_view(conn, TX_TAXA_TABLE.name) is True

    @pytest.mark.asyncio
    async def test_refresh_created_view_contains_seeded_row(self, conn, clean_matviews, base_data):
        """
        Confirm the created view actually selected the real data, 
        i.e. create_sql ran against live tables and not an empty stub.
        """
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

        async with conn.cursor() as cur:
            await cur.execute(
                sql.SQL(
                    "SELECT count(*) FROM {}").format(sql.Identifier(TX_TAXA_TABLE.name))
            )
            row = await cur.fetchone()

        assert row[0] >= 1

    @pytest.mark.asyncio
    async def test_refresh_existing_view_does_not_error(self, conn, clean_matviews, base_data):
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)  # create
        # refresh — must not raise
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

    @pytest.mark.asyncio
    async def test_refresh_existing_view_picks_up_new_rows(self, conn, clean_matviews, base_data):
        # create, 1 taxon
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

        async with conn.cursor() as cur:
            await cur.execute(
                sql.SQL(
                    "SELECT count(*) FROM {}").format(sql.Identifier(TX_TAXA_TABLE.name))
            )
            (before,) = await cur.fetchone()

        await insert_rows(
            [{'taxon_id': 5035742, 'accepted_name_usage_id': 5035742,
              'species_id': 5035742, 'scientific_name': 'Atta second',
              'canonical_name': 'Atta second'}],
            GBIF_INVERTS_BACKBONE.name,
            conn,
        )
        await insert_rows(
            [{
                'gbif_id': 2, 'taxon_key': 5035742, 'accepted_taxon_key': 5035742,
                'collection_start_date': '2020-03-04', 'collection_end_date': '2020-03-05',
                'kingdom_id': 1, 'family_id': 4342, 'genus_id': 1323108, 'species_id': 5035742,
                'dataset_key': 'dataset-a', 'institution_code': 'TxState',
                'coordinate_uncertainty_in_meters': 100,
                'geometry': 'POINT(-97.7431 30.2672)',
            }],
            GBIF_OBSERVATIONS_TABLE.name,
            conn
        )

        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)  # refresh

        async with conn.cursor() as cur:
            await cur.execute(
                sql.SQL(
                    "SELECT count(*) FROM {}").format(sql.Identifier(TX_TAXA_TABLE.name))
            )
            (after,) = await cur.fetchone()

        assert after > before


class TestRefreshMaterializedViews:
    @pytest.mark.asyncio
    async def test_refresh_materialized_views_builds_all_in_dependency_order(
        self, conn, clean_matviews, base_data
    ):
        """
        Regression guard for dict-order fragility: refresh_materialized_views has
        no explicit dependency resolution, it just iterates MATERIALIZED_VIEWS.
        If that dict is manually reordered (or a view is added alphabetically without
        thinking about dependencies), lineage/presence would try to build against
        a tx_taxa that doesn't exist yet and this test should catch it.
        """
        assert list(MATERIALIZED_VIEWS.keys())[:4] == REAL_VIEW_NAMES, (
            "MATERIALIZED_VIEWS order no longer matches expected order"
        )

        await refresh_materialized_views(conn)

        for name in REAL_VIEW_NAMES:
            assert await check_for_mat_view(conn, name) is True

    @pytest.mark.asyncio
    async def test_refresh_materialized_views_second_pass_refreshes_not_errors(
        self, conn, clean_matviews, base_data
    ):
        await refresh_materialized_views(conn)  # create all
        await refresh_materialized_views(conn)  # refresh all — must not raise
