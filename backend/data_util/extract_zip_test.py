from os import path
import os
import shutil
import pytest
from backend.data_util.extract_zip import extract_zip_files


@pytest.fixture
def zip_fixture(tmp_path):
    filenames = ['file_1.txt', 'file_2.txt']
    for filename in filenames:
        open(path.join(tmp_path, filename), 'w').close()
    zip_file = shutil.make_archive(os.path.join(
        tmp_path, 'test_zip'), 'zip', tmp_path)
    return zip_file, tmp_path, filenames


# Make sure extract_zip_files raises FileNotFoundError for nonexistent fp
def test_raises_on_missing_zip():
    with pytest.raises(FileNotFoundError):
        extract_zip_files(fp='false_path', output_fp='dummy_path')


def test_raises_on_missing_target_file(zip_fixture):
    zip_file, tmp_path, _ = zip_fixture

    with pytest.raises(FileNotFoundError):
        extract_zip_files(fp=zip_file, output_fp=os.path.join(
            tmp_path, 'unzipped'), target_files=['bad_file.txt'])


# Test that extract_zip_files extracts ONLY target_files
def test_extracts_desired_file(zip_fixture):
    zip_file, tmp_path, (file1, file2) = zip_fixture

    # Extract JUST desired file from zip
    output_fp = extract_zip_files(fp=zip_file, output_fp=path.join(
        tmp_path, 'unzipped'), target_files=[file1])

    assert os.path.exists(os.path.join(output_fp, file1))
    assert not os.path.exists(os.path.join(output_fp, file2))


# Test that extract_zip_files extracts all files if not given target_files
def test_extracts_all_files(zip_fixture):
    zip_file, tmp_path, (file1, file2) = zip_fixture

    # Extract JUST desired file from zip
    output_fp = extract_zip_files(fp=zip_file, output_fp=path.join(
        tmp_path, 'unzipped'))

    assert os.path.exists(os.path.join(output_fp, file1))
    assert os.path.exists(os.path.join(output_fp, file2))


# Test that zip files gets deleted when delete_zip=True
def test_deletes_zip_when_flag_set(zip_fixture):
    zip_file, tmp_path, _ = zip_fixture

    extract_zip_files(
        fp=zip_file, output_fp=tmp_path, delete_zip=True)

    assert not os.path.exists(os.path.join(zip_file))
