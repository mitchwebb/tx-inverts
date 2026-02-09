import zipfile
import os


# TODO: Erroring on extraction should make operation FAIL. Currently it will still delete the zip
# if delete_zip is true and extraction fails.
# ALSO. Target_files needing to be an array is bad, since (at the moment) you can input a string
def extract_zip_files(fp, output_fp, target_files=None, delete_zip=False) -> str | None:
    if not os.path.exists(fp):
        print(f'{fp} does not exist')
        return None

    try:
        # Open .zip
        with zipfile.ZipFile(fp, 'r') as zip_ref:
            # If target files provided, extract these
            if target_files:
                available_files = zip_ref.namelist()
                for target_file in target_files:
                    if target_file in available_files:
                        print(f'Extracting {target_file} from .zip...')
                        zip_ref.extract(target_file, output_fp)
                    else:
                        print(f'{target_file} not found in .zip. Exiting process...')
                        raise FileNotFoundError(f"{target_file} not found in .zip archive.")
            else:
                print('Extracting files from zip...')
                zip_ref.extractall(output_fp)

        if delete_zip:
            print('Deleting original zip...')
            try:
                os.remove(fp)
            except PermissionError as e:
                import time
                import logging
                logging.error(
                    f"Zip file could not be deleted immediately: {e}")
                time.sleep(1)
                try:
                    os.remove(fp)
                except Exception as e2:
                    logging.error(f"Still couldn't delete zip: {e2}")

        print(f'File(s) downloaded successfully to {output_fp}')

    except zipfile.BadZipFile:
        print(f"Failed to open zip file {fp}. It may be corrupted.")

    return output_fp