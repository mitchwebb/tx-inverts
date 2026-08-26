# This is a MATERIALIZED VIEW dependent on the gbif_observations and observation_regions tables
from backend.db.schema.base_table import DBTable


class TaxonRegionPresence(DBTable):
    """
    Mat view with accepted_taxon_key and region_id pairs
    """

    name = 'taxon_region_presence'
    primary_key = None
    columns = {
        'accepted_taxon_key': 'TEXT',
        'region_id': 'TEXT'
    }


TAXON_PRESENCE_TABLE = TaxonRegionPresence()
