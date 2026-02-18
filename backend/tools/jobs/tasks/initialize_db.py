from psycopg import Connection
from psycopg.errors import Error as PsycopgError
from backend.db_schema import ALL_TABLES
from backend.db_schema.base import DBTable
from backend.tools.jobs.tasks.database import update_indexes
from backend.core.logging import db_logger

# Check if table already exists (for readable erroring)
async def table_exists(conn: Connection, table_name: str) -> bool:
    async with conn.cursor() as cur:
        await cur.execute('''
                SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                )
        ''', (table_name,))
        row = await cur.fetchone()
        return row[0] if row else False
    
async def initialize_table(conn, table: DBTable, verbose: bool = False, strict: bool = True):
    try:
        if await table_exists(conn, table.name):
            if verbose:
                db_logger.info(f"Table '{table.name}' already exists. Skipping.")
            return
            
        create_sql = table.create_table_query()
        async with conn.cursor() as cur:
            await cur.execute(create_sql)
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
async def initialize_all_tables(conn: Connection, *, verbose: bool = False, strict: bool = True):
    for table in ALL_TABLES:
        await initialize_table(conn, table, verbose, strict)

    await update_indexes(conn)
