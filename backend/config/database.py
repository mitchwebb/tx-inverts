from pydantic import Field
from pydantic_settings import BaseSettings


# PostgreSQL
class PostgresSettings(BaseSettings):
    name: str
    user: str
    password: str
    host: str = 'localhost'
    port: int = 5432
