# This is a MATERIALIZED VIEW for easy region info lookup via ID
from backend.db.schema.base import DBTable


class Regions(DBTable):
    name = 'regions'
    primary_key = None,
    columns = {
        'id': 'UUID',
        'region_type': 'TEXT',
        'name': 'TEXT',
        'geometry': 'GEOMETRY(MultiPolygon, 4326)'
    }


REGIONS_VIEW = Regions()
