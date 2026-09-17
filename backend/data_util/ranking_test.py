import pytest
import pytest_asyncio
from backend.conftest import insert_rows
from backend.core.exception_handler import TaxonNotFoundError
from backend.data_util.ranking import calculate_ns_values, calculate_rank
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.models.occurrence import OccurrenceFilters


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    # Values to insert into backbone table, then brought into tx_taxa mat view
    taxa = [
        {
            'scientific_name': 'Atta texana',
            'canonical_name': 'Atta texana',
            'taxon_id': 'ATTATX',
            'accepted_name_usage_id': 'ATTATX',
            'parent_name_usage_id': 'ATTA',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        {
            'scientific_name': 'Atta',
            'canonical_name': 'Atta',
            'taxon_id': 'ATTA',
            'parent_name_usage_id': 'HYM',
            'accepted_name_usage_id': None,
            'taxon_rank': 'genus',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        {
            'scientific_name': 'Scolopendra heros',
            'canonical_name': 'Scolopendra heros',
            'taxon_id': 'SCOLOH',
            'accepted_name_usage_id': 'SCOLOH',
            'parent_name_usage_id': 'SCOLO',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        # Taxon with no occurrence records
        {
            'scientific_name': 'Notfoundin texana',
            'canonical_name': 'Notfoundin texana',
            'taxon_id': 'NOTFOUNDTX',
            'accepted_name_usage_id': 'NOTFOUNDTX',
            'parent_name_usage_id': 'NOTFOUND',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
    ]
    # Include some observations with range_extent adding up to 50km2 (rounded)
    occ = [
        {
            'gbif_id': 1,
            'taxon_key': 'ATTATX',
            'accepted_taxon_key': 'ATTATX',
            'collection_start_date': '2021-03-04',
            'geometry': 'POINT(-100.0 31.0)'
        },
        {
            'gbif_id': 2,
            'taxon_key': 'ATTATX',
            'accepted_taxon_key': 'ATTATX',
            'collection_start_date': '2021-03-04',
            'geometry': 'POINT(-99.895  31.000)'
        },
        {
            'gbif_id': 3,
            'taxon_key': 'ATTATX',
            'accepted_taxon_key': 'ATTATX',
            'collection_start_date': '2021-03-04',
            'geometry': 'POINT(-100.000 31.090)'
        },
        {
            'gbif_id': 4,
            'taxon_key': 'ATTATX',
            'accepted_taxon_key': 'ATTATX',
            'collection_start_date': '2021-03-04',
            'geometry': 'POINT(-100.000 31.080)'
        },
        {
            'gbif_id': 5,
            'taxon_key': 'ATTA',
            'accepted_taxon_key': 'ATTA',
            'collection_start_date': '2022-03-04',
            'geometry': 'POINT(-100.0 33.0)'
        },
        {
            'gbif_id': 6,
            'taxon_key': 'SCOLOH',
            'accepted_taxon_key': 'SCOLOH',
            'collection_start_date': '2024-03-04',
            'geometry': 'POINT(1.0 1.0)'
        },
    ]

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)


@pytest.mark.parametrize(
    'occurrences,range_extent,area_of_occupancy,expected_rank', [
        (22,        998,         4,               '2'),
        (66,        2345,        100,             '3'),
        (342,       6723,        27,              '4'),
        (300,       10000000000, 4,               '3'),
        (0,         0,           None,            'u'),
        (10,        10,          1000000,         '4'),
        (1000,      1000,        None,            '4'),
    ])
def test_valid_rank_calculations(occurrences, range_extent, area_of_occupancy, expected_rank):
    """Small test to make sure rank calculations match the NS Calculator"""
    assert calculate_rank(occurrences, range_extent,
                          area_of_occupancy) == expected_rank


class TestCalculateNSValues:
    @pytest.mark.asyncio
    async def test_simple_values_calculation(self, conn, tx_bounding_box, simple_tx_taxa):
        """Test successful ns_values calculation with predicted values"""

        filters = OccurrenceFilters(
            taxon_ids=['ATTATX'],
            include_inat=None,
            date_start=None,
            date_end=None,
            datasets=None,
        )

        ns_values = await calculate_ns_values(
            conn,
            filters=filters
        )

        assert ns_values
        # Test points calculated to be close to 50km2
        assert round(ns_values['range_extent_km2']) == 50
        assert ns_values['number_of_occurrences'] == 4
        assert ns_values['observation_count'] == 4
        # Two points are close enough together to be merged with 4km2 bins
        assert ns_values['area_of_occupancy_4km2_bins'] == 3
        # But not close enough to merge at 1km2
        assert ns_values['area_of_occupancy_1km2_bins'] == 4

    @pytest.mark.asyncio
    async def test_higher_taxon_values(self, conn, tx_bounding_box, simple_tx_taxa):
        """Test requesting a parent genus includes children"""

        filters = OccurrenceFilters(
            taxon_ids=['ATTA'],
            include_inat=None,
            date_start=None,
            date_end=None,
            datasets=None
        )

        ns_values = await calculate_ns_values(
            conn,
            filters=filters,
        )

        assert ns_values
        assert round(ns_values['range_extent_km2']) == 1114
        assert ns_values['number_of_occurrences'] == 5
        assert ns_values['observation_count'] == 5
        # Two points are close enough together to be merged with 4km2 bins
        assert ns_values['area_of_occupancy_4km2_bins'] == 4
        # But not close enough to merge at 1km2
        assert ns_values['area_of_occupancy_1km2_bins'] == 5

    @pytest.mark.asyncio
    async def test_empty_taxon_returns_zeroes(self, conn, tx_bounding_box, simple_tx_taxa):
        filters = OccurrenceFilters(
            taxon_ids=['NOTFOUNDTX'],
            include_inat=None,
            date_start=None,
            date_end=None,
            datasets=None
        )

        ns_values = await calculate_ns_values(
            conn,
            filters=filters
        )

        assert ns_values
        assert round(ns_values['range_extent_km2']) == 0
        assert ns_values['number_of_occurrences'] == 0
        assert ns_values['observation_count'] == 0
        assert ns_values['area_of_occupancy_4km2_bins'] == 0
        assert ns_values['area_of_occupancy_1km2_bins'] == 0

    @pytest.mark.asyncio
    async def test_missing_taxon_errors(self, conn, tx_bounding_box, simple_tx_taxa):
        filters = OccurrenceFilters(
            taxon_ids=['99999999999999'],
            include_inat=None,
            date_start=None,
            date_end=None,
            datasets=None
        )

        with pytest.raises(TaxonNotFoundError):
            ns_values = await calculate_ns_values(
                conn,
                filters=filters
            )

    @pytest.mark.asyncio
    async def test_dont_compute_occurrences(self, conn, tx_bounding_box, simple_tx_taxa):
        filters = OccurrenceFilters(
            taxon_ids=['ATTA'],
            include_inat=None,
            date_start=None,
            date_end=None,
            datasets=None
        )

        ns_values = await calculate_ns_values(
            conn,
            filters=filters,
            compute_occurrences=False
        )

        assert ns_values
        assert ns_values['number_of_occurrences'] == None
