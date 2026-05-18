from .base import DBTable


class TaxonTileCache(DBTable):
    name = 'taxon_tile_cache'
    primary_key = 'PRIMARY KEY (taxon_id, zoom, x_bin, y_bin, event_month, institution_code)'
    columns = {
        'taxon_id': 'BIGINT NOT NULL',
        'zoom': 'INT NOT NULL',
        'x_bin': 'INT NOT NULL',
        'y_bin': 'INT NOT NULL',
        'observation_count': 'INT NOT NULL',
        'institution_code': 'TEXT NOT NULL',
    }


TAXON_TILE_CACHE = TaxonTileCache()
