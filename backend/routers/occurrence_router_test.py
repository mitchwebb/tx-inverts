from backend.core.exception_handler import TaxonNotFoundError
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.conftest import insert_rows
import pytest_asyncio
import pytest

from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view
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
    }
]
# Include some observations with range_extent adding up to 50km2 (rounded)
occ = [
    {
        'gbif_id': 1,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2020-03-04',
        'kingdom_key': 1,
        'family_key': 4342,
        'genus_key': 1323108,
        'species_key': 5035741,
        'geometry': 'POINT(-100.0 31.0)',
        'dataset_key': '07ad9e66-6a83-4054-b176-ef6bc5196b4f'
    },
    {
        'gbif_id': 2,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2021-03-04',
        'kingdom_key': 1,
        'family_key': 4342,
        'genus_key': 1323108,
        'species_key': 5035741,
        'geometry': 'POINT(-99.895  31.000)',
        'dataset_key': '07ad9e66-6a83-4054-b176-ef6bc5196b4f'
    },
    {
        'gbif_id': 3,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2019-03-04',
        'kingdom_key': 1,
        'family_key': 4342,
        'genus_key': 1323108,
        'species_key': 5035741,
        'geometry': 'POINT(-100.000 31.090)',
        'dataset_key': '1e3cf1be-3f9c-48d4-8da8-af28d21216ee'
    }
]


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

datasets = [
    {
        'dataset_key': '07ad9e66-6a83-4054-b176-ef6bc5196b4f',
        'dataset_title': 'dataset_1'
    },
    {
        'dataset_key': '1e3cf1be-3f9c-48d4-8da8-af28d21216ee',
        'dataset_title': 'dataset_2'
    }
]


@pytest_asyncio.fixture
async def simple_datasets_table(setup_gbif_schema, conn):
    await insert_rows(datasets, GBIF_DATASET_META.name, conn)


class TestGetDatasets:
    @pytest.mark.asyncio
    async def test_get_dataset_table_success(self, simple_datasets_table, client):
        response = await client.get(
            '/occurrence/get_datasets',
        )
        result = response.json()
        assert len(result['datasets']) == 2

        retrieved_keys = {item['dataset_key'] for item in result['datasets']}
        expected_keys = {item['dataset_key'] for item in datasets}
        assert retrieved_keys == expected_keys

    @pytest.mark.asyncio
    async def test_get_dataset_table_empty(self, setup_gbif_schema, client):
        response = await client.get(
            '/occurrence/get_datasets',
        )
        assert response.status_code == 404
        assert 'No datasets' in response.json()['detail']


class TestGetDatasetCounts:
    @pytest.mark.asyncio
    async def test_basic_dataset_counts_success(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_dataset_counts',
            json={
                'taxon_id': 4342,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
            }
        )
        result = response.json()
        assert result
        assert result['07ad9e66-6a83-4054-b176-ef6bc5196b4f'] == 2
        assert result['1e3cf1be-3f9c-48d4-8da8-af28d21216ee'] == 1

    @pytest.mark.asyncio
    async def test_dataset_counts_responds_to_filters(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_dataset_counts',
            json={
                'taxon_id': 4342,
                'include_inat': True,
                'date_start': '2020-09-04',
                'date_end': None,
            }
        )
        result = response.json()
        assert result
        assert result['07ad9e66-6a83-4054-b176-ef6bc5196b4f'] == 1
        assert result['1e3cf1be-3f9c-48d4-8da8-af28d21216ee'] == 0

    @pytest.mark.asyncio
    async def test_dataset_counts_empty_returns_none(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_dataset_counts',
            json={
                'taxon_id': 4084,
            }
        )
        result = response.json()
        assert result is None

    @pytest.mark.asyncio
    async def test_dataset_counts_taxon_not_found(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_dataset_counts',
            json={
                'taxon_id': 99999999999,
            }
        )
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']


