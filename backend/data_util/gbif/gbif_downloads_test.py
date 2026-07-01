import pytest
from backend.config import get_settings
from backend.data_util.gbif.gbif_downloads import gbif_download_request

REQUEST_BODY = '{"type": "OCCURRENCE", "format": "SIMPLE_CSV"}'

SETTINGS = get_settings()


# Test bad credentials error on 401 (just testing erroring behavior)
async def test_raises_on_bad_credentials(mocker):
    mock_response = mocker.MagicMock()
    mock_response.status = 401
    mock_response.text = mocker.AsyncMock(return_value='')

    mock_session = mocker.MagicMock()
    mock_session.post = mocker.AsyncMock(return_value=mock_response)

    # Patch the aiohttp session to return our mock_session/response
    mocker.patch(
        'backend.data_util.gbif.gbif_downloads.aiohttp.ClientSession',
        return_value=mocker.MagicMock(
            __aenter__=mocker.AsyncMock(return_value=mock_session),
            __aexit__=mocker.AsyncMock(return_value=False)
        )
    )

    with pytest.raises(RuntimeError, match='401'):
        await gbif_download_request(REQUEST_BODY, pwd='wrong', username='wrong')


# Test that gbif_download_request returns download key on 201 (just return behavior)
async def test_returns_download_key(mocker):
    mock_response = mocker.MagicMock()
    mock_response.status = 201
    mock_response.text = mocker.AsyncMock(return_value='gbif_key')

    mock_session = mocker.MagicMock()
    mock_session.post = mocker.AsyncMock(return_value=mock_response)

    # Patch the aiohttp session to return our mock_session/response
    mocker.patch(
        'backend.data_util.gbif.gbif_downloads.aiohttp.ClientSession',
        return_value=mocker.MagicMock(
            __aenter__=mocker.AsyncMock(return_value=mock_session),
            __aexit__=mocker.AsyncMock(return_value=False)
        )
    )

    result = await gbif_download_request(REQUEST_BODY, pwd='pwd', username='user')
    assert result == 'gbif_key'
