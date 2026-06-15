# PostgreSQL settings class
from pydantic_settings import BaseSettings
from psycopg import adapt


# PostgreSQL
class PostgresSettings(BaseSettings):
    name: str
    user: str
    password: str
    host: str = 'localhost'
    port: int = 5432

# Handle pd.na values in psycopg copy statements
class NADumper(adapt.Dumper):
    def dump(self, obj):
        return None  # tells psycopg to emit NULL