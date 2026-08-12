from unittest.mock import AsyncMock

import pytest
from psycopg import sql
from backend.db.schema import ALL_TABLES
from backend.jobs.tasks.table_tasks import initialize_table, table_exists, truncate_table
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.geometries import TEXAS_GEOMETRY_TABLE


# initialize_table tests
class TestInitializeTable:
    @pytest.mark.asyncio
    async def test_skip_existing_table(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.table_tasks.table_exists',
                     return_value=True)
        mock_exec = mocker.patch(
            'backend.jobs.tasks.table_tasks.execute_psql_query')

        await initialize_table(conn, ALL_TABLES[0])
        # Make sure execute_psql_query never runs (early return)
        mock_exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_table(self, mock_conn, mocker):
        conn, _ = mock_conn
        conn.commit = AsyncMock()
        mocker.patch('backend.jobs.tasks.table_tasks.table_exists',
                     return_value=False)
        mock_exec = mocker.patch(
            'backend.jobs.tasks.table_tasks.execute_psql_query')

        table = ALL_TABLES[0]

        await initialize_table(conn, table)

        mock_exec.assert_awaited_once()
        assert mock_exec.call_args_list[0].args[1] == table.create_table_query()


# Simple tests for table_exists return values
class TestTableExists:
    @pytest.mark.asyncio
    async def test_table_exists_return(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.table_tasks.execute_psql_query',
                     return_value=[True])

        result = await table_exists(conn, table_name='test')
        assert result == True

    @pytest.mark.asyncio
    async def test_table_not_exists_return(self, mock_conn, mocker):
        conn, _ = mock_conn
        mocker.patch('backend.jobs.tasks.table_tasks.execute_psql_query',
                     return_value=None)

        result = await table_exists(conn, table_name='test')
        assert result == False


class TestTruncateTable:
    async def test_missing_table_warns(self, conn):
        """Test that requesting to truncate a table that does not exist raises an informative ValueError"""
        with pytest.raises(ValueError, match='does not exist'):
            await truncate_table(conn, 'missing_table')

    async def test_existing_table_truncates(self, conn, tx_bounding_box):
        """Test that requesting to truncate an existing table succeeds"""

        select_query = sql.SQL(
            "SELECT * FROM {tx_geom}").format(
            tx_geom=sql.Identifier(TEXAS_GEOMETRY_TABLE.name)
        )

        # Make sure table has contents
        before = await execute_psql_query(
            conn,
            select_query,
            fetch='one'
        )
        assert before is not None
        assert before[0] is not None

        await truncate_table(conn, TEXAS_GEOMETRY_TABLE.name)
        # Make sure table is empty
        after = await execute_psql_query(
            conn,
            select_query,
            fetch='one'
        )
        assert after is None
