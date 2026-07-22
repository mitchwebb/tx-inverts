import os
from dotenv import load_dotenv
from .base import DevSettings, ProdSettings
from functools import lru_cache

# Get current ENV param from base .env file
load_dotenv(dotenv_path='.env')


@lru_cache()
def get_settings():
    env = os.getenv('ENV', 'dev')
    # Ignore needed as pydantic doesn't understand these nested settings
    return ProdSettings() if env == 'prod' else DevSettings()  # type: ignore
