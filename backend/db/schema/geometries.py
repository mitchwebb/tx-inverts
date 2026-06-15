# Various geometry tables for mapping
from .base import DBTable


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
