import json
import os
import csv
from pathlib import Path
import pandas as pd
from pandas import DataFrame
from backend.config import get_settings
from backend.core.logging import tasks_logger
from backend.constants.paths import DATA_OUT_PATH
from backend.data_util.gbif.gbif_downloads import gbif_download_request, get_gbif_download
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.data_util.taxa_data import inverts_mask


# Simple flow to request and retrieve gbif invasive species dataset
async def get_invasives_dataset():
    tasks_logger.info("Retrieving invasives dataset from GBIF...")

    # Global Register of Introduced and Invasive Species - United States
    # While this wont change often, and is only used to create the data table, it's worth
    # noting that this may be updated one day, and this value may need to be replaced
    dataset_key = '32ad19ed-6b89-447a-9242-795c0897f345'

    settings = get_settings()

    # Request a GBIF download
    request_body = {
        'creator': settings.gbif.user,
        'notificationAddresses': [
            settings.gbif.email
        ],
        'format': 'dwca',
        'sendNotification': True,
        'predicate': {
            'type': 'equals',
            'key': 'DATASET_KEY',
            'value': dataset_key,
            'matchCase': False
        }
    }

    # Request GBIF download from API
    key = await gbif_download_request(
        request_body=json.dumps(request_body),
        pwd=settings.gbif.password,
        username=settings.gbif.user
    )

    # Wait for/retrieve GBIF download
    output_dir = await get_gbif_download(key, output_fp=DATA_OUT_PATH, target_files=['occurrence.txt'])

    # Get filepath for invasives occurrence.txt file for return
    observations_fp = os.path.join(output_dir, 'occurrence.txt')

    return observations_fp


async def prep_invasives_dataset(data: str | Path | DataFrame) -> DataFrame:
    # If passed filepath string or Path
    if isinstance(data, (str, Path)):
        # Read in file at provided path
        df = pd.read_csv(
            data,
            delimiter='\t',
            quoting=csv.QUOTE_NONE,
            on_bad_lines='warn',
            low_memory=False,
            header=0
        )
    else:
        df = data

    # Add taxonID column with values of taxonKey column
    df['taxonID'] = df['taxonKey']

    # Reasonably, we're not tagging anything higher than species
    # This filter eliminates GBIF oddities, like how the red-black
    # hybrid Solenopsis is resolving to 'Formicidae', causing Formicidae to be
    # marked as invasive
    mask = inverts_mask(df) & df['taxonRank'].isin(
        ['GENUS', 'SPECIES', 'SUBSPECIES'])

    # Apply filter
    filtered_df = df.loc[mask]

    # Coerce and validate
    filtered_df = US_INVASIVES_TABLE.coerce_dataframe(filtered_df)

    return filtered_df
