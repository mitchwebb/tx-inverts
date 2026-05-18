import json
import os
import csv
import pandas as pd
from backend.config import get_settings
from backend.constants.paths import DATA_OUT_PATH
from backend.data_util.gbif.gbif_downloads import gbif_download_request, get_gbif_download
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE


async def get_invasives_dataset():
    # Global Register of Introduced and Invasive Species - United States
    dataset_key = '32ad19ed-6b89-447a-9242-795c0897f345'

    settings = get_settings()

    # Request a GBIF download
    request_body = {
        "creator": settings.gbif.user,
        "notificationAddresses": [
            settings.gbif.email
        ],
        "format": "dwca",
        "sendNotification": "true",
        "predicate": {
            "type": "equals",
            "key": "DATASET_KEY",
            "value": dataset_key,
            "matchCase": "false"
        }
    }

    key = gbif_download_request(
        request_body=json.dumps(request_body),
        pwd=settings.gbif.password,
        username=settings.gbif.user
    )

    output_dir = await get_gbif_download(key, output_fp=DATA_OUT_PATH, target_files=['occurrence.txt'])

    observations_fp = os.path.join(output_dir, 'occurrence.txt')

    return observations_fp


async def prep_invasives_dataset(fp):
    df = pd.read_csv(
        os.path.join(fp),
        delimiter='\t',
        quoting=csv.QUOTE_NONE,
        on_bad_lines='warn',
        low_memory=False,
        header=0
    )

    df['taxonID'] = df['taxonKey']

    def filter_invasive_chordates(df):
        mask = (
            (df['kingdom'] == 'Animalia') &
            (
                (df['phylum'] != 'Chordata') |
                (df['class'].isin(
                    ['Ascidiacea', 'Leptocardii', 'Appendicularia', 'Thaliacea']))
            )
        )

        filtered_df = df.loc[mask]

        return filtered_df

    filtered_df = filter_invasive_chordates(df)

    df = US_INVASIVES_TABLE.coerce_dataframe(filtered_df)
    US_INVASIVES_TABLE.validate_columns(df)

    return filtered_df
