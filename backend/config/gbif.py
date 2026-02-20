from pydantic import Field
from pydantic_settings import BaseSettings


# GBIF
class GBIFSettings(BaseSettings):
    user: str
    password: str
    email: str
    url: str = 'http://api.gbif.org/v1/'
