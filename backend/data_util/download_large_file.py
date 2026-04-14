import requests
import os
import tempfile
from contextlib import contextmanager
from backend.core.logging import data_logger


@contextmanager
def download_large_temp_file(url, chunk_size=1024*1024):
    """
    Downloads a large file in chunks.
    Returns temp output filepath to be used in context.
    File is deleted after context is ended.

    Args:
        url (str): File URL.
        chunk_size (int): Chunk size in bytes. Default is 1MB.

    Returns:
        output_fp (str): Path to the downloaded file.
    """

    # Use temporary directory and path
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, 'downloaded_file')
        _download_file(url, tmp_path, chunk_size)
        yield tmp_path
        # Automatic cleanup after context exits


def download_large_file(url, output_fp=None, chunk_size=1024*1024, verbose=False):
    """
    Downloads a large file in chunks.
    Returns output filepath.

    Args:
        url (str): File URL.
        output_fp (str, optional): Output file path.
        chunk_size (int): Chunk size in bytes. Default is 1MB.
        verbose (bool)

    Returns:
        output_fp (str): Path to the downloaded file.
    """

    if not output_fp:
        raise ValueError('Must provide output_fp')

    _download_file(url, output_fp, chunk_size)
    return output_fp


def _download_file(url, output_fp, chunk_size, verbose=False):
    """
    Helper to handle streaming and saving of a file
    """
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_fp, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = (downloaded / total) * 100
                            if (verbose):
                                data_logger.debug(f"""\rDownloaded {downloaded / 1024 / 1024:.2f} MB
                                              of {total / 1024 / 1024:.2f} MB
                                              ({percent:.2f}%)", end=''""")
                        else:
                            if (verbose):
                                data_logger.info(
                                    f"Downloaded {downloaded / 1024 / 1024:.2f} MB", end='')

        data_logger.info(f"Download complete.")

    except Exception as e:
        data_logger.exception(f'Download failed: {e}')
        # If download fails, we need to delete the temp file
        if os.path.exists(output_fp):
            os.remove(output_fp)
        raise
