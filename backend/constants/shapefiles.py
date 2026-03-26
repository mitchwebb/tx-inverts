
# Maps from shape/geojson file naming to database table naming
from backend.constants.map import TEXAS_COUNTIES_GEOJSON, TEXAS_GEOJSON, TEXAS_PARKS_GEOJSON
from backend.db_schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_GEOMETRY_TABLE, TEXAS_PARKS_TABLE


TX_COUNTIES_COL_MAP = {
    'COUNTY': 'county',
}

TX_PARKS_COL_MAP = {
    'OBJECTID': 'id',
    'ParkName': 'park_name',
    'PropType': 'prop_type',
}

TX_COL_MAP = {
    'STATE': 'state'
}

GEOMETRY_TABLE_CONFIGS = [
    (TEXAS_COUNTIES_GEOJSON, TEXAS_COUNTIES_TABLE, TX_COUNTIES_COL_MAP),
    (TEXAS_PARKS_GEOJSON, TEXAS_PARKS_TABLE, TX_PARKS_COL_MAP),
    (TEXAS_GEOJSON, TEXAS_GEOMETRY_TABLE, TX_COL_MAP),
]
