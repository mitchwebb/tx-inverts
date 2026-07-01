from datetime import date

import pytest

from psycopg import sql
from backend.data_util.gbif.get_latest_record_date import get_latest_record_date
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE


@pytest.fixture
async def observations_with_dates(conn, setup_gbif_schema):
    async with conn.cursor() as cur:
        await cur.execute(sql.SQL('''
            INSERT INTO {observations_table} (gbif_id, modified, last_interpreted)
            VALUES 
                (1, '2021-06-01', '2021-07-01'),
                (2, '2020-06-01', '2020-07-01'),
                (3, '3000-06-01', '3000-07-01'),
                (4, NULL, NULL)
        ''').format(
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        ))
    yield


@pytest.mark.db
@pytest.mark.asyncio
class TestGetLatestRecordDate:
    # Test that function gets expected 'modified' date
    async def test_gets_reasonable_modified_date(self, conn, setup_gbif_schema, observations_with_dates):
        result = await get_latest_record_date(conn, 'modified')
        assert result == date(2021, 6, 1)

    # Test that function gets expected 'last_interpreted' date
    async def test_gets_reasonable_last_interpreted_date(self, conn, setup_gbif_schema, observations_with_dates):
        result = await get_latest_record_date(conn, 'last_interpreted')
        assert result == date(2021, 7, 1)

    # Test to make sure dates in the future are thrown out
    async def test_rejects_future_date(self, conn, setup_gbif_schema):
        today = date.today()
        next_year = date(today.year + 1, today.month, today.day)
        async with conn.cursor() as cur:
            await cur.execute(sql.SQL('''
                INSERT INTO {observations_table} (gbif_id, modified)
                    VALUES (1, {next_year})
            ''').format(
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
                next_year=sql.Literal(next_year)
            ))

        result = await get_latest_record_date(conn, 'modified')
        assert result is None
