import io
import pandas as pd
import uuid

from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import AsyncConnection, sql
from backend.data_util.case import to_snake_case
from backend.core.logging import db_logger, data_logger


class DBTable:
    '''Abstract base class for table definitions.'''
    name: str = ''
    primary_key: str | None = None  # This assumes a single primary key!
    columns: dict[str, str] = {}

    def __init__(self):
        if not self.name or not self.columns:
            raise NotImplementedError(
                'Subclasses must define name and columns')

    def preprocess_df(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Override in subclasses to fix/transform df before validation and copy.'''
        return df

    # Get create table statement
    def create_table_query(self) -> str:
        '''Get create table statement for table using snake_case column names'''
        # Generate list of columns (in snake_case) and types
        columns = [
            sql.SQL('{column} {type}').format(
                column=sql.Identifier(to_snake_case(col)),
                type=sql.SQL(dtype)
            ) for col, dtype in self.columns.items()
        ]

        # Plug column list into creation statement
        create_sql = sql.SQL(
            "CREATE TABLE IF NOT EXISTS {table_name} ({column_list});"
        ).format(
            table_name=sql.Identifier(self.name),
            column_list=sql.SQL(', ').join(columns)
        )
        return create_sql

    # Get drop table statement
    def drop_table_query(self) -> str:
        return sql.SQL(
            "DROP TABLE IF EXISTS {table_name}"
        ).format(table_name=sql.Identifier(self.name))

    # Get list of columns in snake_case
    def column_order(self) -> list[str]:
        '''Get list of columns in snake_case, in the defined order.'''
        return [to_snake_case(col) for col in self.columns]

    def coerce_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
            Renames columns to snake_case
            Drops unexpected columns
            Validates that required columns exist
        """
        df = df.rename(columns={col: to_snake_case(col) for col in df.columns})

        allowed_cols = set(self.column_order())
        actual_cols = set(df.columns)
        extra = actual_cols - allowed_cols
        missing = allowed_cols - actual_cols

        if extra:
            data_logger.info(f'Removing unwanted columns...')
            df = df[[col for col in df.columns if col in allowed_cols]]

        if missing:
            data_logger.info(f'Adding empty missing columns to df: {missing}')
            for col in missing:
                df[col] = None

        # TODO: This should be made more flexible
        # Fix int columns to use nullable pandas Int64 dtype
        bigint_columns = [
            col_name for col_name, col_type in self.columns.items() if "BIGINT" in col_type
        ]

        for column in bigint_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column], errors='coerce').astype('Int64')

        self.validate_columns(df)

        # Reorder columns to match table definition (for copying)
        df = df[self.column_order()]

        return df

    def validate_columns(self, df: pd.DataFrame):
        '''Ensure DataFrame has all required columns.'''
        expected = set(self.column_order())
        actual = {to_snake_case(col) for col in df.columns}

        missing = expected - actual
        extra = actual - expected

        if missing:
            raise ValueError(f'df is missing expected columns: {missing}')
        if extra:
            raise ValueError(f'df has unexpected columns: {extra}')
