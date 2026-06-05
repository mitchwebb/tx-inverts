from typing import LiteralString, NamedTuple
import pandas as pd
from psycopg import sql
from backend.data_util.case import to_snake_case
from backend.core.logging import data_logger


class SQLTypeMapping(NamedTuple):
    pandas_dtype: str
    needs_numeric_coercion: bool


# Map from SQL type to pandas type, with boolean to indicate numeric conversion
SQL_TYPE_MAP = {
    'BIGINT': SQLTypeMapping('Int64', True),
    'INTEGER': SQLTypeMapping('Int32', True),
    'SMALLINT': SQLTypeMapping('Int16', True),
    'DOUBLE PRECISION': SQLTypeMapping('float64', True),
    'FLOAT': SQLTypeMapping('float64', True),
    'REAL': SQLTypeMapping('float32', True),
    'NUMERIC': SQLTypeMapping('float64', True),
    'DECIMAL': SQLTypeMapping('float64', True),
    'BOOLEAN': SQLTypeMapping('boolean', False),
    'TEXT': SQLTypeMapping('object', False),
    'VARCHAR': SQLTypeMapping('object', False),
    'CHAR': SQLTypeMapping('object', False),
    'DATE': SQLTypeMapping('object', False),
    'TIMESTAMP': SQLTypeMapping('object', False),
    'TIMESTAMPTZ': SQLTypeMapping('object', False),
    'GEOMETRY': SQLTypeMapping('object', False),
}


class DBTable:
    """Abstract base class for table definitions"""
    name: str
    columns: dict[str, LiteralString]
    primary_key: str | None = None  # This assumes a single primary key!

    def __init__(self):
        if not self.name or not self.columns:
            raise NotImplementedError(
                'Subclasses must define name and columns')

    # Get create table statement
    def create_table_query(self) -> sql.Composed:
        """Get create table statement for table using snake_case column names"""
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
    def drop_table_query(self) -> sql.Composed:
        return sql.SQL(
            "DROP TABLE IF EXISTS {table_name}"
        ).format(table_name=sql.Identifier(self.name))

    # Get list of columns in snake_case
    def column_order(self) -> list[str]:
        """Get list of columns in snake_case in their defined order."""
        return [to_snake_case(col) for col in self.columns]

    def coerce_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
            Renames columns to snake_case
            Drops unexpected columns
            Validates that required columns exist
        """
        df = df.rename(columns={col: to_snake_case(col) for col in df.columns})

        # Get list of columns from column_order method
        allowed_cols = set(self.column_order())
        # Get list of columns in provided df
        actual_cols = set(df.columns)
        # Get lists of extra and missing column names
        extra = actual_cols - allowed_cols
        missing = allowed_cols - actual_cols

        # Remove unwanted columns
        if extra:
            data_logger.info(f'Removing unwanted columns...')
            df = df[[col for col in df.columns if col in allowed_cols]]

        # Add missing columns
        if missing:
            data_logger.info(f'Adding empty missing columns to df: {missing}')
            for col in missing:
                df[col] = None

        # Coerce numeric columns to appropriate nullable pandas types
        for col_name, col_type in self.columns.items():
            col_name = to_snake_case(col_name)
            if col_name not in df.columns:
                continue
            for sql_type, mapping in SQL_TYPE_MAP.items():
                if sql_type in col_type:
                    if mapping.needs_numeric_coercion:
                        df[col_name] = pd.to_numeric(
                            df[col_name], errors='coerce')
                    # SQL_TYPE_MAP ensures that this is safe (even with the ignore)
                    df[col_name] = df[col_name].astype(
                        mapping.pandas_dtype)  # type: ignore[arg-type]
                    break

        self.validate_columns(df)

        # Reorder columns to match table definition (for copying)
        df = df[self.column_order()]

        return df

    def validate_columns(self, df: pd.DataFrame):
        """
        Ensure DataFrame has all required columns
        """
        expected = set(self.column_order())
        actual = set(df.columns)

        missing = expected - actual
        extra = actual - expected

        if missing:
            raise ValueError(f'df is missing expected columns: {missing}')
        if extra:
            raise ValueError(f'df has unexpected columns: {extra}')
