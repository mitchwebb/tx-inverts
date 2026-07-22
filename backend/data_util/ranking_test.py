import pytest
import pytest_asyncio
from backend.conftest import insert_rows
from backend.core.exception_handler import TaxonNotFoundError
from backend.data_util.ranking import calculate_ns_values, calculate_rank
from backend.db.queries.occurrence import create_occurrence_filter_sql
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.views import refresh_materialized_view
from backend.models.occurrence import OccurrenceFilters


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    # Values to insert into backbone table, then brought into tx_taxa mat view
    taxa = [
        {
            'scientific_name': 'Atta texana',
            'canonical_name': 'Atta texana',
            'taxon_id': 5035741,
            'accepted_name_usage_id': 5035741,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
        },
        {
            'scientific_name': 'Atta',
            'canonical_name': 'Atta',
            'taxon_id': 1323108,
            'accepted_name_usage_id': None,
            'taxon_rank': 'genus',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': None
        },
        {
            'scientific_name': 'Scolopendra heros',
            'canonical_name': 'Scolopendra heros',
            'taxon_id': 5179407,
            'accepted_name_usage_id': None,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4084,
            'genus_id': 2231802,
            'species_id': None
        },
        # Taxon with no occurrence records
        {
            'scientific_name': 'Notfoundin texana',
            'canonical_name': 'Notfoundin texana',
            'taxon_id': 0000000,
            'accepted_name_usage_id': None,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 2,
            'genus_id': 3,
            'species_id': 0000000
        },
    ]
    # Include some observations with range_extent adding up to 50km2 (rounded)
    occ = [
        {
            'gbif_id': 1,
            'taxon_key': 5035741,
            'accepted_taxon_key': 5035741,
            'collection_start_date': '2021-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
            'geometry': 'POINT(-100.0 31.0)'
        },
        {
            'gbif_id': 2,
            'taxon_key': 5035741,
            'accepted_taxon_key': 5035741,
            'collection_start_date': '2021-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
            'geometry': 'POINT(-99.895  31.000)'
        },
        {
            'gbif_id': 3,
            'taxon_key': 5035741,
            'accepted_taxon_key': 5035741,
            'collection_start_date': '2021-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
            'geometry': 'POINT(-100.000 31.090)'
        },
        {
            'gbif_id': 4,
            'taxon_key': 5035741,
            'accepted_taxon_key': 5035741,
            'collection_start_date': '2021-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
            'geometry': 'POINT(-100.000 31.080)'
        },
        {
            'gbif_id': 5,
            'taxon_key': 1323108,
            'accepted_taxon_key': 1323108,
            'collection_start_date': '2022-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': None,
            'geometry': 'POINT(-100.0 33.0)'
        },
        {
            'gbif_id': 6,
            'taxon_key': 5179407,
            'accepted_taxon_key': 5179407,
            'collection_start_date': '2024-03-04',
            'kingdom_id': 1,
            'family_id': 4084,
            'genus_id': 2231802,
            'species_id': None,
            'geometry': 'POINT(1.0 1.0)'
        },
    ]

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)


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
    async def test_simple_values_calculation(self, conn, tx_bounding_box, simple_tx_taxa):
        """Test successful ns_values calculation with predicted values"""

        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        filters = OccurrenceFilters(
            taxon_ids=[5035741],
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
        # Test points calculated to be close to 50km2
        assert round(ns_values['range_extent_km2']) == 50
        assert ns_values['number_of_occurrences'] == 4
        assert ns_values['observation_count'] == 4
        # Two points are close enough together to be merged with 4km2 bins
        assert ns_values['area_of_occupancy_4km2_bins'] == 3
        # But not close enough to merge at 1km2
        assert ns_values['area_of_occupancy_1km2_bins'] == 4

    async def test_higher_taxon_values(self, conn, tx_bounding_box, simple_tx_taxa):
        """Test requesting a parent genus includes children"""

        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        filters = OccurrenceFilters(
            taxon_ids=[1323108],
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

    async def test_empty_taxon_returns_zeroes(self, conn, tx_bounding_box, simple_tx_taxa):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        filters = OccurrenceFilters(
            taxon_ids=[0000000],
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

    async def test_missing_taxon_errors(self, conn, tx_bounding_box, simple_tx_taxa):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        filters = OccurrenceFilters(
            taxon_ids=[99999999999999],
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

    async def test_dont_compute_occurrences(self, conn, tx_bounding_box, simple_tx_taxa):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        filters = OccurrenceFilters(
            taxon_ids=[1323108],
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
