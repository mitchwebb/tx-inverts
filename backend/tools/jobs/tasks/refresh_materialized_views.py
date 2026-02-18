from backend.db_schema.index_definitions import MATERIALIZED_VIEWS
from backend.core.logging import db_logger
from psycopg import sql, AsyncConnection


async def check_for_mat_view(conn: AsyncConnection, view_name: str) -> bool:
    view_def = MATERIALIZED_VIEWS.get(view_name)
    if not view_def:
        raise ValueError(f'Definition for "{view_name}" not found.')

    check_sql = "SELECT 1 FROM pg_matviews WHERE matviewname = %s"

    async with conn.cursor() as cur:
        await cur.execute(check_sql, (view_name,))
        row = await cur.fetchone()

    return row is not None


async def refresh_materialized_view(
    conn: AsyncConnection,
    view_name
):
    view_exists = await check_for_mat_view(conn, view_name)
    async with conn.cursor() as cur:
        if not view_exists:
            view_def = MATERIALIZED_VIEWS.get(view_name)
            db_logger.info(
                f'Materialized view {view_name} not yet created, creating now...')
            await cur.execute(view_def['create_sql'])
        else:
            db_logger.info(
                f'Materialized view {view_name} already created, refreshing...')
            await cur.execute(
                sql.SQL('REFRESH MATERIALIZED VIEW {}').format(
                    sql.Identifier(view_name))
            )

    db_logger.info(f'{view_name} refreshed.')


async def refresh_materialized_views(conn):
    db_logger.info('Refreshing materialized views...')

    for view_name in MATERIALIZED_VIEWS:
        await refresh_materialized_view(conn, view_name)

    db_logger.info('Refresh complete.')
