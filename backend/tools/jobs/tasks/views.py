from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.index_definitions import MATERIALIZED_VIEWS
from backend.core.logging import db_logger
from psycopg import sql, AsyncConnection


async def check_for_mat_view(conn: AsyncConnection, view_name: str) -> bool:
    check_sql = sql.SQL("SELECT 1 FROM pg_matviews WHERE matviewname = {view_name}").format(
        view_name=sql.Literal(view_name))

    row = await execute_psql_query(conn, check_sql, fetch='one')

    return row is not None


# Refresh (or create) materialized view
async def refresh_materialized_view(
    conn: AsyncConnection,
    view_name
):

    view_def = MATERIALIZED_VIEWS.get(view_name)
    if not view_def:
        raise ValueError(f'Definition for "{view_name}" not found.')

    # Check to see if the view exists
    view_exists = await check_for_mat_view(conn, view_name)

    # If not, create
    if not view_exists:
        db_logger.info(
            f'{view_name} not yet created, creating now...')
        await execute_psql_query(conn, view_def['create_sql'])
        db_logger.info(f'{view_name} created.')
        # Else, refresh
    else:
        db_logger.info(
            f'Materialized view {view_name} already created, refreshing...')

        refresh_statement = sql.SQL('REFRESH MATERIALIZED VIEW {}').format(
            sql.Identifier(view_name))

        await execute_psql_query(conn, refresh_statement)
        db_logger.info(f'{view_name} refreshed.')

    await conn.commit()


async def refresh_materialized_views(conn):
    db_logger.info('Refreshing materialized views...')

    for view_name in MATERIALIZED_VIEWS:
        await refresh_materialized_view(conn, view_name)

    db_logger.info('Refresh complete.')
