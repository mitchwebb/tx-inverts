from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.db.schema.index_definitions import INDEX_DEFINITIONS
from backend.jobs.tasks.indexes import update_index


class TestUpdateIndex:
    @pytest.mark.asyncio
    async def test_raises_on_missing_def(self, mock_conn):
        with pytest.raises(ValueError):
            await update_index(mock_conn, 'fake_index')

    @pytest.mark.asyncio
    async def test_reindex_existing(self, mock_conn, mocker):
        conn, _ = mock_conn
        conn.commit = AsyncMock()

        # Get name of real index
        index_name = next(iter(INDEX_DEFINITIONS))

        # Index existence check returns True, reindex query returns None
        mock_exec = mocker.patch(
            'backend.jobs.tasks.indexes.execute_psql_query', side_effect=[True, None]
        )

        await update_index(conn, index_name, reindex=True)

        # Get info for second execute_psql_query call
        second_psql_call = mock_exec.call_args_list[1]
        second_call_query = second_psql_call.args[1].as_string()

        # Check for REINDEX in sql query
        assert 'REINDEX' in second_call_query
        assert index_name in second_call_query
        # Check that conn.commit is called
        conn.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skip_existing(self, mock_conn, mocker):
        conn, _ = mock_conn
        conn.commit = AsyncMock()

        # Get name of real index
        good_index_name = next(iter(INDEX_DEFINITIONS))

        # Index existence check returns true, reindex query returns None
        mock_exec = mocker.patch(
            'backend.jobs.tasks.indexes.execute_psql_query', return_value=True)

        await update_index(conn, good_index_name, reindex=False)

        # Check that only one execute_psql_query was made (to check index existence)
        mock_exec.assert_awaited_once()
        # Check that function returns without commit
        conn.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_index(self, mock_conn, mocker):
        conn, _ = mock_conn
        conn.commit = AsyncMock()

        # Get name of real index
        index_name = next(iter(INDEX_DEFINITIONS))

        # Index existence check returns None, create query reutrns None
        mock_exec = mocker.patch(
            'backend.jobs.tasks.indexes.execute_psql_query', side_effect=[None, None]
        )

        await update_index(conn, index_name)

        # Get info for second execute_psql_query call
        second_psql_call = mock_exec.call_args_list[1]
        second_call_query = second_psql_call.args[1]

        assert second_call_query == INDEX_DEFINITIONS[index_name].create_sql()
        conn.commit.assert_awaited_once()
