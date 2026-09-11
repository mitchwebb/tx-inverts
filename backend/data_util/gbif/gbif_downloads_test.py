from backend.data_util.gbif.gbif_downloads import get_gbif_download
import os
import pytest
from backend.config import get_settings
from backend.data_util.gbif.gbif_downloads import gbif_download_request
import aiohttp

SETTINGS = get_settings()

TEST_REQUEST_BODY = "{'type': 'OCCURRENCE', 'format': 'SIMPLE_CSV'}"


@pytest.fixture
def session_patch(mocker):
    def _patch(status: int, text: str):
        mock_response = mocker.MagicMock(
            status=status,
            text=mocker.AsyncMock(return_value=text)
        )
        mock_session = mocker.MagicMock(
            post=mocker.AsyncMock(return_value=mock_response)
        )

        # Patch the aiohttp session to return our mock_session/response
        mocker.patch(
            'backend.data_util.gbif.gbif_downloads.aiohttp.ClientSession',
            return_value=mocker.MagicMock(
                __aenter__=mocker.AsyncMock(return_value=mock_session),
                __aexit__=mocker.AsyncMock(return_value=False)
            )
        )
        return mock_session

    return _patch


class TestGBIFDownloadRequest:
    @pytest.mark.asyncio
    async def test_raises_on_bad_credentials(self, session_patch):
        """Test bad credentials error on 401 (just testing erroring behavior)"""
        session_patch(status=401, text='')

        with pytest.raises(RuntimeError, match='401'):
            await gbif_download_request(TEST_REQUEST_BODY, pwd='wrong', username='wrong')

    @pytest.mark.asyncio
    async def test_returns_download_key(self, session_patch):
        """Test that gbif_download_request returns download key on 201 (just return behavior)"""
        session_patch(status=201, text='gbif_key')

        result = await gbif_download_request(TEST_REQUEST_BODY, pwd='pwd', username='user')
        assert result == 'gbif_key'

    @pytest.mark.asyncio
    async def test_posts_correct_request(self, session_patch):
        """Test that request request args and body are passed correctly"""
        mock_session = session_patch(status=201, text='gbif_key')

        await gbif_download_request(TEST_REQUEST_BODY, pwd='pwd', username='user')

        mock_session.post.assert_called_once()
        _, kwargs = mock_session.post.call_args
        assert mock_session.post.call_args.args[0] == 'https://api.gbif.org/v1/occurrence/download/request'
        assert kwargs['data'] == TEST_REQUEST_BODY
        assert isinstance(kwargs['auth'], aiohttp.BasicAuth)
        assert kwargs['auth'].login == 'user'
        assert kwargs['auth'].password == 'pwd'
        assert kwargs['headers'] == {'Content-Type': 'application/json'}

    @pytest.mark.asyncio
    async def test_uses_uat_url_when_test_true(self, session_patch):
        mock_session = session_patch(status=201, text='gbif_key')

        await gbif_download_request(TEST_REQUEST_BODY, pwd='pwd', username='user', test=True)

        called_url = mock_session.post.call_args.args[0]
        assert called_url == 'https://api.gbif-uat.org/v1/occurrence/download/request'

    @pytest.mark.asyncio
    async def test_raises_on_other_error_status(self, session_patch):
        session_patch(status=500, text='Internal Server Error')

        with pytest.raises(RuntimeError, match='500.*Internal Server Error'):
            await gbif_download_request(TEST_REQUEST_BODY, pwd='pwd', username='user')


@pytest.fixture
def download_session_patch(mocker):
    def _patch(get_side_effects: list):
        mock_session = mocker.MagicMock(
            get=mocker.MagicMock(side_effect=get_side_effects))
        mocker.patch(
            'backend.data_util.gbif.gbif_downloads.aiohttp.ClientSession',
            return_value=mocker.MagicMock(
                __aenter__=mocker.AsyncMock(return_value=mock_session),
                __aexit__=mocker.AsyncMock(return_value=False)
            )
        )
        mocker.patch(
            'backend.data_util.gbif.gbif_downloads.asyncio.sleep', mocker.AsyncMock())
        return mock_session
    return _patch


@pytest.fixture
def mock_extract(mocker):
    return mocker.patch(
        'backend.data_util.gbif.gbif_downloads.extract_zip_files',
        return_value='/fake/extracted/path'
    )


