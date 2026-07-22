from datetime import datetime, date
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import AsyncConnection, sql
from typing import Literal

from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE


async def get_latest_record_date(conn: AsyncConnection, param: Literal['last_interpreted', 'modified']) -> date | None:
    """
    Get the most recent 'last_interpreted' or 'modified' datetime from gbif_observations

    Args:
        conn (AsyncConnection): psycopg connection
        param (Literal['last_interpreted', 'modified']): column to check

    Returns:
        datetime | None: the latest date, or None if no data (or unreasonable date)
    """

    now = datetime.now()

    query = sql.SQL("""
        SELECT MAX({param}) FROM {observations_table}
        WHERE {param} <= {now}
    """).format(
        param=sql.Identifier(param),
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        now=sql.Literal(now.isoformat())
    )

    result = await execute_psql_query(conn, query, fetch='one')

    if result and result[0]:
        latest = result[0]
        latest_date = latest.date() if isinstance(latest, datetime) else latest

        return latest_date if latest_date <= now.date() else None

    return None
