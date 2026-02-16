import re
import io
from typing import Dict
import pandas as pd
import uuid
from psycopg import AsyncConnection, sql
from backend.data_util.case import to_snake_case


class DBTable:
    '''Abstract base class for table definitions.'''
    name: str = ''
    primary_key: str | None = None  # This assumes a single primary key!
    columns: dict[str, str] = {}
    raw_column_map: dict[str, str] = {}

    # Verify that the column mapping provided satisfies the columns provided
    @classmethod
    def get_column_mapping(cls) -> Dict[str, str]:
        """Return RAW → table mapping, verifying table coverage."""

        if not cls.raw_column_map:
            # No raw mapping defined — safe for derived tables that don't ingest raw data
            return {}

        missing: list[str] = [
            v for v in cls.raw_column_map.values() if v not in cls.columns]
        if missing:
            raise ValueError(
                f"raw_column_map maps to undefined columns: {missing}")
        return cls.raw_column_map

    def __init__(self):
        if not self.name or not self.columns:
            raise NotImplementedError(
                'Subclasses must define name and columns')

    def preprocess_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Override in subclasses to fix/transform df before validation and copy."""
        return df

    def create_table_query(self) -> str:
        columns = [
            sql.SQL('{} {}').format(sql.Identifier(
                to_snake_case(col)), sql.SQL(dtype))
            for col, dtype in self.columns.items()
        ]
        create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
            sql.Identifier(self.name),
            sql.SQL(', ').join(columns)
        )
        return create_sql

    def drop_table_query(self) -> str:
        return sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(self.name))

    def column_order(self) -> list[str]:
        '''Get list of columns in snake_case, in the defined order.'''
        return [to_snake_case(col) for col in self.columns]

    async def copy_from_df(
        self,
        conn: AsyncConnection,
        df: pd.DataFrame,
        drop_table: bool = False,
        create_if_not_exists: bool = False,
        overwrite_rows: bool = False,
        chunk_size: int = 10000
    ) -> None:
        '''Copy DataFrame into the table using PostgreSQL COPY.

        Args:
            conn (AsyncConnection): psycopg AsyncConnection
            df (pd.DataFrame): pandas DataFrame with data
            drop_table (bool): If True, drop the existing table before copying
            create_if_not_exists (bool): If True, create the table before copying
            overwrite_rows (bool): If True, overwrite rows with duplicate pkey
            chunk_size: chunk size for reading in csv
        '''

    # Rename columns to snake_case before validation
        df = df.rename(columns={col: to_snake_case(col) for col in df.columns})

        # Validate or reorder columns before copy
        self.validate_columns(df)

        if drop_table:
            try:
                async with conn.cursor() as cur:
                    await cur.execute(self.drop_table_query())
                    await conn.commit()
                    print(f"Dropped '{self.name}'")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to drop table '{self.name}': {e}") from e

        if create_if_not_exists or drop_table:
            try:
                async with conn.cursor() as cur:
                    await cur.execute(self.create_table_query())
                    await conn.commit()
                    print(f"Created '{self.name}'")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create table '{self.name}': {e}") from e

        columns = self.column_order()
        df_to_copy = df[columns]
        buffer = io.StringIO()
        df_to_copy.to_csv(buffer, index=False, sep='\t',
                          encoding='utf-8', header=False, na_rep='\\N')

        # Quotes to help with reserved words
        columns_sql = sql.SQL(', ').join(sql.Identifier(col) for col in columns)

        # Shared column copy logic
        async def copy_buffer(cur, table_name, columns_sql, buffer, chunk_size):
            copy_sql = sql.SQL(
                "COPY {} ({}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
            ).format(
                sql.Identifier(table_name),
                columns_sql
            )
            buffer.seek(0)
            async with cur.copy(copy_sql) as copy:
                while (chunk := buffer.read(chunk_size)):
                    await copy.write(chunk)

        # Prepare and execute SQL
        async with conn.cursor() as cur:
            # Check if table has primary_key. If not, ignore overwrite
            pkey = self.primary_key
            if not pkey and overwrite_rows:
                print(
                    f"Warning: overwrite_rows=True ignored because no primary key is defined for table '{self.name}'"
                )
                overwrite_rows = False

            try:
                # If overwriting rows, we must create a temp table (COPY cannot handle errors)
                if overwrite_rows:
                    # Generate a temp table name
                    temp_table = f"_tmp_{self.name}_{uuid.uuid4().hex[:6]}"

                    # Create the temp table with same structure
                    create_tmp_sql = sql.SQL(
                        "CREATE TEMP TABLE {} (LIKE {} INCLUDING ALL);"
                    ).format(
                        sql.Identifier(temp_table),
                        sql.Identifier(self.name)
                    )
                    await cur.execute(create_tmp_sql)

                    # Chunk COPY into temp table
                    await copy_buffer(cur,
                                      temp_table,
                                      columns_sql,
                                      buffer,
                                      chunk_size)

                    assert pkey in columns, f"Primary key '{pkey}' not in table columns {columns}"

                    # ON CONFLICT clause
                    update_set_sql = sql.SQL(', ').join(
                        sql.SQL('{} = EXCLUDED.{}').format(
                            sql.Identifier(col),
                            sql.Identifier(col)
                        ) for col in columns if col != pkey
                    )

                    upsert_sql = sql.SQL('''
                        INSERT INTO {} ({})
                        SELECT {} FROM {}
                        ON CONFLICT ({}) DO UPDATE
                        SET {};
                    ''').format(
                        sql.Identifier(self.name),
                        columns_sql,
                        columns_sql,
                        sql.Identifier(temp_table),
                        sql.Identifier(pkey),
                        update_set_sql
                    )
                    await cur.execute(upsert_sql)
                else:
                    # Standard COPY into real table
                    await copy_buffer(cur,
                                      self.name,
                                      columns_sql,
                                      buffer,
                                      chunk_size)

                await conn.commit()
                print(f"Copied into '{self.name}'")
            except Exception as e:
                await conn.rollback()
                raise RuntimeError(
                    f"Failed to copy data into '{self.name}': {e}") from e

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
            print(f'Dropping unexpected columns: {extra}')
            df = df[[col for col in df.columns if col in allowed_cols]]

        if missing:
            print(f'Adding empty missing columns: {missing}')
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
