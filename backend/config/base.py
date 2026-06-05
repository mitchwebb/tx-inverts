# Base app setting management
from backend.config.cors import CORSSettings
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .database import PostgresSettings
from .gbif import GBIFSettings


# Determine backend root
DEFAULT_BACKEND_ROOT = Path(__file__).resolve().parent.parent

ENV_NESTED_DELIM = '__'


class BaseAppSettings(BaseSettings):
    # Shared settings
    debug: bool = False
    backend_root: Path = DEFAULT_BACKEND_ROOT

    # Determined by .env
    database: PostgresSettings
    gbif: GBIFSettings
    cors: CORSSettings

    model_config = SettingsConfigDict(
        env_file='.env',  # Fallback for common variables
        env_nested_delimiter=ENV_NESTED_DELIM  # For nested settings
    )


# Choose the settings class based on the environment
class DevSettings(BaseAppSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter=ENV_NESTED_DELIM,
        env_file='.env.dev',
    )


class ProdSettings(BaseAppSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter=ENV_NESTED_DELIM,
        env_file='.env.prod',
    )
