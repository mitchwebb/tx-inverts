from unittest.mock import AsyncMock

import pytest
from backend.db.schema import ALL_TABLES
from backend.jobs.tasks.tables import initialize_table, table_exists


# initialize_table tests
class TestInitializeTable:
    @pytest.mark.asyncio
    async def test_skip_existing_table(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.tables.table_exists',
                     return_value=True)
        mock_exec = mocker.patch('backend.jobs.tasks.tables.execute_psql_query')

        await initialize_table(conn, ALL_TABLES[0])
        # Make sure execute_psql_query never runs (early return)
        mock_exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_table(self, mock_conn, mocker):
        conn, _ = mock_conn
        conn.commit = AsyncMock()
        mocker.patch('backend.jobs.tasks.tables.table_exists',
                     return_value=False)
        mock_exec = mocker.patch('backend.jobs.tasks.tables.execute_psql_query')

        table = ALL_TABLES[0]

        await initialize_table(conn, table)

        mock_exec.assert_awaited_once()
        assert mock_exec.call_args_list[0].args[1] == table.create_table_query()


# Simple tests for table_exists return values
class TestTableExists:
    @pytest.mark.asyncio
    async def test_table_exists_return(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.tables.execute_psql_query',
                     return_value=[True])

        result = await table_exists(conn, table_name='test')
        assert result == True

    @pytest.mark.asyncio
    async def test_table_not_exists_return(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.tables.execute_psql_query',
                     return_value=None)

        result = await table_exists(conn, table_name='test')
        assert result == False
