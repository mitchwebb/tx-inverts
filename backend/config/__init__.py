import os
from dotenv import load_dotenv
from .base import DevSettings, ProdSettings
from functools import lru_cache

load_dotenv(dotenv_path=".env")

@lru_cache() 
def get_settings():
    env = os.getenv('ENV', 'dev')
    
    if env == 'prod':
        return ProdSettings()
    return DevSettings()