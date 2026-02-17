import json
import os
import csv
import requests
import pandas as pd

from backend.config.data import DATA_OUT_PATH, settings
from backend.data_util.gbif import gbif_downloads, observations_request
from backend.db_schema.us_invasives_checklist import US_INVASIVES_TABLE


def get_invasive_status(taxon_key, test=False):
    # Global Register of Introduced and Invasive Species - United States
    dataset_key = '32ad19ed-6b89-447a-9242-795c0897f345'

    # Construct the request URL
    url = f"https://api.gbif.org/v1/occurrence/count?datasetKey={dataset_key}&taxonKey={taxon_key}"

    # Make the GET request
    response = requests.get(url)

    # Check the response status
    if response.status_code == 200:
        is_invasive = response.json()
        return False if is_invasive == 0 else True
    else:
        print(f"Request failed with status code: {response.status_code}")


async def get_invasives_dataset():
    # Global Register of Introduced and Invasive Species - United States
    dataset_key = '32ad19ed-6b89-447a-9242-795c0897f345'

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

    key = gbif_downloads.gbif_download_request(
        request_body=json.dumps(request_body),
        pwd=settings.gbif.password,
        username=settings.gbif.user
    )

    output_dir = await gbif_downloads.get_gbif_download(key, output_fp=DATA_OUT_PATH, target_files=['occurrence.txt'])

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
