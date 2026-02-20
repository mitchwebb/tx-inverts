# Model for db_metadata table
from .base import DBTable


class DBMetadata(DBTable):
    name = 'db_metadata'
    primary_key = 'key'
    columns = {
        'key': 'TEXT PRIMARY KEY',
        'table_name': 'TEXT NOT NULL',
        'description': 'TEXT'
    }


DB_METADATA_TABLE = DBMetadata()
