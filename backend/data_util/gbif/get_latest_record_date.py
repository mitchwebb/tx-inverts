from datetime import date
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import AsyncConnection, sql
from typing import Literal


async def get_latest_record_date(conn: AsyncConnection, param: Literal['last_interpreted', 'modified']) -> date | None:
    """
    Get the most recent 'last_interpreted' or 'modified' datetime from gbif_observations

    Args:
        conn (AsyncConnection): psycopg connection
        param (Literal['last_interpreted', 'modified']): column to check

    Returns:
        datetime | None: the latest date, or None if no data (or unreasonable date)
    """

    query = sql.SQL("""
        SELECT MAX({param}) FROM gbif_observations
    """).format(param=sql.Identifier(param))

    result = await execute_psql_query(conn, query, fetch='one')

    if result and result[0]:
        latest_date = result[0].date()
        today = date.today()

        return latest_date if latest_date <= today else None

    return None
