# Mapping constants

# Base tile size in pixels at each zoom level
WEB_MERCATOR_TILE_SIZE = 156543.03

# Base size of observations square in pixels at each zoom level
PIXELS_PER_GRID = 4

# Zoom levels on which to show/store bin tiles
# Can be used when calculating caches
BIN_ZOOM_LEVELS = (2, 3, 4, 5, 6, 7, 8, 9)

# Web mercator value that needs to be added to x-values for calculations with x, y, z
HALF_WORLD = 20037508.342789244


# Derive meters_per_pixel value from our tile size given a zoom level
def get_meters_per_pixel(zoom: int) -> float:
    return WEB_MERCATOR_TILE_SIZE / (2 ** zoom)
