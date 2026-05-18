# Paths to various files used by backend

import os
from backend.config import get_settings


# Path to data folder (used with GBIF imports)
DATA_OUT_PATH = os.path.join(get_settings().backend_root, 'data')


# Make paths to various shapefiles for map layers
settings = get_settings()
base = os.path.join(settings.backend_root, 'static', 'shapefiles')

SHAPEFILE_PATHS = {
    'texas':    os.path.join(base, 'tx.geojson'),
    'parks':    os.path.join(base, 'LWRCRP.gdb'),
    'counties': os.path.join(base, 'tx_counties.geojson'),
    'eco_l3':   os.path.join(base, 'tx_eco_l3.shp'),
    'eco_l4':   os.path.join(base, 'tx_eco_l4.shp'),
}
