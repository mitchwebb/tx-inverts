from backend.db.schema.base_table import DBTable


class DataMetadata(DBTable):
    """
    Table of various database metadata values.
    """

    name = 'data_metadata'
    primary_key = 'dataset_name'
    columns = {
        'dataset_name': 'TEXT PRIMARY KEY',
        'last_updated_at': 'TIMESTAMPTZ NOT NULL DEFAULT NOW()',
        'doi': 'TEXT'
    }


DATA_META_TABLE = DataMetadata()
