from unittest.mock import AsyncMock

import aiohttp
import pytest

from backend.config import get_settings
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.jobs.tasks.dataset_tasks import fill_dataset_table

from psycopg import sql

settings = get_settings()


class TestFillDatasetTable:
    @pytest.mark.asyncio
    async def test_inserts_dataset_title_into_table(self, conn, mocker):
        """Happy path: fetched dataset info is written to gbif_dataset_metadata."""
        dataset_key = '07ad9e66-6a83-4054-b176-ef6bc5196b4f'
        mocker.patch(
            'backend.jobs.tasks.dataset_tasks.fetch_data',
            new=AsyncMock(return_value={'title': 'Test Dataset Title'})
        )
        await fill_dataset_table(conn, [dataset_key])

        result = await execute_psql_query(
            conn,
            sql.SQL("SELECT dataset_title FROM {dataset_table} WHERE dataset_key = {key}").format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                key=sql.Literal(dataset_key),
            ),
            fetch='one'
        )
        assert result is not None
        assert result[0] == 'Test Dataset Title'

    @pytest.mark.asyncio
    async def test_missing_dataset_info_is_skipped_not_raised(self, conn, mocker):
        """If GBIF returns None for a dataset key, log and continue rather than error."""
        dataset_key = 'nonexistent-key'
        mocker.patch(
            'backend.jobs.tasks.dataset_tasks.fetch_data',
            new=AsyncMock(return_value=None)
        )
        # Should not raise
        await fill_dataset_table(conn, [dataset_key])

        result = await execute_psql_query(
            conn,
            sql.SQL("SELECT dataset_title FROM {dataset_table} WHERE dataset_key = {key}").format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                key=sql.Literal(dataset_key),
            ),
            fetch='one'
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_conflict_updates_existing_title(self, conn, mocker):
        """ON CONFLICT should update dataset_title, not duplicate or error on repeat key."""
        dataset_key = '07ad9e66-6a83-4054-b176-ef6bc5196b4f'
        fetch_mock = mocker.patch(
            'backend.jobs.tasks.dataset_tasks.fetch_data',
            new=AsyncMock(return_value={'title': 'Original Title'})
        )
        await fill_dataset_table(conn, [dataset_key])

        fetch_mock.return_value = {'title': 'Updated Title'}
        await fill_dataset_table(conn, [dataset_key])

        result = await execute_psql_query(
            conn,
            sql.SQL("SELECT dataset_title FROM {dataset_table} WHERE dataset_key = {key}").format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                key=sql.Literal(dataset_key),
            ),
            fetch='one'
        )
        assert result is not None
        assert result[0] == 'Updated Title'

    @pytest.mark.asyncio
    async def test_multiple_dataset_ids_processed_independently(self, conn, mocker):
        """A None result for one key shouldn't prevent others from being inserted."""
        key_ok = 'good-key'
        key_missing = 'missing-key'

        async def fake_fetch(session, url):
            if key_missing in url:
                return None
            return {'title': 'Good Dataset'}

        mocker.patch(
            'backend.jobs.tasks.dataset_tasks.fetch_data',
            new=AsyncMock(side_effect=fake_fetch)
        )
        await fill_dataset_table(conn, [key_ok, key_missing])

        result = await execute_psql_query(
            conn,
            sql.SQL("SELECT dataset_title FROM {dataset_table} WHERE dataset_key = {key}").format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                key=sql.Literal(key_ok),
            ),
            fetch='one'
        )
        assert result is not None
        assert result[0] == 'Good Dataset'

    @pytest.mark.asyncio
    async def test_empty_dataset_ids_no_op(self, conn):
        """Empty list should complete without inserting or erroring."""
        # Should not raise, should not touch the DB meaningfully
        await fill_dataset_table(conn, [])

    @pytest.mark.asyncio
    @pytest.mark.requires_external_api
    @pytest.mark.skipif(
        not settings.gbif.uat_user or not settings.gbif.uat_password,
        reason="GBIF UAT credentials not configured"
    )
    async def test_real_gbif_dataset_response_has_title_key(self):
        """
        Confirms the live GBIF API still returns a 'title' key on dataset info,
        since fill_dataset_table assumes dataset_info['title'] unconditionally.
        """
        known_dataset_key = '50c9509d-22c7-4a22-a47d-8c48425ef4a7'  # GBIF backbone taxonomy
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f'https://api.gbif.org/v1/dataset/{known_dataset_key}'
            )
            assert response.status == 200
            body = await response.json()
            assert 'title' in body
