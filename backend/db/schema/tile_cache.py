from .base_table import DBTable


class TileCache(DBTable):
    name = 'taxon_tile_cache'
    primary_key = 'PRIMARY KEY key'
    columns = {
        'key': 'TEXT PRIMARY KEY',
        'data': 'BYTEA NOT NULL',  # Empty tiles stored as b''
        'size_bytes': 'BIGINT NOT NULL',
        # Marks tiles pinned (to not be culled)
        'pinned': 'BOOLEAN NOT NULL DEFAULT false',
        'last_used_at': 'TIMESTAMPTZ'
    }


TILE_CACHE = TileCache()
