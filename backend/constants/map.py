import os
from backend.config import get_settings


settings = get_settings()

TEXAS_GEOJSON = os.path.join(
    settings.backend_root, 'static', 'shapefiles', 'tx.geojson')
WEB_MERCATOR_TILE_SIZE = 156543.03

# Zoom levels on which to show/store bin tiles
BIN_ZOOM_LEVELS = [2, 3, 4, 5, 6, 7, 8, 9]
PIXELS_PER_GRID = 4  # size of square in pixels

# Web mercator value that needs to be added to x-values for calculations with x, y, z
HALF_WORLD = 20037508.342789244


# Derive meters_per_pixel value from our tile size
def meters_per_pixel(zoom: int) -> float:
    return WEB_MERCATOR_TILE_SIZE / (2 ** zoom)
