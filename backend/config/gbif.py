# GBIF settings class
from pydantic_settings import BaseSettings


# GBIF
class GBIFSettings(BaseSettings):
    user: str
    password: str
    email: str
    url: str = 'https://api.gbif.org/v1/'
