from backend.config.cors import CORSSettings
from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from .database import PostgresSettings
from .gbif import GBIFSettings

# Calculate backend root
DEFAULT_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class BaseAppSettings(BaseSettings):
    # Shared settings
    debug: bool = Field(False, env='DEBUG')
    backend_root: Path = DEFAULT_BACKEND_ROOT

    # Determined by .env
    database: PostgresSettings
    gbif: GBIFSettings
    cors: CORSSettings

    class Config:
        env_file = '.env'  # fallback for common variables
        env_nested_delimiter = '__'  # for nested settings


# Choose the settings class based on the environment
class DevSettings(BaseAppSettings):
    class Config:
        env_file = '.env.dev'


class ProdSettings(BaseAppSettings):
    class Config:
        env_file = '.env.prod'
