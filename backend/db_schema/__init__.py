# Registry for all tables

from backend.db_schema.observation_regions import OBSERVATION_REGIONS_TABLE, ObservationRegions

from .gbif_observations import GBIF_OBSERVATIONS_TABLE
from .db_metadata import DB_METADATA_TABLE
from .gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from .geometries import GEOMETRY_TABLES
from .base import DBTable


# Running list of all tables for initialization

ALL_TABLES: DBTable = [
    GBIF_OBSERVATIONS_TABLE,
    DB_METADATA_TABLE,
    GBIF_INVERTS_BACKBONE,
    # OBSERVATION_REGIONS_TABLE must be last as it references other tables
] + GEOMETRY_TABLES + [OBSERVATION_REGIONS_TABLE]
