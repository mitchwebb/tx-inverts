from .base import DBTable


class GeometriesTable(DBTable):
    name = 'geometries'
    primary_key = 'geometry_name'
    columns = {
        'geometry_name': 'TEXT PRIMARY KEY',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


GEOMETRIES_TABLE = GeometriesTable()
