import hashlib
import json

from psycopg import AsyncConnection, sql

from backend.constants.map import PIXELS_PER_GRID, get_meters_per_pixel
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.queries.meta_queries import OBSERVATIONS_DATASET
from backend.db.queries.occurrence import create_occurrence_filter_sql
from backend.db.schema.data_metadata import DATA_META_TABLE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.tile_cache import TILE_CACHE
from backend.models.occurrence import OccurrenceFilters


def tile_key(filters: OccurrenceFilters, z: int, x: int, y: int) -> str:
    """32 hex characters identifying one tile's bytes: path (z/x/y) + filters."""

    fields = filters.model_dump(mode='json')   # dates become ISO strings

    for name, value in fields.items():
        # list fields are sets: [a, b] == [b, a]
        if isinstance(value, list):
            fields[name] = sorted(set(value))
    identity = [z, x, y, fields]

    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:32]


def build_tile_query(filters: OccurrenceFilters, z: int, x: int, y: int) -> sql.Composed:
    occurrence_filter = create_occurrence_filter_sql(filters)

    # Get grid size in meters at given zoom level
    grid_size = get_meters_per_pixel(z) * PIXELS_PER_GRID
    # Controls which rows affect cell counts (by expanding past tile edges)
    expand_by = 2 * grid_size

    if z < 11:
        return sql.SQL("""
                WITH
                bbox AS (
                    SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
                ),
                bins AS (
                    SELECT
                        ST_SnapToGrid(geometry_3857, {grid_size}) AS grid_geom,
                        COUNT(*) AS observation_count
                    FROM {occurrence_table}
                    WHERE
                        geometry_3857 && ST_Expand(
                            ST_TileEnvelope({z}, {x}, {y}),
                            {expand_by}
                        )
                        AND {occurrence_filter}
                    GROUP BY ST_SnapToGrid(geometry_3857, {grid_size})
                ),
                bins_geom AS (
                    SELECT
                        ST_SetSRID(
                        ST_MakeEnvelope(
                            ST_X(bins.grid_geom) - ({grid_size} / 2),
                            ST_Y(bins.grid_geom) - ({grid_size} / 2),
                            ST_X(bins.grid_geom) + ({grid_size} / 2),
                            ST_Y(bins.grid_geom) + ({grid_size} / 2)
                        ),
                        3857
                        ) AS geom,
                        bins.observation_count as observation_count
                    FROM bins
                ),
                mvt_geom AS (
                    SELECT
                        ST_AsMVTGeom(bins_geom.geom, bbox.geom, 4096, 64, true) AS geom,
                        bins_geom.observation_count
                    FROM bins_geom, bbox
                )
                SELECT ST_AsMVT(mvt_geom, 'observations-heatmap', 4096, 'geom') FROM mvt_geom;
            """).format(
            include_inat=sql.Literal(filters.include_inat),
            taxon_id=sql.Literal(filters.taxon_ids),
            x=sql.Literal(x),
            y=sql.Literal(y),
            z=sql.Literal(z),
            grid_size=sql.Literal(grid_size),
            expand_by=sql.Literal(expand_by),
            occurrence_table=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter
        )
    # Return point observations if zoomed in
    else:
        return sql.SQL("""
                WITH
                bbox AS (
                    SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
                ),
                obs AS (
                    SELECT 
                        publisher,
                        dataset_key,
                        locality,
                        decimal_latitude,
                        decimal_longitude,
                        accepted_scientific_name,
                        gbif_id,
                        collection_start_date,
                        collection_end_date,
                        geometry_3857
                    FROM {occurrence_table}
                    WHERE
                    {occurrence_filter}
                ),
                mvt_geom AS (
                    SELECT ST_AsMVTGeom(obs.geometry_3857, bbox.geom, 4096, 64, true) AS geom,
                        obs.*
                    FROM obs, bbox
                    WHERE ST_Intersects(obs.geometry_3857, bbox.geom)
                )
                SELECT ST_AsMVT(mvt_geom, 'observations-circles', 4096, 'geom') FROM mvt_geom;
            """).format(
            include_inat=sql.Literal(filters.include_inat),
            taxon_id=sql.Literal(filters.taxon_ids),
            x=sql.Literal(x),
            y=sql.Literal(y),
            z=sql.Literal(z),
            occurrence_table=sql.Identifier(
                GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter
        )


async def get_cached_tile(conn: AsyncConnection, key):
    """
    Returns {'data': bytes | None, 'checked_at': timestamp}.
    data is None on a miss. Pass checked_at to store_tile.
    """

    query = sql.SQL("""
        WITH touch AS (
            UPDATE {tile_cache}
            SET last_used_at = NOW()
            WHERE key = {key} AND last_used_at < NOW() - INTERVAL '1 hour'
        )
        SELECT (SELECT data FROM {tile_cache} WHERE key = {key}) AS data,
               clock_timestamp() AS checked_at
    """).format(tile_cache=sql.Identifier(TILE_CACHE.name), key=sql.Literal(key))

    result = await execute_psql_query(
        conn,
        query,
        dict_cursor=True,
        fetch='one'
    )
    if result is None:
        raise ValueError('get_cached_tile query failed.')
    return result


async def store_tile(conn: AsyncConnection, key, data: bytes, rendered_at, pinned: bool = False):
    """
    Insert or overwrite a tile. `rendered_at` is the checked_at value from before
    rendering began (get_cached_tile).

    In the chance that a render is created before an observations refresh, it will not be inserted.
    """

    query = sql.SQL("""
        INSERT INTO {tile_cache} (key, data, size_bytes, pinned, last_used_at)
        SELECT {key}, {data}, {size_bytes}, {pinned}, NOW()
            WHERE {rendered_at} >= COALESCE(
                (SELECT last_updated_at FROM {meta_table} WHERE dataset_name = {observations_dataset}),
                '-infinity'
            )
        ON CONFLICT (key) DO UPDATE
        SET data = EXCLUDED.data,
            size_bytes = EXCLUDED.size_bytes,
            pinned = EXCLUDED.pinned,
            last_used_at = NOW()
    """).format(
        tile_cache=sql.Identifier(TILE_CACHE.name),
        meta_table=sql.Identifier(DATA_META_TABLE.name),
        key=sql.Literal(key),
        data=sql.Literal(data),
        observations_dataset=sql.Literal(OBSERVATIONS_DATASET),
        size_bytes=sql.Literal(len(data)),
        rendered_at=sql.Literal(rendered_at),
        pinned=sql.Literal(pinned)
    )

    await execute_psql_query(conn, query)


async def get_cache_size(conn: AsyncConnection) -> int:
    """Check total size of tile cache using size_bytes column"""

    query = sql.SQL("""
            SELECT COALESCE(SUM(size_bytes), 0)::bigint
            FROM {tile_cache}
        """).format(tile_cache=sql.Identifier(TILE_CACHE.name))

    result = await execute_psql_query(conn, query, fetch='one')

    if result is None:
        raise RuntimeError("Failed to retrieve tile cache size")

    return result[0]


async def evict_lru_tiles(
    conn: AsyncConnection,
    target_bytes: int,
    rows_in_chunk: int = 100,
) -> int:
    """
    Delete least-recently-used tiles until the cache is at or below target_bytes.
    This function blindly deletes a number of rows dictated by rows_in_chunk, and often overshoot significantly.
    """
    current_bytes = await get_cache_size(conn)

    if current_bytes <= target_bytes:
        return 0

    removed = 0

    while current_bytes - removed > target_bytes:
        query = sql.SQL("""
            DELETE FROM {tile_cache}
            WHERE key IN (
                SELECT key
                FROM {tile_cache}
                WHERE pinned = false
                ORDER BY last_used_at ASC, key ASC
                LIMIT {rows}
                FOR UPDATE SKIP LOCKED
            )
            RETURNING size_bytes
        """).format(
            tile_cache=sql.Identifier(TILE_CACHE.name),
            rows=sql.Literal(rows_in_chunk),
        )

        rows = await execute_psql_query(conn, query, fetch='all') or []

        if not rows:
            # No unpinned tiles remain
            break

        removed += sum(row[0] for row in rows)

    return removed


async def clear_tile_cache(conn: AsyncConnection):
    await execute_psql_query(
        conn, sql.SQL("TRUNCATE {tile_cache}").format(tile_cache=sql.Identifier(TILE_CACHE.name)))
