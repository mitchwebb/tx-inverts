import requests
import os
import tempfile
from contextlib import contextmanager

@contextmanager
def download_large_temp_file(url, output_fp=None, chunk_size=1024*1024):
    """
    Downloads a large file in chunks.
    Returns output filepath to be used in context.
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
        
        
def download_large_file(url, output_fp=None, chunk_size=1024*1024):
    """
    Downloads a large file in chunks.
    Returns output filepath.

    Args:
        url (str): File URL.
        output_fp (str, optional): Output file path. Required if temporary=False.
        chunk_size (int): Chunk size in bytes. Default is 1MB.

    Returns:
        output_fp (str): Path to the downloaded file.
    """
    
    if not output_fp:
        raise ValueError('Must provide output_fp if temporary is False')
    
    _download_file(url, output_fp, chunk_size)
    return output_fp
    
    
def _download_file(url, output_fp, chunk_size):
    """
    Internal helper to stream and save a file
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
                            print(f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB "
                                f"of {total / 1024 / 1024:.2f} MB "
                                f"({percent:.2f}%)", end='')
                        else:
                            print(f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB", end='')
                            
        print("\nDownload complete.")
    
    except Exception as e:
        print(f'Download failed: {e}')
        # If download fails, we need to delete the temp file
        if os.path.exists(output_fp):
            os.remove(output_fp)
        raise