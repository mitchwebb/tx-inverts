"""
Integration tests for backend.db.queries.tile_cache
(get_cached_tile, store_tile, get_cache_size, evict_lru_tiles, clear_tile_cache)

These run against the real test schema. The behavior under test lives in the
SQL (CTE touch, freshness guard against data_metadata, LRU delete with
SKIP LOCKED), so mocking psycopg would verify nothing.

Assumes setup_gbif_schema creates tile_cache and data_metadata.
"""
from datetime import datetime, timedelta, timezone

import pytest
from psycopg import sql

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.queries.tile_cache import (
    clear_tile_cache,
    evict_lru_tiles,
    get_cache_size,
    get_cached_tile,
    store_tile,
)
from backend.db.schema.data_metadata import DATA_META_TABLE, OBSERVATIONS_DATASET
from backend.db.schema.tile_cache import TILE_CACHE


# Little helper
def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _insert_tile(
    conn,
    key: str,
    data: bytes = b'x' * 100,
    pinned: bool = False,
    last_used_at: datetime | None = None,
):
    """Insert a tile directly, bypassing store_tile's freshness guard."""
    await execute_psql_query(
        conn,
        sql.SQL("""
            INSERT INTO {tile_cache} (key, data, size_bytes, pinned, last_used_at)
            VALUES ({key}, {data}, {size}, {pinned}, {timestamp})
        """).format(
            tile_cache=sql.Identifier(TILE_CACHE.name),
            key=sql.Literal(key),
            data=sql.Literal(data),
            size=sql.Literal(len(data)),
            pinned=sql.Literal(pinned),
            timestamp=sql.Literal(last_used_at or _now()),
        ),
    )


async def _get_row(conn, key: str) -> dict | None:
    """Helper to fetch a row from tile_cache"""
    return await execute_psql_query(
        conn,
        sql.SQL("""
            SELECT key, data, size_bytes, pinned, last_used_at FROM {tile_cache} WHERE key = {key}
        """).format(
            tile_cache=sql.Identifier(TILE_CACHE.name), key=sql.Literal(key)),
        dict_cursor=True,
        fetch='one',
    )


async def _all_keys(conn) -> set[str]:
    """Get list of all keys from tile cache"""
    rows = await execute_psql_query(
        conn,
        sql.SQL("SELECT key FROM {tile_cache}").format(
            tile_cache=sql.Identifier(TILE_CACHE.name)),
        fetch='all',
    )
    return {r[0] for r in rows} if rows else set()


async def _set_observations_updated(conn, ts: datetime, dataset: str = OBSERVATIONS_DATASET):
    await insert_rows(
        [{'dataset_name': dataset, 'last_updated_at': ts}],
        DATA_META_TABLE.name,
        conn,
    )


@pytest.mark.asyncio
class TestGetCachedTile:

    async def test_miss_returns_none_data_and_checked_at(self, setup_gbif_schema, conn):
        """Test that tile cache returns None data for missing tile (with checked_at timestamp)"""
        result = await get_cached_tile(conn, 'missing')
        assert result['data'] is None
        assert isinstance(result['checked_at'], datetime)

    async def test_hit_returns_stored_bytes(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'k1', data=b'tile-bytes')
        result = await get_cached_tile(conn, 'k1')
        assert bytes(result['data']) == b'tile-bytes'

    async def test_stale_last_used_at_is_touched(self, setup_gbif_schema, conn):
        """Make sure that stale tiles get an updated 'last_used_at' when accessed"""
        old = _now() - timedelta(hours=3)
        await _insert_tile(conn, 'k1', last_used_at=old)

        await get_cached_tile(conn, 'k1')

        row = await _get_row(conn, 'k1')
        assert row and row['last_used_at'] > old

    async def test_recent_last_used_at_is_not_touched(self, setup_gbif_schema, conn):
        """Test that the 1 hour throttle avoids a 'last_used_at' update write on every hot-path read."""
        recent = _now() - timedelta(minutes=10)
        await _insert_tile(conn, 'k1', last_used_at=recent)

        await get_cached_tile(conn, 'k1')

        row = await _get_row(conn, 'k1')
        assert row and row['last_used_at'] == recent

    async def test_miss_does_not_create_row(self, setup_gbif_schema, conn):
        await get_cached_tile(conn, 'missing')
        assert await _get_row(conn, 'missing') is None

    async def test_touch_only_affects_requested_key(self, setup_gbif_schema, conn):
        old = _now() - timedelta(hours=3)
        await _insert_tile(conn, 'a', last_used_at=old)
        await _insert_tile(conn, 'b', last_used_at=old)

        await get_cached_tile(conn, 'a')

        row = await _get_row(conn, 'b')
        assert row and row['last_used_at'] == old


