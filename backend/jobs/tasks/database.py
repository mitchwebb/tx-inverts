from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.index_definitions import INDEX_DEFINITIONS
from backend.core.logging import db_logger
import psycopg
from psycopg import sql


async def update_index(
    conn: psycopg.AsyncConnection,
    index_name: str,
    reindex: bool = False,
):
    index_def = INDEX_DEFINITIONS.get(index_name)
    if not index_def:
        raise ValueError(f"Index definition for '{index_name}' not found.")

    table_name = index_def.table.name
    create_sql = index_def.create_sql()

    # Check if index exists
    exists_query = sql.SQL("""
        SELECT 1 FROM pg_indexes
        WHERE tablename = {table_name} AND indexname = {index_name}
    """).format(
        table_name=sql.Literal(table_name),
        index_name=sql.Literal(index_name)
    )
    exists = await execute_psql_query(conn, exists_query, fetch='one')

    # If index exists and reindex == True, reindex
    if exists:
        if reindex:
            db_logger.info(f'{index_name} already exists, reindexing...')
            reindex_query = sql.SQL('REINDEX INDEX {index_name}').format(
                index_name=sql.Identifier(index_name)
            )
            await execute_psql_query(conn, reindex_query)

        # If index exists and reindex == False, skip
        else:
            db_logger.info(f'{index_name} already exists, skipping...')
            return
    # Else run create_index_query (if provided)
    else:
        db_logger.info(
            f'{index_name} does not yet exist, creating index...')
        await execute_psql_query(conn, create_sql)

    await conn.commit()


async def update_indexes(conn: psycopg.AsyncConnection, reindex: bool = False):
    for index_name in INDEX_DEFINITIONS.keys():
        await update_index(conn, index_name, reindex)
    db_logger.info(f'Finished updating {len(INDEX_DEFINITIONS)} indexes.')
