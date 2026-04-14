from backend.db_schema.index_definitions import INDEX_DEFINITIONS
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

    table_name = index_def['table']
    create_sql = index_def['create_sql']

    async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        # Check if index exists
        await cur.execute(
            '''
            SELECT 1 FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            ''',
            (table_name, index_name)
        )
        exists = await cur.fetchone()

        # If index exists and reindex == True, reindex
        if exists:
            if reindex:
                db_logger.info(f'{index_name} already exists, reindexing...')
                await cur.execute(
                    sql.SQL('REINDEX INDEX {}').format(
                        sql.Identifier(index_name))
                )
            # If index exists and reindex == False, skip
            else:
                db_logger.info(f'{index_name} already exists, skipping...')
                return
        # Else run create_index_query (if provided)
        else:
            db_logger.info(
                f'{index_name} does not yet exist, creating index...')
            await cur.execute(create_sql)
        
    await conn.commit()
    return


async def update_indexes(
    conn: psycopg.AsyncConnection,
    reindex: bool = False
):

    for index_name in INDEX_DEFINITIONS.keys():
        await update_index(
            conn,
            index_name,
            reindex
        )

    return