@pytest.mark.asyncio
class TestStoreTile:

    async def test_inserts_when_no_observations_metadata(self, setup_gbif_schema, conn):
        """
        If no value for the observations dataset last_update_at (or no value)
        COALESCE falls back to '-infinity', so tile writes are still allowed.
        """

        await store_tile(conn, 'k1', b'abc', _now())

        row = await _get_row(conn, 'k1')
        assert row and bytes(row['data']) == b'abc'

    async def test_size_bytes_matches_data_length(self, setup_gbif_schema, conn):
        await store_tile(conn, 'k1', b'x' * 1234, _now())
        row = await _get_row(conn, 'k1')
        assert row and row['size_bytes'] == 1234

    async def test_pinned_tile_survives_eviction(self, setup_gbif_schema, conn):
        await store_tile(conn, 'pinned', b'x' * 100, _now(), pinned=True)
        await store_tile(conn, 'not pinned', b'x' * 100, _now())

        await evict_lru_tiles(conn, target_bytes=0, rows_in_chunk=1)

        assert await _all_keys(conn) == {'pinned'}

    async def test_pinned_defaults_false(self, setup_gbif_schema, conn):
        await store_tile(conn, 'k1', b'abc', _now())
        row = await _get_row(conn, 'k1')
        assert row and row['pinned'] is False

    async def test_inserts_when_rendered_after_refresh(self, setup_gbif_schema, conn):
        refresh = _now() - timedelta(minutes=5)
        await _set_observations_updated(conn, refresh)

        await store_tile(conn, 'k1', b'abc', _now())

        assert await _get_row(conn, 'k1') is not None

    async def test_rejected_when_rendered_before_refresh(self, setup_gbif_schema, conn):
        """Render began before an observations refresh, so data may be stale—skip."""
        rendered_at = _now() - timedelta(minutes=10)
        await _set_observations_updated(conn, _now())

        await store_tile(conn, 'k1', b'abc', rendered_at)

        assert await _get_row(conn, 'k1') is None

    async def test_conflict_overwrites_data_and_size(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'k1', data=b'old')

        await store_tile(conn, 'k1', b'new-longer-data', _now())

        row = await _get_row(conn, 'k1')
        assert row and bytes(row['data']) == b'new-longer-data'
        assert row['size_bytes'] == len(b'new-longer-data')

    async def test_conflict_refreshes_last_used_at(self, setup_gbif_schema, conn):
        old = _now() - timedelta(days=1)
        await _insert_tile(conn, 'k1', last_used_at=old)

        await store_tile(conn, 'k1', b'new', _now())

        row = await _get_row(conn, 'k1')
        assert row and row['last_used_at'] > old

    async def test_stale_render_does_not_overwrite_existing_tile(self, setup_gbif_schema, conn):
        rendered_at = _now() - timedelta(minutes=10)
        await _insert_tile(conn, 'k1', data=b'existing')
        await _set_observations_updated(conn, _now())

        await store_tile(conn, 'k1', b'stale-render', rendered_at)

        row = await _get_row(conn, 'k1')
        assert row and bytes(row['data']) == b'existing'

    async def test_round_trip_with_get_cached_tile(self, setup_gbif_schema, conn):
        """
        Make sure checked_at from get_cached_tile is properly 
        returned and accepted by store_tile on a fresh dataset.
        """

        miss = await get_cached_tile(conn, 'k1')
        assert miss['data'] is None

        await store_tile(conn, 'k1', b'rendered', miss['checked_at'])

        hit = await get_cached_tile(conn, 'k1')
        assert bytes(hit['data']) == b'rendered'

    async def test_round_trip_rejected_when_refresh_lands_mid_render(self, setup_gbif_schema, conn):
        """Make sure to reject tile stores when refresh commits between check and store."""
        miss = await get_cached_tile(conn, 'k1')
        await _set_observations_updated(conn, _now())

        await store_tile(conn, 'k1', b'rendered', miss['checked_at'])

        assert await _get_row(conn, 'k1') is None


@pytest.mark.asyncio
class TestGetCacheSize:

    async def test_empty_cache_is_zero(self, setup_gbif_schema, conn):
        assert await get_cache_size(conn) == 0

    async def test_sums_size_bytes(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'a', data=b'x' * 100)
        await _insert_tile(conn, 'b', data=b'x' * 250)

        assert await get_cache_size(conn) == 350

    async def test_includes_pinned_tiles(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'a', data=b'x' * 100, pinned=True)
        await _insert_tile(conn, 'b', data=b'x' * 100, pinned=False)

        assert await get_cache_size(conn) == 200

    async def test_returns_int(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'a')
        assert isinstance(await get_cache_size(conn), int)


