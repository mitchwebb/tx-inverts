# This is a MATERIALIZED VIEW dependent on the gbif_observations and observation_regions tables
from backend.db_schema.base import DBTable


class TaxonRegionPresence(DBTable):
    name = 'taxon_region_presence'
    primary_key = None,
    columns = {
        'accepted_taxon_key': 'BIGINT',
        'region_id': 'TEXT'
    }


TAXON_PRESENCE_TABLE = TaxonRegionPresence()
