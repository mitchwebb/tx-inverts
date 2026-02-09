from .base import DBTable


class TaxonDescendantCache(DBTable):
    name = 'taxon_descendant_cache'
    primary_key = None
    columns = {
        'ancestor_key': 'BIGINT NOT NULL',
        'descendant_scientific_name': 'TEXT',
        'descendant_key': 'BIGINT NOT NULL'
    }
    
TAXON_DESCENDANT_CACHE = TaxonDescendantCache()