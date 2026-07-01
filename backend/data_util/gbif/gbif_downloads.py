# Logic for inititating and retreiving an occurrence download from GBIF
import time
import os
import asyncio
import aiohttp
from backend.data_util.extract_zip import extract_zip_files
from backend.core.logging import data_logger


async def gbif_download_request(request_body: str, pwd: str, username: str, test: bool = False):
    """
    Creates a download request using GBIF's API

    This will kick off a data download request on GBIF's end, which can take
    anywhere from 1 minute to 30+ minutes, depending on the complexity of the
    query as well as the current status of GBIF's download API.

    This function is designed to be used in conjunction with the
    get_GBIF_download function.

    Args:
        request_body (str): GBIF request body (refer to GBIF documentation)
        pwd (str): GBIF password
        username (str): GBIF username
        test (bool = False): Determines use of GBIF test API for testing

    Returns:
        GBIF download key (str)
    """

    headers = {
        "Content-Type": "application/json"
    }

    gbif_url = "https://api.gbif.org/v1/occurrence/download/request"

    if test:
        gbif_url = "https://api.gbif-uat.org/v1/occurrence/download/request"

    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                gbif_url,
                data=request_body,
                auth=aiohttp.BasicAuth(username, pwd),
                headers=headers
            )
            if response.status == 201:
                data_logger.info('Download request submitted successfully.')
                key = await response.text()
                data_logger.info(
                    f'Find this download request at https://www.gbif.org/occurrence/download/{key}')
                return key
            if response.status == 401:
                data_logger.warning(
                    '401 Unauthorized. If using the GBIF test server, ensure you are using '
                    'credentials registered at uat.gbif.org — production credentials will not work.'
                )
                text = await response.text()
                raise RuntimeError(f'Download request failed: 401 Unauthorized')
            else:
                text = await response.text()
                raise RuntimeError(
                    f'Download request failed: {response.status}: {text}'
                )
    except Exception as e:
        data_logger.exception(f"Request failed: {e}")
        raise


# Adaptive formatting of MB logging
def _fmt_size_string(bytes: int):
    # If over one GB
    if bytes >= 1024**3:
        return f"{bytes / 1024**3:.2f} GB"
    # Else return as MB
    return f"{bytes / 1024**2:.2f} MB"


async def get_gbif_download(key: str, output_fp: str, time_to_wait: int = 10800, target_files: list[str] | None = None, verbose=False) -> str:
    """
    Uses a GBIF download key to download and save a GBIF download to a local CSV

    This function will attempt to download the provided GBIF download every
    ten seconds for a given time (time_to_wait)

    This function can be used in conjunction with the
    GBIF_download_request function.

    Args:
        key (str): GBIF download key
        output_fp (str): Desired filepath for resulting CSV (refer to GBIF documentation)
        time_to_wait (int, optional): The total amount of time to continue
            pinging the GBIF api (default is 3 hours, as is GBIF high estimate)
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

    # This is how long the session will stay open for downloading/unzipping the file
    session_timeout = aiohttp.ClientTimeout(total=100000)
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        while time.time() < end_time:
            try:
                async with session.get(f'https://api.gbif.org/v1/occurrence/download/{key}') as meta:
                    metadata = await meta.json()
                    total_size = metadata.get('size', 0)
                    if total_size:
                        data_logger.info(
                            f'Expected download size: {_fmt_size_string(total_size)}'
                        )
                async with session.get(f'https://api.gbif.org/v1/occurrence/download/request/{key}', allow_redirects=True) as response:
                    # If the download is found
                    if response.status == 200:
                        chunk_size = 1024 * 1024
                        downloaded = 0
                        next_log_threshold = 50 * 1024 * 1024  # Log every 50 MB
                        zip_fp = os.path.join(output_fp, f'{key}.zip')
                        if total_size:
                            data_logger.info(
                                f"Starting download of {_fmt_size_string(total_size)}")
                        else:
                            data_logger.info("Starting download (Size Unknown)")
                        with open(zip_fp, "wb") as f:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                f.write(chunk)
                                downloaded += len(chunk)
                                # Log download progress in 50MB chunks
                                if downloaded >= next_log_threshold:
                                    if total_size:
                                        data_logger.info(
                                            f"Downloaded {_fmt_size_string(downloaded)} / {_fmt_size_string(total_size)}")
                                    else:
                                        data_logger.info(
                                            f"Downloaded {_fmt_size_string(downloaded)} so far")
                                    next_log_threshold += 50 * 1024 * 1024
                        data_logger.info(
                            f"Download complete ({_fmt_size_string(downloaded)}): {zip_fp}")
                        output_fp = extract_zip_files(zip_fp, os.path.join(
                            output_fp, key), target_files, delete_zip=True)
                        return output_fp
                    # This is what GBIF returns when the download is still being processed
                    elif response.status == 404:
                        if (verbose):
                            data_logger.warning(
                                f"No response for that key. Download is likely still being processed in GBIF's system. Trying again in {waiting_interval} seconds.")
                    elif response.status == 410:
                        raise FileNotFoundError(
                            f'GBIF download {key} has been deleted.')
                    else:
                        raise RuntimeError(
                            f'Unexpected status code: {response.status}')
            except Exception as e:
                data_logger.exception(f'Error occurred: {e}')
                raise

            # asyncio so the server doesn't get hung up waiting
            await asyncio.sleep(waiting_interval)

    # If failed within provided time, give up
    raise TimeoutError(
        f'No successful response received within {time_to_wait} seconds.')
