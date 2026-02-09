from pydantic_settings import BaseSettings


class CORSSettings(BaseSettings):
    domain: str
