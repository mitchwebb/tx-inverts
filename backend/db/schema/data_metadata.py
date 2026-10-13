from backend.db.schema.base_table import DBTable

# Possible values for dataset_name
OBSERVATIONS_DATASET = 'observations'
BACKBONE_DATASET = 'backbone'


class DataMetadata(DBTable):
    """
    Table of various database metadata values.
    Stores Dataset Name ('backbone', 'observations', etc.) alongside
    their associated DOI and last_updated_at timestamp.

    DOI may be NULL. 
    """

    name = 'data_metadata'
    primary_key = 'dataset_name'
    columns = {
        'dataset_name': 'TEXT PRIMARY KEY',
        'last_updated_at': 'TIMESTAMPTZ NOT NULL DEFAULT NOW()',
        'doi': 'TEXT'
    }


DATA_META_TABLE = DataMetadata()