@pytest.mark.asyncio
class TestEvictLruTiles:

    async def _seed_ordered(self, conn, n: int = 10, size: int = 100, pinned: set[int] | None = None):
        """Many tiles t0 -> t(n-1); t0 is the oldest."""
        base = _now() - timedelta(days=1)
        for i in range(n):
            await _insert_tile(
                conn, f't{i}', data=b'x' * size,
                pinned=i in (pinned or set()),
                last_used_at=base + timedelta(minutes=i),
            )

    async def test_noop_when_under_target(self, setup_gbif_schema, conn):
        await self._seed_ordered(conn, n=3)

        removed = await evict_lru_tiles(conn, target_bytes=1000)

        assert removed == 0
        assert len(await _all_keys(conn)) == 3

    async def test_noop_when_exactly_at_target(self, setup_gbif_schema, conn):
        await self._seed_ordered(conn, n=3)  # 3 tiles of 100 bytes each

        assert await evict_lru_tiles(conn, target_bytes=300) == 0

    async def test_noop_on_empty_cache(self, setup_gbif_schema, conn):
        assert await evict_lru_tiles(conn, target_bytes=0) == 0

    async def test_evicts_oldest_first(self, setup_gbif_schema, conn):
        await self._seed_ordered(conn, n=10)  # 10 tiles of 100 bytes each

        removed = await evict_lru_tiles(conn, target_bytes=500, rows_in_chunk=1)

        assert removed == 500
        assert await _all_keys(conn) == {f't{i}' for i in range(5, 10)}

    async def test_returns_bytes_removed(self, setup_gbif_schema, conn):
        await self._seed_ordered(conn, n=4, size=250)

        removed = await evict_lru_tiles(conn, target_bytes=500, rows_in_chunk=1)

        assert removed == 500
        assert await get_cache_size(conn) == 500

    async def test_large_chunk_overshoots_target(self, setup_gbif_schema, conn):
        """
        Chunk deletes blindly, so a chunk larger than the row count wipes 
        everything even if the target needed only a few rows. This isn't
        perfect, but is quicker than summing values.
        """

        await self._seed_ordered(conn, n=10)

        removed = await evict_lru_tiles(conn, target_bytes=900, rows_in_chunk=100)

        assert removed == 1000
        assert await _all_keys(conn) == set()

    async def test_multiple_chunks_until_target_met(self, setup_gbif_schema, conn):
        "See that evict_lru_tiles evicts in chunks in a loop until target is met"
        await self._seed_ordered(conn, n=10)

        removed = await evict_lru_tiles(conn, target_bytes=300, rows_in_chunk=3)

        # 3 chunks of 3 rows: 1000 -> 700 -> 400 -> 100
        assert removed == 900
        assert await get_cache_size(conn) == 100

    async def test_pinned_tiles_never_evicted(self, setup_gbif_schema, conn):
        await self._seed_ordered(conn, n=5, pinned={0, 1})

        await evict_lru_tiles(conn, target_bytes=0, rows_in_chunk=1)

        assert await _all_keys(conn) == {'t0', 't1'}

    async def test_terminates_when_only_pinned_remain(self, setup_gbif_schema, conn):
        """Loop must break on empty delete, not continue looping."""
        await self._seed_ordered(conn, n=3, pinned={0, 1, 2})

        removed = await evict_lru_tiles(conn, target_bytes=0)

        assert removed == 0
        assert len(await _all_keys(conn)) == 3

    async def test_pinned_older_than_unpinned_is_skipped_not_blocking(self, setup_gbif_schema, conn):
        """When oldest tile is pinned, eviction must proceed to the next-oldest unpinned."""
        await self._seed_ordered(conn, n=4, pinned={0})

        await evict_lru_tiles(conn, target_bytes=200, rows_in_chunk=1)

        assert await _all_keys(conn) == {'t0', 't3'}

    async def test_get_cached_tile_touch_protects_from_eviction(self, setup_gbif_schema, conn):
        """A read on the oldest tile makes it survive."""
        await self._seed_ordered(conn, n=4)  # t0 oldest, all >1h old

        await get_cached_tile(conn, 't0')
        await evict_lru_tiles(conn, target_bytes=100, rows_in_chunk=1)

        assert await _all_keys(conn) == {'t0'}


@pytest.mark.asyncio
class TestClearTileCache:

    async def test_removes_all_tiles(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'a')
        await _insert_tile(conn, 'b')

        await clear_tile_cache(conn)

        assert await _all_keys(conn) == set()
        assert await get_cache_size(conn) == 0

    async def test_removes_pinned_tiles(self, setup_gbif_schema, conn):
        await _insert_tile(conn, 'a', pinned=True)

        await clear_tile_cache(conn)

        assert await _all_keys(conn) == set()

    async def test_noop_on_empty_cache(self, setup_gbif_schema, conn):
        await clear_tile_cache(conn)
        assert await get_cache_size(conn) == 0
