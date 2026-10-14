import asyncio
from math import cos, log, pi, radians, tan
import time
from typing import Counter

from psycopg import AsyncConnection, sql

from backend.constants.map import TEXAS_BBOX
from backend.constants.tiles import MIN_COMPUTE_S, TILE_CACHE_MAX_BYTES, TILE_CACHE_TARGET_BYTES
from backend.data_util.db import get_single_db_connection
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.queries.tile_cache import clear_tile_cache, evict_lru_tiles, get_cache_size, get_cached_tile, store_tile
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.models.occurrence import OccurrenceFilters
from backend.routers.occurrence_router import build_tile_query, tile_key
from backend.core.logging import tasks_logger


async def get_large_taxa(conn: AsyncConnection, min_observations: int) -> list[str]:
    """Taxa (including parents) with more observations than the threshold, largest first."""
    query = sql.SQL("""
        WITH per_key AS (
            SELECT accepted_taxon_key, COUNT(*) AS n
            FROM {observations}
            WHERE collection_start_date IS NOT NULL
            GROUP BY accepted_taxon_key
        )
        SELECT tl.ancestor_id
        FROM {lineage} tl
        JOIN per_key p ON p.accepted_taxon_key = tl.accepted_taxon_key
        LEFT JOIN {taxa} t ON t.taxon_id = tl.accepted_taxon_key
        WHERE COALESCE(t.us_invasive, false) = false
           OR tl.accepted_taxon_key = tl.ancestor_id
        GROUP BY tl.ancestor_id
        HAVING SUM(p.n) > {minimum}
        ORDER BY SUM(p.n) DESC
    """).format(
        observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name),
        taxa=sql.Identifier(TX_TAXA_TABLE.name),
        minimum=sql.Literal(min_observations),
    )
    tasks_logger.info('Getting list of large taxa...')
    rows = await execute_psql_query(conn, query, fetch='all')
    return [row[0] for row in rows or []]


def _tile_xy(lon: float, lat: float, z: int) -> tuple[int, int]:
    """Standard web-map tile index containing a longitude/latitude."""
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - log(tan(radians(lat)) + 1 / cos(radians(lat))) / pi) / 2 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def tiles_covering_bbox(z: int, bbox=TEXAS_BBOX) -> list[tuple[int, int]]:
    """Get list of all tile indexes (X and Y) in bbox for a given zoom"""
    lon_min, lat_min, lon_max, lat_max = bbox
    # north-west corner: smallest x and y
    x0, y0 = _tile_xy(lon_min, lat_max, z)
    # south-east corner: largest x and y
    x1, y1 = _tile_xy(lon_max, lat_min, z)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


async def warm_one_tile(
    conn: AsyncConnection,
    taxon_id: str,
    z: int,
    x: int,
    y: int,
    pinned: bool = False
) -> str:
    """
    Render and store one default-filter tile, the same way the tile route would.
    Returns 'already_cached', 'stored', or 'fast' (rendered, too cheap to store).

    If pinned == True, tile will be marked as pinned (to avoid culling).
    """
    filters = OccurrenceFilters(taxon_ids=[taxon_id])
    key = tile_key(filters, z, x, y)

    tasks_logger.info(
        "WARM key: taxon=%s tile=%s/%s/%s key=%s",
        taxon_id, z, x, y, key,
    )

    cached = await get_cached_tile(conn, key)

    if cached['data'] is not None:
        return 'already_cached'

    query = build_tile_query(filters, z, x, y)
    started = time.monotonic()
    result = await execute_psql_query(conn, query, fetch='one', dict_cursor=False)

    render_seconds = time.monotonic() - started

    tile = bytes(result[0]) if result and result[0] is not None else b''

    if render_seconds < MIN_COMPUTE_S:
        return 'fast'

    await store_tile(conn, key, tile, cached['checked_at'], pinned)
    await conn.commit()

    return 'stored'


async def warm_tile_cache(
    conn: AsyncConnection,
    min_observations: int = 100000,
    min_zoom: int = 4,
    max_zoom: int = 6,
    concurrency: int = 2,
) -> Counter:
    """
    Pre-render default-filter tiles over Texas for the largest taxa, so the first
    visitor after a data refresh gets cached tiles. Largest taxa and lowest zoom
    levels go first, since those are the most expensive tiles.
    Run after the cache has been cleared.
    """
    taxa = await get_large_taxa(conn, min_observations)

    work = asyncio.Queue()
    for taxon_id in taxa:
        for z in range(min_zoom, max_zoom + 1):
            for x, y in tiles_covering_bbox(z):
                work.put_nowait((taxon_id, z, x, y))
    total = work.qsize()
    tasks_logger.info(
        f'Warming tile cache: {len(taxa)} taxa, {total} tiles, {concurrency} at a time')

    results = Counter()
    started = time.monotonic()

    async def worker():
        # One connection per worker: a connection runs one query at a time
        worker_conn = await get_single_db_connection()
        try:
            while True:
                try:
                    taxon_id, z, x, y = work.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    results[await warm_one_tile(worker_conn, taxon_id, z, x, y, True)] += 1
                except Exception:
                    results['error'] += 1
                    tasks_logger.exception(
                        f'Warming failed: taxon {taxon_id} tile {z}/{x}/{y}')
                    await worker_conn.rollback()  # clear any failed transaction
                done = sum(results.values())
                if done % 200 == 0:
                    tasks_logger.info(
                        f'{done}/{total} tiles, {time.monotonic() - started:.0f}s, {dict(results)}')
        finally:
            await worker_conn.close()

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    tasks_logger.info(
        f'Warming finished in {time.monotonic() - started:.0f}s: {dict(results)}')
    return results


async def rebuild_tile_cache(conn: AsyncConnection) -> None:
    """
    Final step of an observations refresh: empty the cache, then pre-render the
    large taxa. Call it after the refresh's data and last_updated_at are committed.

    A failed warm-up is logged but does not fail the refresh. The data is already
    loaded, and tiles that were not warmed are simply rendered and cached on demand.
    """
    await clear_tile_cache(conn)
    await conn.commit()
    tasks_logger.info('Tile cache cleared')
    try:
        await warm_tile_cache(conn)
    except Exception:
        tasks_logger.exception(
            'Tile cache warm-up failed; tiles will be cached on demand')


async def cull_tile_cache(conn: AsyncConnection, target_bytes: int = TILE_CACHE_TARGET_BYTES, max_bytes: int = TILE_CACHE_MAX_BYTES) -> int:
    """Evict least recently used tiles if the cache exceeds max_bytes."""
    before = await get_cache_size(conn)

    if before <= max_bytes:
        return 0

    removed = await evict_lru_tiles(conn, target_bytes)
    await conn.commit()

    MB = 1024 * 1024
    tasks_logger.info(
        f'Tile cache culled to target {target_bytes // MB} MB: '
        f'{before / MB:.1f} MB -> {(before - removed) / MB:.1f} MB ({removed / MB:.1f} MB evicted)')
    return removed
