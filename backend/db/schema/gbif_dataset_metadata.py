from backend.db.schema.base import DBTable


class GBIFDatasetMetadata(DBTable):
    name = 'gbif_dataset_metadata'
    primary_key = 'dataset_key'
    columns = {
        'dataset_key': 'TEXT PRIMARY KEY',
        'dataset_title': 'TEXT',
    }


GBIF_DATASET_META = GBIFDatasetMetadata()
