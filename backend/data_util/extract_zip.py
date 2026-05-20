from typing import List
import zipfile
import time
import os

from backend.core.logging import data_logger


def extract_zip_files(fp: str, output_fp: str, target_files: List[str] = None, delete_zip: bool = False) -> str:
    """
    Helper to extract zip files, extracting only specific files if provided by name
    Optionally deleted original .zip

    Args:
        fp (str): Filepath to .zip
        output_fp (str): Desired output path
        target_files (List[str]): Optional list of desired file names
        delete_zip (bool): Optional boolean for deleted original .zip

    Return:
        (str) output_fp if files extracted
    """

    if not os.path.exists(fp):
        data_logger.error(f'{fp} does not exist')
        raise FileNotFoundError(f"{fp} does not exist.")

    try:
        # Open .zip
        with zipfile.ZipFile(fp, 'r') as zip_ref:
            # If target files provided, extract these
            if target_files:
                # Normalize target_files to list (if string provided)
                if isinstance(target_files, str):
                    target_files = [target_files]
                available_files = zip_ref.namelist()
                for target_file in target_files:
                    if target_file in available_files:
                        data_logger.info(
                            f'Extracting {target_file} from .zip...')
                        zip_ref.extract(target_file, output_fp)
                    else:
                        data_logger.error(
                            f'{target_file} not found in .zip. Exiting process...')
                        raise FileNotFoundError(
                            f"{target_file} not found in .zip archive.")
            else:
                data_logger.info('Extracting files from zip...')
                zip_ref.extractall(output_fp)

        if delete_zip:
            data_logger.info('Deleting original zip...')
            try:
                os.remove(fp)
            except PermissionError as e:
                data_logger.error(
                    f"Zip file could not be deleted immediately: {e}")
                time.sleep(1)
                try:
                    os.remove(fp)
                except Exception as e2:
                    data_logger.exception(f"Still couldn't delete zip: {e2}")

        data_logger.info(f'File(s) downloaded successfully to {output_fp}')

        return output_fp

    except FileNotFoundError as e:
        data_logger.exception(str(e))
        raise

    except zipfile.BadZipFile:
        data_logger.exception(
            f"Failed to open zip file {fp}. It may be corrupted.")
        raise

    except Exception as e:
        data_logger.exception(f"Unexpected error during extraction: {e}")
        raise
