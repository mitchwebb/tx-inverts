# Registry for all tables
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE, ObservationRegions
from .gbif_observations import GBIF_OBSERVATIONS_TABLE
from .gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from .geometries import GEOMETRY_TABLES
from .base import DBTable


# Running list of all tables for auto-initialization
ALL_TABLES: list[DBTable] = [
    GBIF_OBSERVATIONS_TABLE,
    GBIF_INVERTS_BACKBONE,
    GBIF_DATASET_META,
] + GEOMETRY_TABLES + [OBSERVATION_REGIONS_TABLE]
