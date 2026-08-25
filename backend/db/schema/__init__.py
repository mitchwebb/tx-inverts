# Registry for all tables
from backend.db.schema.gbif_dataset_metadata import GBIF_DATASET_META
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE, ObservationRegions
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from .gbif_observations import GBIF_OBSERVATIONS_TABLE
from .gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from .data_metadata import DATA_META_TABLE
from .geometries import GEOMETRY_TABLES
from .base_table import DBTable


# Running list of all primary tables needed for auto-initialization
# Order matters (OBSERVATION_REGIONS_TABLE creation relies on GEOMETRY tables)
ALL_TABLES: list[DBTable] = [
    GBIF_OBSERVATIONS_TABLE,
    GBIF_INVERTS_BACKBONE,
    GBIF_DATASET_META,
    DATA_META_TABLE,
    US_INVASIVES_TABLE
] + GEOMETRY_TABLES + [OBSERVATION_REGIONS_TABLE]
