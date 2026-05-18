from .base import DBTable


class TexasGeometry(DBTable):
    name = 'tx_geometry'
    primary_key = 'state'
    columns = {
        'id': 'uuid PRIMARY KEY',
        'state': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_GEOMETRY_TABLE = TexasGeometry()


class TexasParksTable(DBTable):
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
    name = 'tx_counties'
    primary_key = 'county'
    columns = {
        'id': 'uuid PRIMARY KEY',
        'county': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


TEXAS_COUNTIES_TABLE = TexasCountiesTable()

GEOMETRY_TABLES = [
    TEXAS_GEOMETRY_TABLE,
    TEXAS_COUNTIES_TABLE,
    TEXAS_PARKS_TABLE
]