class TestGetObservationDates:
    @pytest.mark.asyncio
    async def test_basic_dataset_counts_success(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_observation_dates',
            json={
                'taxon_id': 5035741,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
            }
        )
        result = response.json()
        assert result['min_date'] == '2019-03-04'
        assert result['max_date'] == '2021-03-04'

    @pytest.mark.asyncio
    async def test_basic_dataset_counts_filter(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_observation_dates',
            json={
                'taxon_id': 5035741,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
                'datasets': ['1e3cf1be-3f9c-48d4-8da8-af28d21216ee']
            }
        )
        result = response.json()
        assert result['min_date'] == '2019-03-04'
        assert result['max_date'] == '2019-03-04'

    @pytest.mark.asyncio
    async def test_basic_dataset_counts_missing_taxon(self, simple_tx_taxa, client):
        response = await client.post(
            '/occurrence/get_observation_dates',
            json={
                'taxon_id': 99999999999,
                'include_inat': True,
                'date_start': None,
                'date_end': None,
            }
        )
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']


class TestObservationTiles:

    ### Heatmap tiles (z<10) ###
    @pytest.mark.asyncio
    async def test_obs_heatmap_tile_with_features(self, simple_tx_taxa, client):
        response = await client.get(
            '/occurrence/tiles/9/113/209.mvt',
            params=[
                ('taxon_id', 5035741),
                ('include_inat', True),
                ('date_start', None),
                ('date_end', None),
            ],
        )

        assert response.status_code == 200
        # Content should have features in it
        assert response.content
        # Should contain observations-heatmap features
        assert b'observations-heatmap' in response.content

        assert response.headers['content-type'] == 'application/x-protobuf'

    @pytest.mark.asyncio
    async def test_obs_heatmap_tile_without_features(self, simple_tx_taxa, client):
        """Tile without features should be empty bytes (b'')"""

        response = await client.get(
            '/occurrence/tiles/9/309/398.mvt',
            params=[
                ('taxon_id', 5035741),
                ('include_inat', True),
                ('date_start', None),
                ('date_end', None),
            ],
        )

        assert response.status_code == 200
        assert response.content is b''  # Content should be empty bytes
        assert response.headers['content-type'] == 'application/x-protobuf'

    @pytest.mark.asyncio
    async def test_obs_heatmap_date_filter_excludes_old_records(self, simple_tx_taxa, client):
        """
        This serves as a simple are-the-filters-plugged-in check. 
        Observations filters are more thoroughly checked in their own tests.
        """

        response = await client.get(
            '/occurrence/tiles/10/227/419.mvt',
            params=[
                ('taxon_id', 5035741),
                ('date_start', '2022-01-01'),
            ],
        )

        assert response.status_code == 200
        assert response.content == b''

    ### Circle Tiles (z>=10) ###
    @pytest.mark.asyncio
    async def test_obs_circles_tile_with_features(self, simple_tx_taxa, client):
        response = await client.get(
            '/occurrence/tiles/10/227/419.mvt',
            params=[
                ('taxon_id', 5035741),
                ('include_inat', True),
                ('date_start', None),
                ('date_end', None),
            ],
        )

        assert response.status_code == 200
        # Content should have features in it
        assert response.content
        # Should contain observations-circles features
        assert b'observations-circles' in response.content

        assert response.headers['content-type'] == 'application/x-protobuf'

    @pytest.mark.asyncio
    async def test_obs_circles_tile_without_features(self, simple_tx_taxa, client):
        """Tile without features should be empty bytes (b'')"""

        response = await client.get(
            '/occurrence/tiles/10/309/398.mvt',
            params=[
                ('taxon_id', 5035741),
                ('include_inat', True),
                ('date_start', None),
                ('date_end', None),
            ],
        )

        assert response.status_code == 200
        assert response.content is b''  # Content should be empty bytes
        assert response.headers['content-type'] == 'application/x-protobuf'
