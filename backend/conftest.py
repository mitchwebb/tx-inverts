# Make fake conn/cur for calling functions
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_conn():
    # Fake cursor with async methods
    mock_cursor = AsyncMock()

    # conn.cursor() needs to work as `async with conn.cursor(...) as cur`
    mock_cursor_ctx = MagicMock()
    mock_cursor_ctx.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_ctx.__aexit__ = AsyncMock(return_value=None)

    conn = MagicMock()
    conn.cursor = MagicMock(return_value=mock_cursor_ctx)
    return conn, mock_cursor