def _async_context_manager(mocker, value=None, exc=None):
    """Mock an async context manager: `async with x as y:`."""
    cm = mocker.MagicMock()
    cm.__aenter__ = mocker.AsyncMock(
        side_effect=exc) if exc else mocker.AsyncMock(return_value=value)
    cm.__aexit__ = mocker.AsyncMock(return_value=False)
    return cm


def _meta(mocker, size=0):
    """Mock meta response for async context manager"""
    return mocker.MagicMock(json=mocker.AsyncMock(return_value={'size': size}))


def _response(mocker, status, body=b''):
    """Mock response for async context manager"""
    async def chunks():
        if body:
            yield body
    response = mocker.MagicMock(status=status)
    response.content.iter_chunked = mocker.MagicMock(return_value=chunks())
    return response


class TestGetGBIFDownload:
    @pytest.mark.asyncio
    async def test_downloads_and_extracts_on_200(self, mocker, download_session_patch, mock_extract, tmp_path):
        """Test that a 200 response downloads and extracts target files"""

        body = b'col1,col2\nval1,val2\n'
        mock_session = download_session_patch([
            _async_context_manager(mocker, _meta(mocker, size=len(body))),
            _async_context_manager(mocker, _response(mocker, 200, body)),
        ])

        result = await get_gbif_download(key='abc123', output_fp=str(tmp_path), target_files=['occ.txt'])

        zip_fp = os.path.join(str(tmp_path), 'abc123.zip')
        with open(zip_fp, 'rb') as f:
            assert f.read() == body
        mock_extract.assert_called_once_with(
            zip_fp, os.path.join(str(tmp_path), 'abc123'), ['occ.txt'], delete_zip=True)
        assert result == '/fake/extracted/path'

        calls = mock_session.get.call_args_list
        assert calls[0].args[0] == 'https://api.gbif.org/v1/occurrence/download/abc123'
        assert calls[1].args[0] == 'https://api.gbif.org/v1/occurrence/download/request/abc123'

    @pytest.mark.asyncio
    async def test_retries_on_404_then_succeeds(self, mocker, download_session_patch, mock_extract, tmp_path):
        """Test that an initial 404 response tries again"""

        mock_session = download_session_patch([
            _async_context_manager(mocker, _meta(mocker)),
            _async_context_manager(mocker, _response(mocker, 404)),
            _async_context_manager(mocker, _meta(mocker)),
            _async_context_manager(mocker, _response(mocker, 200, b'data')),
        ])

        result = await get_gbif_download(key='k', output_fp=str(tmp_path))

        assert mock_session.get.call_count == 4
        assert result == '/fake/extracted/path'

    @pytest.mark.asyncio
    async def test_raises_on_410(self, mocker, download_session_patch, mock_extract, tmp_path):
        """Test for FileNotFoundError on 410 response"""

        download_session_patch([
            _async_context_manager(mocker, _meta(mocker)),
            _async_context_manager(mocker, _response(mocker, 410)),
        ])

        with pytest.raises(FileNotFoundError):
            await get_gbif_download(key='k', output_fp=str(tmp_path))
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_unexpected_status(self, mocker, download_session_patch, mock_extract, tmp_path):
        """Test for RuntimeError on 500 response"""

        download_session_patch([
            _async_context_manager(mocker, _meta(mocker)),
            _async_context_manager(mocker, _response(mocker, 500)),
        ])

        with pytest.raises(RuntimeError, match='500'):
            await get_gbif_download(key='k', output_fp=str(tmp_path))

    @pytest.mark.asyncio
    async def test_survives_transient_network_error_and_succeeds(self, mocker, download_session_patch, mock_extract, tmp_path):
        """Test that a network error wont end the call prematurely"""

        mock_session = download_session_patch([
            _async_context_manager(
                mocker, exc=aiohttp.ClientConnectionError('reset')),
            _async_context_manager(mocker, _meta(mocker)),
            _async_context_manager(mocker, _response(mocker, 200, b'data')),
        ])

        result = await get_gbif_download(key='k', output_fp=str(tmp_path))

        assert mock_session.get.call_count == 3
        assert result == '/fake/extracted/path'

    @pytest.mark.asyncio
    async def test_raises_timeout_error_when_time_exhausted(self, download_session_patch, tmp_path):
        """Test for final timeout error if function outlasts time_to_wait"""

        mock_session = download_session_patch([])

        with pytest.raises(TimeoutError):
            await get_gbif_download(key='k', output_fp=str(tmp_path), time_to_wait=-1)
        mock_session.get.assert_not_called()
