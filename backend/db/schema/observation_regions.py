from backend.db.schema.base_table import DBTable


class ObservationRegions(DBTable):
    name = 'observation_regions'
    primary_key = None
    columns = {
        'observation_id': 'BIGINT REFERENCES gbif_observations(gbif_id) ON DELETE CASCADE',
        'region_id': 'UUID',
        'region_type': 'TEXT'
    }


OBSERVATION_REGIONS_TABLE = ObservationRegions()
