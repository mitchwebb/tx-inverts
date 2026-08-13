
import os

import pytest
from backend.data_util.download_large_file import download_large_temp_file


# Test that download_large_temp_file returns requested temp file
@pytest.mark.asyncio
async def test_returns_temp_file_context(mocker):
    # Fake download to replace _download_file helper, which normally takes a URL
    def fake_download(url, path, chunk_size, verbose):
        with open(path, 'w') as f:
            f.write('test content')

    # Patch in new download helper function
    mocker.patch('backend.data_util.download_large_file._download_file',
                 side_effect=fake_download)

    with download_large_temp_file('http://example.com/file') as tmp_path:
        assert os.path.exists(tmp_path)
        assert open(tmp_path).read() == 'test content'

    assert not os.path.exists(tmp_path)
