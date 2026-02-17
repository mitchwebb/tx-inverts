# Logic for inititating and retreiving an occurrence download from GBIF

import requests
import time
import os
import asyncio
import aiohttp
from backend.data_util.extract_zip import extract_zip_files
from backend.core.logging import data_logger


def gbif_download_request(request_body: str, pwd: None, username: None, test=False):
    """
    Creates a download request using GBIF's API

    This will kick off a data download request on GBIF's end, which can take 
    anywhere from 1 minute to 30+ minutes, depending on the complexity of the
    query as well as the current status of GBIF's download API.

    This function is designed to be used in conjuction with the 
    get_GBIF_download function.

    Args:
        request_body (str): GBIF request body (refer to GBIF documentation)
        test (bool, optional): Determines use of GBIF test API for testing

    Returns:
        GBIF download key (str)
    """

    headers = {
        "Content-Type": "application/json"
    }

    if test:
        GBIF_url = "http://api.gbif-uat.org/v1/occurrence/download/request"
    else:
        GBIF_url = "http://api.gbif.org/v1/occurrence/download/request"

    try:
        response = requests.post(GBIF_url, data=request_body, auth=(
            username, pwd), headers=headers)
        if response.status_code == 201:
            data_logger.info('Download request submitted successfully.')
            data_logger.info(
                f'Find this download request at https://www.gbif.org/occurrence/download/{response.text}')
            return response.text
        elif response.status_code == 400:
            data_logger.error(f'Error: {response.status_code}: Invalid Query')
            return None
        elif response.status_code == 401:
            data_logger.error(f'Error: Incorrect credentials.')
            return None
        elif response.status_code == 429:
            data_logger.error(
                f'Error: {response.status_code}: Too many concurrent downloads')
            return None
        else:
            data_logger.error(f'Error: {response.status_code}: {response.text}')
            return None

    except Exception as e:
        data_logger.exception(f"Request failed: {e}")
        return None


async def get_gbif_download(key: str, output_fp: str, time_to_wait: int = 1200, target_files=None, verbose=False):
    """
    Uses a GBIF download key to download and save a GBIF download to a local CSV

    This function will attempt to download the provided GBIF download every
    ten seconds for a given time (time_to_wait)

    This function can be used in conjuction with the 
    GBIF_download_request function.

    Args:
        key (str): GBIF API endpoint (ex: 'occurrence/download/request')
        output_fp (str): Desired filepath for resulting CSV (refer to GBIF documentation)
        time_to_wait (int, optional): The total amount of time to continue
            pinging the GBIF api (default is 20 minutes)
        target_files (string, optional): Specific files to extract (useful for DWCA archives)
        verbose (bool): Controls GBIF retry/ping output messages

    Returns:
        output_filepath (str): Location of resultant file
    """

    # How long to wait between attempts
    waiting_interval = 10

    # Get start time for calculating total time
    start_time = time.time()
    end_time = start_time + time_to_wait

    data_logger.info(
        f'Waiting for GBIF download to be ready (will try for {time_to_wait/60} minutes)...')

    while time.time() < end_time:
        try:
            # This is how long the session will stay open for downloading/unzipping the file
            session_timeout = aiohttp.ClientTimeout(total=100000)
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.get(f'http://api.gbif.org/v1/occurrence/download/request/{key}', allow_redirects=True) as response:
                    if response.status == 302:
                        body = await response.text()
                        data_logger.info(f'Download found. {body}')
                        return None
                    # If the download is found
                    if response.status == 200:
                        chunk_size = 1024 * 1024
                        downloaded = 0
                        zip_fp = os.path.join(output_fp, f'{key}.zip')
                        # Get content length if available
                        total_size = int(
                            response.headers.get("Content-Length", 0))
                        if total_size:
                            data_logger.info(
                                f"Starting download of {total_size / (1024*1024):.2f} MB")
                        else:
                            data_logger.info("Starting download (size unknown)")
                        with open(zip_fp, "wb") as f:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                f.write(chunk)
                                downloaded += len(chunk)
                        data_logger.info(f'Download complete: {zip_fp}')
                        output_fp = extract_zip_files(zip_fp, os.path.join(
                            output_fp, key), target_files, delete_zip=True)
                        data_logger.info(
                            f"Finished downloading {downloaded / (1024*1024):.2f} MB")
                        return output_fp
                    # This is what GBIF returns when the download is still being processed
                    elif response.status == 404:
                        if (verbose):
                            data_logger.error(
                                f"No response for that key. Download is likely still being processed in GBIF's system. Trying again in {waiting_interval} seconds.")
                    elif response.status == 410:
                        data_logger.error(
                            'Occurrence download file was erased and no longer exists.')
                        return None
                    else:
                        data_logger.error(
                            f'Attempt failed. Status code: {response.status}.')
                        return None
        except Exception as e:
            data_logger.exception(f'Error occurred: {e}')
            return

        # asyncio so the server doesn't get hung up waiting
        await asyncio.sleep(waiting_interval)

    # If failed within provided time, give up
    raise (f'No successful response received within {time_to_wait} seconds.')
