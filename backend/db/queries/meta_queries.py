from psycopg import AsyncConnection, sql

from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.dataset_versions import DATA_VERSIONS_TABLE
from backend.core.logging import db_logger


### NOTE: ###
# All matview names are useable for this functions, along with the two
# DATASET keys below. The matviews will automatically log their last_updated_at
# time when they're refreshed, and the 'observations' and 'backbone' datasets should
# be updated when their corresponding data is pulled.

OBSERVATIONS_DATASET = 'observations'
BACKBONE_DATASET = 'backbone'


async def store_doi(conn: AsyncConnection, dataset_name: str, doi: str | None):
    """
    Store a provided DOI associated with a provided dataset_name and 
    current timestamp to the DATA_VERSIONS_TABLE
    """

    try:
        doi_query = sql.SQL("""
            INSERT INTO {dataset_versions} (dataset_name, last_updated_at, doi)
            VALUES ({dataset_name}, CURRENT_TIMESTAMP, {doi})
            ON CONFLICT (dataset_name) DO UPDATE
            SET
                doi = EXCLUDED.doi,
                last_updated_at = EXCLUDED.last_updated_at
        """).format(
            dataset_name=sql.Literal(dataset_name),
            dataset_versions=sql.Identifier(DATA_VERSIONS_TABLE.name),
            doi=sql.Literal(doi)
        )

        await execute_psql_query(conn, doi_query)
    except Exception:
        db_logger.error("Failed to store DOI")
        raise


async def stamp_dataset_updated(conn: AsyncConnection, dataset_name: str):
    """
    Add dataset with last_updated_at value to dataset_versions (or update)
    Does not include DOI
    """

    try:
        stamp_sql = sql.SQL("""
            INSERT INTO {dataset_versions} (dataset_name, last_updated_at)
            VALUES ({dataset_name}, CURRENT_TIMESTAMP)
            ON CONFLICT (dataset_name) DO UPDATE
                SET last_updated_at = EXCLUDED.last_updated_at
        """).format(
            dataset_versions=sql.Identifier(DATA_VERSIONS_TABLE.name),
            dataset_name=sql.Literal(dataset_name),
        )
        await execute_psql_query(conn, stamp_sql)
        db_logger.info(f"Stamped last_updated_at for {dataset_name}", )

    except Exception:
        db_logger.error(f"Failed to stamp last_updated_at for {dataset_name}")
        raise


async def retrieve_dataset_meta(conn: AsyncConnection, dataset_name: str):
    try:
        query = sql.SQL("""
            SELECT * FROM {dataset_versions}
            WHERE dataset_name = {dataset_name}
        """).format(
            dataset_name=sql.Literal(dataset_name),
            dataset_versions=sql.Identifier(DATA_VERSIONS_TABLE.name),
        )

        result = await execute_psql_query(conn, query, fetch='one', dict_cursor=True)
        return result
    except Exception:
        db_logger.error(f"Failed to retrieve dataset_meta for {dataset_name}")
        raise
