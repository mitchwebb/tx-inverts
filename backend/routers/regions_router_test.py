import pytest
from psycopg import sql
import pytest_asyncio
from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.db.schema.regions import REGIONS_VIEW
from backend.jobs.tasks.views import refresh_materialized_view
from backend.routers.regions_router import format_park


counties = [
    {
        'id': 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc',
        'county': 'Travis',
        'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
    },
    {
        'id': 'ddbaaa24-8a5b-4b4b-af21-ff57f8a0077e',
        'county': 'Denton',
        'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
    }
]

parks = [
    {
        'id': '5dd66bb5-f81c-483d-b289-81a84174ec3a',
        'prop_name': 'Sparky Pocket Park',
        'alt_prop_name': '',
        'prop_class': 'City',
        'owner': 'Austin, City of',
        'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
    },
    {
        'id': 'f571c45d-387c-4d75-908b-e0028c4d6612',
        'prop_name': 'Balmorhea',
        'alt_prop_name': '',
        'prop_class': 'State',
        'owner': 'Public; unknown',
        'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
    }
]


@pytest_asyncio.fixture
async def basic_regions_view(setup_gbif_schema, conn):

    await insert_rows(counties, TEXAS_COUNTIES_TABLE.name, conn)
    await insert_rows(parks, TEXAS_PARKS_TABLE.name, conn)

    await refresh_materialized_view(conn, REGIONS_VIEW.name)


class TestGetRegionInfo():
    @pytest.mark.asyncio
    async def test_basic_region_info_retrieval(self, client, basic_regions_view):
        response = await client.get('/regions/get_region_info', params={'region_id': 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc'})
        result = response.json()

        assert result['name'] == 'Travis'
        assert result['region_type'] == 'county'

        response = await client.get('/regions/get_region_info', params={'region_id': '5dd66bb5-f81c-483d-b289-81a84174ec3a'})
        result = response.json()

        assert result['name'] == 'Sparky Pocket Park'
        assert result['region_type'] == 'park'

    @pytest.mark.asyncio
    async def test_404_missing_region(self, client, basic_regions_view):
        response = await client.get('/regions/get_region_info', params={'region_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'})
        assert response.status_code == 404

        result = response.json()

        assert result['detail'] == 'Region aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa not found'


class TestSearchRegions():
    """Tests for both search_counties and search_parks"""
    @pytest.mark.asyncio
    async def test_basic_counties_search(self, client, basic_regions_view):
        response = await client.get('/regions/search_counties', params={'search_term': 'tra'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]['id'] == 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc'
        assert {'id', 'county'}.issubset(result[0].keys())

        response = await client.get('/regions/search_counties', params={'search_term': 'den'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]['id'] == 'ddbaaa24-8a5b-4b4b-af21-ff57f8a0077e'
        assert result[0]['id']

    @pytest.mark.asyncio
    async def test_basic_counties_empty(self, client, basic_regions_view):
        response = await client.get('/regions/search_counties', params={'search_term': 'zzz'})
        assert response.status_code == 200
        result = response.json()
        assert not result  # Results array should be empty

    @pytest.mark.asyncio
    async def test_basic_parks_search(self, client, basic_regions_view):
        response = await client.get('/regions/search_parks', params={'search_term': 'spa'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]['id'] == '5dd66bb5-f81c-483d-b289-81a84174ec3a'
        assert {'prop_name', 'alt_prop_name', 'prop_class',
                'owner', 'id'}.issubset(result[0].keys())

        response = await client.get('/regions/search_parks', params={'search_term': 'bal'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]['id'] == 'f571c45d-387c-4d75-908b-e0028c4d6612'

    @pytest.mark.asyncio
    async def test_basic_parks_empty(self, client, basic_regions_view):
        response = await client.get('/regions/search_parks', params={'search_term': 'zzz'})
        assert response.status_code == 200
        result = response.json()
        assert not result  # Results array should be empty


class TestParkFormatting:
    async def test_park_formatting(self):
        """Test some known 'owner' values and their associated formatting fixes."""

        formatted_row = format_park(parks[0])
        assert formatted_row.owner == 'City of Austin'

        formatted_row = format_park(parks[1])
        assert formatted_row.owner == 'Public'
