from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import AsyncConnection, sql
from psycopg.errors import Error as PsycopgError
from backend.db.schema import ALL_TABLES
from backend.db.schema.base import DBTable
from backend.jobs.tasks.database import update_indexes
from backend.core.logging import db_logger
from backend.jobs.tasks.views import refresh_materialized_views


# Check if table already exists (for readable erroring)
async def table_exists(conn: AsyncConnection, table_name: str) -> bool:
    exists_query = sql.SQL("""
        SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = {table_name}
        )
    """).format(table_name=sql.Literal(table_name))
    result = await execute_psql_query(conn, exists_query, fetch='one')
    return result[0] if result else False


async def initialize_table(conn, table: DBTable, verbose: bool = False, strict: bool = True):
    try:
        if await table_exists(conn, table.name):
            if verbose:
                db_logger.info(
                    f"Table '{table.name}' already exists. Skipping.")
            return

        create_sql = table.create_table_query()
        await execute_psql_query(conn, create_sql)
        if verbose:
            db_logger.info(f'Created table: {table.name}')

    except PsycopgError as e:
        error_msg = getattr(e, "pgerror", str(e))
        db_logger.error(f"Failed to create table '{table.name}': {error_msg}")
        if strict:
            raise
    except Exception as e:
        db_logger.exception(
            f"Unexpected error initializing '{table.name}': {str(e)}")
        if strict:
            raise

    finally:
        await conn.commit()


# Initialize all tables provided to ALL_TABLES constant
async def initialize_all_tables(conn: AsyncConnection, *, verbose: bool = False, strict: bool = True):
    for table in ALL_TABLES:
        await initialize_table(conn, table, verbose, strict)

    await refresh_materialized_views(conn)
    await update_indexes(conn)
