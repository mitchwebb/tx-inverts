from backend.db.schema.base_table import DBTable


class GBIFDatasetMetadata(DBTable):
    """
    Table of all dataset keys and titles.
    Designed to be populated through GBIF API calls, the only source of the 'title' attribute.
    """

    name = 'gbif_dataset_metadata'
    primary_key = 'dataset_key'
    columns = {
        'dataset_key': 'TEXT PRIMARY KEY',
        'dataset_title': 'TEXT',
    }


GBIF_DATASET_META = GBIFDatasetMetadata()
