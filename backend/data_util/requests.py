
import asyncio
from typing import Any
from backend.core.logging import api_logger
import aiohttp


async def fetch_data(session: aiohttp.ClientSession, url: str) -> Any:
    """
    General helper for simple async JSON fetches given session and url

    Args:
        session (aiohttp.ClientSession): aiohttp session
        url (str): API URL for fetch request

    Return:
        JSON response (Any)
    """
    try:
        async with session.get(url) as response:
            # If response indicates error, raise
            response.raise_for_status()
            data = await response.json()
            return data
    except aiohttp.ClientError as e:
        api_logger.error(f'Error fetching data from {url}: {e}')
        raise
    except asyncio.TimeoutError:
        print(f'Request to {url} timed out')
        raise
