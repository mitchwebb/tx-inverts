from psycopg import AsyncConnection, sql
from typing import Literal
from dateutil import parser


async def get_latest_record_date(conn: AsyncConnection, param: Literal['last_interpreted', 'modified']):
    """
    Get the most recent 'last_interpreted' or 'modified' datetime from gbif_observations

    Args:
        conn (AsyncConnection): psycopg connection
        param (Literal['last_interpreted', 'modified']): column to check

    Returns:
        datetime | None: the latest date, or None if no data
    """

    async with conn.cursor() as cur:
        query = sql.SQL('''
            SELECT MAX({param}) FROM gbif_observations
        ''').format(param=sql.Identifier(param))

        await cur.execute(query)
        result = await cur.fetchone()

        if result and result[0]:
            # DB column is text; parse ISO string into a date
            dt = parser.isoparse(result[0])
            return dt.date()

        return None
