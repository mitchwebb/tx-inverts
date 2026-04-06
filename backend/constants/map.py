# Constants and mapping values
import os
from backend.config import get_settings


# Get settings for backend_root value
settings = get_settings()

# Path to Texas shapefile (currently lives with repo)
TEXAS_GEOJSON = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'tx.geojson')

TEXAS_PARKS_GDB = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'LWRCRP.gdb')

TEXAS_COUNTIES_GEOJSON = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'tx_counties.geojson')

TEXAS_ECO_L3_SHP = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'tx_eco_l3.shp')

TEXAS_ECO_L4_SHP = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'tx_eco_l4.shp')

# Base tile size in pixels at each zoom level
WEB_MERCATOR_TILE_SIZE = 156543.03

# Base size of observations square in pixels at each zoom level
PIXELS_PER_GRID = 4

# Zoom levels on which to show/store bin tiles
# Can be used when calculating caches
BIN_ZOOM_LEVELS = [2, 3, 4, 5, 6, 7, 8, 9]

# Web mercator value that needs to be added to x-values for calculations with x, y, z
HALF_WORLD = 20037508.342789244


# Derive meters_per_pixel value from our tile size
def meters_per_pixel(zoom: int) -> float:
    return WEB_MERCATOR_TILE_SIZE / (2 ** zoom)
