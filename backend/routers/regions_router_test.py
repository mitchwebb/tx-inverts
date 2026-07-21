import pytest
from psycopg import sql
import pytest_asyncio
from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.db.schema.regions import REGIONS_VIEW
from backend.jobs.tasks.views import refresh_materialized_view


county = [{
    'id': 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc',
    'county': 'Travis',
    'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
}]

park = [{
    'id': '5dd66bb5-f81c-483d-b289-81a84174ec3a',
    'prop_name': 'Sparky Pocket Park',
    'geometry': 'MULTIPOLYGON(((0 0, 0 0, 0 0, 0 0)))'
}]


@pytest_asyncio.fixture
async def basic_regions_view(setup_gbif_schema, conn):

    await insert_rows(county, TEXAS_COUNTIES_TABLE.name, conn)
    await insert_rows(park, TEXAS_PARKS_TABLE.name, conn)

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
