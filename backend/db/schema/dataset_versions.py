from backend.db.schema.base_table import DBTable


class DatasetVersions(DBTable):
    """
    Table of various dataset version values.
    Stores dataset name alongside their associated DOI (if applicable) 
    and their last_updated_at timestamp.

    This is intended for use with materialized views, as well as the 
    'backbone' and 'observations' datasets sourced from GBIF.

    DOI may be NULL. 
    """

    name = 'dataset_versions'
    primary_key = 'dataset_name'
    columns = {
        'dataset_name': 'TEXT PRIMARY KEY',
        'last_updated_at': 'TIMESTAMPTZ NOT NULL DEFAULT NOW()',
        'doi': 'TEXT'
    }


DATA_VERSIONS_TABLE = DatasetVersions()
