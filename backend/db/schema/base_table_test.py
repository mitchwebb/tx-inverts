import pytest

from backend.db.schema.base_table import DBTable
import pandas as pd
import datetime


@pytest.fixture
def mock_table():
    class MockTable(DBTable):
        name = 'test_table'
        columns = {'userId': 'BIGINT', 'userName': 'TEXT', 'userPIN': 'INTEGER'}
        primary_key = 'userId'
    return MockTable()


class TestBaseTable:
    def test_table_needs_args(self):
        class InvalidTable(DBTable):
            pass
        with pytest.raises(NotImplementedError):
            InvalidTable()

    # Test table creation sql method
    # This is somewhat brittle, but I don't this structure should change
    def test_create_table_query(self, mock_table):
        query = mock_table.create_table_query()
        assert query.as_string(
        ) == '''CREATE TABLE IF NOT EXISTS "test_table" ("user_id" BIGINT, "user_name" TEXT, "user_pin" INTEGER);'''

    def test_drop_table_query(self, mock_table):
        query = mock_table.drop_table_query()
        assert query.as_string(
        ) == '''DROP TABLE IF EXISTS "test_table"'''

    # Verify .column_order() returns columns in original order, converted to snake_case
    def test_column_order(self, mock_table):
        column_order = mock_table.column_order()
        assert column_order == ['user_id', 'user_name', 'user_pin']

    # Verify that, given a df with extra columns, coerce_dataframe will remove extra columns (while keeping others)
    def test_coerce_dataframe_removes_extra_column(self, mock_table):
        test_df = pd.DataFrame(
            {'userId': [1], 'userName': ['Test'], 'userDOB': [datetime.date.today()]})

        coerced = mock_table.coerce_dataframe(test_df)

        assert 'user_dob' not in coerced.columns

    # Verify that, when missing columns, coerce_dataframe adds missing columns with None values
    def test_coerce_dataframe_adds_missing_column(self, mock_table):
        test_df = pd.DataFrame({'userId': [1]})

        coerced = mock_table.coerce_dataframe(test_df)

        assert 'user_name' in coerced.columns
        assert coerced['user_name'].iloc[0] == None
        assert 'user_pin' in coerced.columns
        # INTEGER uses NA
        assert pd.isna(coerced['user_pin'].iloc[0])

    def test_dataframe_type_mapping(self, mock_table):
        test_df = pd.DataFrame({'userId': [1], 'userName': ['Test']})
        coerced = mock_table.coerce_dataframe(test_df)

        assert coerced['user_id'].dtype == pd.Int64Dtype()
        assert coerced['user_pin'].dtype == pd.Int32Dtype()
