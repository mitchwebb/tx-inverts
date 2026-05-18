
# Shapefile information and column names maps (from file names to database names)

from pydantic import BaseModel, ConfigDict

from backend.constants.paths import SHAPEFILE_PATHS
from backend.db.schema.base import DBTable
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_GEOMETRY_TABLE, TEXAS_PARKS_TABLE


### Constants for mapping shapefile columns names to database column names ###
TX_COUNTIES_COL_MAP = {
    'COUNTY': 'county',
    'geometry': 'geometry'
}
TX_PARKS_COL_MAP = {
    'ManagerClass': 'prop_class',
    'ManagerPropName': 'prop_name',
    'ManagerPropNameAlt': 'alt_prop_name',
    'Owner': 'owner',
    'geometry': 'geometry'
}
TX_COL_MAP = {
    'STATE': 'state',
    'geometry': 'geometry'
}


# Class for storing geometry layer configuration info (facilitates db table creation)
class GeometryLayerConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str
    table: DBTable
    col_map: dict[str, str]


# All geometry table configs
GEOMETRY_TABLE_CONFIGS = [
    GeometryLayerConfig(path=SHAPEFILE_PATHS['counties'],
                        table=TEXAS_COUNTIES_TABLE,
                        col_map=TX_COUNTIES_COL_MAP),
    GeometryLayerConfig(path=SHAPEFILE_PATHS['parks'],
                        table=TEXAS_PARKS_TABLE,
                        col_map=TX_PARKS_COL_MAP),
    GeometryLayerConfig(path=SHAPEFILE_PATHS['texas'],
                        table=TEXAS_GEOMETRY_TABLE,
                        col_map=TX_COL_MAP),
]
