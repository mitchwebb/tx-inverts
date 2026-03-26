from .base import DBTable


class TexasGeometry(DBTable):
    name = 'tx_geometry'
    primary_key = 'state'
    columns = {
        'state': 'TEXT PRIMARY KEY',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_GEOMETRY_TABLE = TexasGeometry()


class TexasParksTable(DBTable):
    name = 'tx_parks'
    primary_key = 'id'  # ParkName in file
    columns = {
        'id': 'INT PRIMARY KEY',
        'park_name': 'TEXT',
        'prop_type': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_PARKS_TABLE = TexasParksTable()


class TexasCountiesTable(DBTable):
    name = 'tx_counties'
    primary_key = 'county'
    columns = {
        'county': 'TEXT PRIMARY KEY',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_COUNTIES_TABLE = TexasCountiesTable()

GEOMETRY_TABLES = [
    TEXAS_GEOMETRY_TABLE,
    TEXAS_COUNTIES_TABLE,
    TEXAS_PARKS_TABLE
]
