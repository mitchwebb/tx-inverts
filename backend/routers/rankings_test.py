import re

import pytest
import pytest_asyncio

from backend.conftest import insert_rows
from backend.core.exception_handler import TaxonNotFoundError
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.views import refresh_materialized_view

# Values to insert into backbone table, then brought into tx_taxa mat view
taxa = [
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
    {
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
        'species_id': None
    },
    {
        'scientific_name': 'Scolopendridae',
        'canonical_name': 'Scolopendridae',
        'taxon_id': 4084,
        'accepted_name_usage_id': 4084,
        'parent_name_usage_id': 1,
        'taxon_rank': 'family',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4084,
        'genus_id': None,
        'species_id': None
    }
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
    }
]


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)


class TestGetNSMetrics:
    @pytest.mark.asyncio
    async def test_get_simple_metrics(self, client, tx_bounding_box, simple_tx_taxa):
        """See that get_ns_metrics sends back metrics in the right format"""

        response = await client.post(
            '/rankings/get_ns_metrics',
            json={
                'taxon_id': 5035741,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': None,
                'taxon_rank': 'species'
            }
        )
        result = response.json()

        assert result
        assert result['range_extent_km2'] is not None
        assert result['observation_count'] is not None
        assert result['number_of_occurrences'] is not None
        assert result['area_of_occupancy_4km2_bins'] is not None
        assert result['area_of_occupancy_1km2_bins'] is not None

    @pytest.mark.asyncio
    async def test_higher_taxon_skips_occurrences(self, client, tx_bounding_box, simple_tx_taxa):
        """Test that get_ns_metrics returns None for 'number_of_occurrences' when taxon_rank is great than Genus"""

        response = await client.post(
            '/rankings/get_ns_metrics',
            json={
                'taxon_id': 4342,  # Target parent taxon
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': None,
            }
        )
        result = response.json()

        assert result
        assert result['number_of_occurrences'] == None


class TestGetRangeExtentGeom:
    @pytest.mark.asyncio
    async def test_get_range_extent_geom(self, client, tx_bounding_box, simple_tx_taxa):
        """For an existing taxon, get basic range_extent_geom matching provided points"""

        test_taxon_key = 5035741

        response = await client.post(
            '/rankings/get_range_extent_geom',
            json={
                'taxon_id': test_taxon_key,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': None,
            }
        )
        result = response.json()

        # Get all coords from resulting geometry as set (filter out start/end repeat)
        coords = result['range_extent_geom']['coordinates'][0]
        actual_points = {tuple(pt) for pt in coords}

        # Helper to parse lat/lon from our occ geometry values
        def parse_point(wkt):
            lon, lat = re.findall(r'-?[\d.]+', wkt)
            return (float(lon), float(lat))

        # Get set of lat/lon from our passed-in occurrences
        expected_points = {parse_point(r['geometry'])
                           for r in occ if r['accepted_taxon_key'] == test_taxon_key}

        # Geometric equality, not coordinate-order equality
        assert actual_points == expected_points

    @pytest.mark.asyncio
    async def test_no_matching_taxon(self, client, tx_bounding_box, simple_tx_taxa):
        """Test that we raise TaxonNotFound on requested taxon that doesn't exist in backbone"""

        test_taxon_key = 9999999

        response = await client.post(
            '/rankings/get_range_extent_geom',
            json={
                'taxon_id': test_taxon_key,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': None,
            }
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['detail']

    @pytest.mark.asyncio
    async def test_no_matching_occurrences(self, client, tx_bounding_box, simple_tx_taxa):
        """Test that an existing taxon with no occurrences returns None for range_extent_geom"""

        test_taxon_key = 4084

        response = await client.post(
            '/rankings/get_range_extent_geom',
            json={
                'taxon_id': test_taxon_key,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': None,
            }
        )

        assert response.status_code == 200
        assert response.json()['range_extent_geom'] is None
