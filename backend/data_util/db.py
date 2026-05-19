import psycopg
from backend.config import get_settings


async def get_single_db_connection():
    """
    Get database conn using current environment settings
    """
    settings = get_settings()
    db_settings = settings.database

    conn = await psycopg.AsyncConnection.connect(
        user=db_settings.user,
        password=db_settings.password,
        dbname=db_settings.name,
        host=db_settings.host,
        port=db_settings.port
    )
    return conn
