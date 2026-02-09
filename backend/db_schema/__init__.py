# Registry for all tables

from .gbif_observations import GBIF_OBSERVATIONS_TABLE
from .db_metadata import DB_METADATA_TABLE
from .gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from .geometries import GEOMETRIES_TABLE
from .base import DBTable

ALL_TABLES: DBTable = [
    GBIF_OBSERVATIONS_TABLE,
    DB_METADATA_TABLE,
    GBIF_INVERTS_BACKBONE,
    GEOMETRIES_TABLE
]
