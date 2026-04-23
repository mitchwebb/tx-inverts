import time

from backend.data_util.gbif.gbif_api import gbif_keyed_api_request
from backend.data_util.gbif.observations_request import APPROVED_DATASETS
from backend.db_schema.gbif_dataset_metadata import GBIF_DATASET_META
from psycopg import AsyncConnection, sql


async def fill_dataset_table(conn: AsyncConnection):
    for dataset_key in APPROVED_DATASETS:
        dataset_info = await gbif_keyed_api_request(endpoint='dataset', key=dataset_key)

        # INSERT dataset title into gbif_dataset_metadata
        dataset_title = dataset_info['title']

        async with conn.cursor() as cur:
            await cur.execute(sql.SQL('''
                INSERT INTO {dataset_table} (dataset_key, dataset_title)
                VALUES ({dataset_key}, {dataset_title})
                ON CONFLICT (dataset_key) DO UPDATE SET dataset_title = EXCLUDED.dataset_title
            ''').format(
                dataset_table=sql.Identifier(GBIF_DATASET_META.name),
                dataset_key=sql.Literal(dataset_key),
                dataset_title=sql.Literal(dataset_title)
            ))

        time.sleep(0.1)  # be polite to the API

    await conn.commit()
