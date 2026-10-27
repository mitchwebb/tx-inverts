# Various geometry tables for mapping
from .base_table import DBTable


# Sourced from https://gis-txdot.opendata.arcgis.com/datasets/texas-state-boundary-detailed
class TexasGeometry(DBTable):
    """
    Detailed Texas boundary geometry from TxDOT Open Data
    """

    name = 'tx_geometry'
    primary_key = 'id'
    columns = {
        'id': 'uuid PRIMARY KEY',
        'state': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_GEOMETRY_TABLE = TexasGeometry()


# Sourced from https://gis-tpwd.opendata.arcgis.com/datasets/ec4e6d378ba14779b5d569c27f1236de
class TexasParksTable(DBTable):
    """
    Texas parks and lands shapefile from TPWD Open Data
    """

    name = 'tx_parks'
    primary_key = 'id'  # ParkName in file
    columns = {
        'id': 'uuid PRIMARY KEY',
        'prop_name': 'TEXT',
        'alt_prop_name': 'TEXT',
        'prop_class': 'TEXT',
        'owner': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_PARKS_TABLE = TexasParksTable()


# Sourced from https://gis-txdot.opendata.arcgis.com/datasets/9b2eb7d232584572ad53bad41c76b04d_0
class TexasCountiesTable(DBTable):
    """
    Texas counties shapefile from TxDOT Open Data
    """

    name = 'tx_counties'
    primary_key = 'id'
    columns = {
        'id': 'uuid PRIMARY KEY',
        'county': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_COUNTIES_TABLE = TexasCountiesTable()

# Compiled list of geometry tables for ALL_TABLES const/automatic creation
GEOMETRY_TABLES = [
    TEXAS_GEOMETRY_TABLE,
    TEXAS_COUNTIES_TABLE,
    TEXAS_PARKS_TABLE
]


# While they aren't hosted in the database yet, source files for Ecoregions are as follows:
# Texas L3 Ecoregions: https://dmap-prod-oms-edc.s3.us-east-1.amazonaws.com/ORD/Ecoregions/tx/tx_eco_l3.zip
# Texas l4 Ecoregions: https://dmap-prod-oms-edc.s3.us-east-1.amazonaws.com/ORD/Ecoregions/tx/tx_eco_l4.zip
