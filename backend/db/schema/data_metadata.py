from enum import StrEnum
from typing import Literal

from backend.db.schema.base_table import DBTable
from backend.db.schema.index_definitions import MATERIALIZED_VIEWS
from backend.db.schema.regions import REGIONS_VIEW
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE


class DataMetadata(DBTable):
    """
    Table of various dataset version values.
    Stores dataset name alongside their associated DOI (if applicable) 
    and their last_updated_at timestamp.

    This is intended for use with materialized views, as well as the 
    'backbone' and 'observations' datasets sourced from GBIF.

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
