# Tile renders faster than this many seconds are not stored in the cache
MIN_COMPUTE_S = 2.0

# Ceiling for cache size. While creating and inserting tiles,
# cache size will briefly exceed this, before being reduced
TILE_CACHE_MAX_BYTES = 512 * 1024 * 1024

# Target to reduce cache size below when removing records
TILE_CACHE_TARGET_BYTES = 450 * 1024 * 1024
