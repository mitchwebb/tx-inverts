from typing import Iterator

import requests
import os
import tempfile
from contextlib import contextmanager
from backend.core.logging import data_logger


@contextmanager
def download_large_temp_file(url: str, chunk_size: int = 1024*1024, verbose: bool = False) -> Iterator[str]:
    """
    Downloads a large file in chunks
    Returns temp output filepath to be used in context
    File is deleted after context is ended

    Args:
        url (str): File URL
        chunk_size (int): Chunk size in bytes. Default is 1MB
        verbose (bool): Default False

    Returns:
        temp_path (Iterator[str]): Path to the temp file.
    """

    # Use temporary directory and path
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, 'downloaded_file')
        _download_file(url, tmp_path, chunk_size, verbose)
        yield tmp_path


def download_large_file(url: str, output_fp: str, chunk_size: int = 1024*1024, verbose: bool = False) -> str:
    """
    Downloads a large file in chunks.
    Returns output filepath.

    Args:
        url (str): File URL.
        output_fp (str): Output file path.
        chunk_size (int): Chunk size in bytes. Default is 1MB.
        verbose (bool)

    Returns:
        output_fp (str): Path to the downloaded file.
    """

    _download_file(url, output_fp, chunk_size, verbose)
    return output_fp


def _download_file(url, output_fp, chunk_size, verbose=False):
    """
    Helper to handle streaming and saving of a file
    """
    try:
        # Keep track of downloaded mb for logging
        last_logged_mb = 0

        # Using raw requests.get here for streaming
        with requests.get(url, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))

            # Keep track of mb downloaded
            downloaded = 0

            with open(output_fp, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        downloaded_mb = downloaded / 1024 / 1024
                        if verbose and downloaded_mb - last_logged_mb >= 10:
                            if total:
                                percent = (downloaded / total) * 100
                                data_logger.debug(
                                    f'Downloaded {downloaded_mb:.2f} MB of {total / 1024 / 1024:.2f} MB ({percent:.2f}%)')
                            else:
                                data_logger.info(
                                    f'Downloaded {downloaded_mb:.2f} MB')
                            last_logged_mb = downloaded_mb

        data_logger.info('Download complete.')

    except Exception:
        data_logger.exception('Download failed')
        # If download fails, we need to delete the temp file
        if os.path.exists(output_fp):
            os.remove(output_fp)
        raise
