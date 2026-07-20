import asyncio
from typing import List
from backend.core.logging import api_logger
from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.gbif.observations_request import APPROVED_DATASETS
from backend.data_util.requests import fetch_data
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from psycopg import AsyncConnection, sql
import aiohttp


# TODO: Would it be wiser to grab these dynamically using the datasets present in gbif_observations? Only if we think we'll ingest outside sources.
async def fill_dataset_table(conn: AsyncConnection, dataset_ids: List[str]):
    async with aiohttp.ClientSession() as session:
        for dataset_key in dataset_ids:
            dataset_info = await fetch_data(
                session, f'https://api.gbif.org/v1/dataset/{dataset_key}')

            # If no dataset info is found, log, but continue
            if dataset_info is None:
                api_logger.warning(
                    f'Dataset info not found for dataset key "{dataset_key}"')
                continue
            # INSERT dataset title into gbif_dataset_metadata
            dataset_title = dataset_info['title']

            insert_query = sql.SQL("""
                INSERT INTO {dataset_table} (dataset_key, dataset_title)
                VALUES ({dataset_key}, {dataset_title})
                ON CONFLICT (dataset_key) DO UPDATE SET dataset_title = EXCLUDED.dataset_title
            """).format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                dataset_key=sql.Literal(dataset_key),
                dataset_title=sql.Literal(dataset_title)
            )
            await execute_psql_query(conn, insert_query)

            await asyncio.sleep(0.1)  # be polite to the API

    await conn.commit()
