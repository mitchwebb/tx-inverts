from backend.db_schema.index_definitions import MATERIALIZED_VIEWS, VIEWS
from backend.core.logging import db_logger
from psycopg import sql, AsyncConnection


async def check_for_mat_view(conn: AsyncConnection, view_name: str) -> bool:
    check_sql = "SELECT 1 FROM pg_matviews WHERE matviewname = %s"

    async with conn.cursor() as cur:
        await cur.execute(check_sql, (view_name,))
        row = await cur.fetchone()

    return row is not None


# Refresh (or create) materialized view
async def refresh_materialized_view(
    conn: AsyncConnection,
    view_name
):

    view_def = VIEWS.get(view_name)
    if not view_def:
        raise ValueError(f'Definition for "{view_name}" not found.')

    # Check to see if the view exists
    view_exists = await check_for_mat_view(conn, view_name)

    async with conn.cursor() as cur:
        # In not, create
        if not view_exists:
            db_logger.info(
                f'{view_name} not yet created, creating now...')
            await cur.execute(view_def['create_sql'])
        # Else, refresh
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


async def create_view(conn, view_name: str):
    async with conn.cursor() as cur:
        view_def = VIEWS.get(view_name)
        if not view_def:
            raise ValueError(f'Definition for "{view_name}" not found.')
        db_logger.info(
            f'{view_name} not yet created, creating now...')
        await cur.execute(view_def['create_sql'])

    db_logger.info(f'{view_name} created')
