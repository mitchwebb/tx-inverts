import pandas as pd
import pytest
from backend.jobs.tasks.taxon_tasks import update_ns_ranks, fill_invasives_table, update_invasives, _ensure_rank_columns, _replace_backbone, update_backbone
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.conftest import insert_rows

import datetime


class TestUpdateNSRanks:
    @pytest.mark.asyncio
    async def test_filters_constructed_correctly(self, mocker):
        captured_filters = []

        # Mock calculate_ns_values call
        async def fake_calculate_ns_values(conn, filters):
            captured_filters.append(filters)
            return None

        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.ns.calculate_ns_values',
            side_effect=fake_calculate_ns_values,
        )
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.execute_psql_query',
            new=mocker.AsyncMock(
                side_effect=[{"exists": 1}, {"exists": 1},
                             [{"taxon_id": '42'}], None]
            ),
        )
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.refresh_materialized_view',
            new=mocker.AsyncMock(),
        )

        await update_ns_ranks(mocker.AsyncMock(), taxon_keys=['42'])

        # Check to make sure our default values are being used when calculating
        assert len(captured_filters) == 2
        for f in captured_filters:
            assert f.taxon_ids == [42]  # Mock value
            assert f.coord_uncertainty == 1000
            assert f.include_invasives is False
            assert f.date_start == datetime.date(1800, 1, 1)
        assert {f.include_inat for f in captured_filters} == {True, False}

    @pytest.mark.asyncio
    async def test_adds_missing_columns(self, setup_gbif_schema, conn, mocker):
        mocker.patch.object(conn, 'commit', new=mocker.AsyncMock())

        async with conn.transaction(force_rollback=True):
            await conn.execute(sql.SQL("""
                ALTER TABLE {backbone}
                DROP COLUMN IF EXISTS ns_rank_state CASCADE,
                DROP COLUMN IF EXISTS ns_rank_state_no_inat CASCADE
            """).format(backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)))

            await _ensure_rank_columns(conn)

            result = await execute_psql_query(
                conn,
                sql.SQL("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = {t} AND column_name IN ('ns_rank_state', 'ns_rank_state_no_inat')
                """).format(t=sql.Literal(GBIF_INVERTS_BACKBONE.name)),
                fetch='all', dict_cursor=True,
            )
            assert result
            found = {r['column_name'] for r in result}
            assert found == {'ns_rank_state', 'ns_rank_state_no_inat'}

    @pytest.mark.asyncio
    async def test_updates_rank_for_specified_taxon(self, setup_gbif_schema, occurrence_filter_data):
        conn = occurrence_filter_data
        await update_ns_ranks(conn, taxon_keys=['5035741'])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state, ns_rank_state_no_inat
                FROM {backbone} WHERE taxon_id = %s
            """).format(backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)),
            params=('5035741',), fetch='one', dict_cursor=True,
        )

        assert result
        assert result['ns_rank_state'] is not None
        assert result['ns_rank_state_no_inat'] is not None

    @pytest.mark.asyncio
    async def test_include_inat_changes_the_rank(self, occurrence_filter_data, tx_bounding_box):
        # gbif_id=2 (taxon 5035741) is iNaturalist-origin — excluding it should
        # change occurrence count / extent enough to differ from the with-inat rank.
        conn = occurrence_filter_data
        await update_ns_ranks(conn, taxon_keys=['5035741'])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state, ns_rank_state_no_inat
                FROM {backbone} WHERE taxon_id = %s
            """).format(backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)),
            params=('5035741',), fetch='one', dict_cursor=True,
        )

        assert result
        assert result['ns_rank_state'] != result['ns_rank_state_no_inat']

    @pytest.mark.asyncio
    async def test_only_species_rows_get_ranked(self, occurrence_filter_data):
        # Formicidae (4342) is taxon_rank='family' — the UPDATE's
        # WHERE ... AND taxon_rank = 'species' clause must exclude it.
        conn = occurrence_filter_data
        await update_ns_ranks(conn, taxon_keys=['4342'])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state FROM {backbone} WHERE taxon_id = %s
            """).format(backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)),
            params=('4342',), fetch='one', dict_cursor=True,
        )

        assert result
        assert result['ns_rank_state'] is None

    @pytest.mark.asyncio
    async def test_no_matching_taxa_returns_without_error(self, occurrence_filter_data):
        conn = occurrence_filter_data
        await update_ns_ranks(conn, taxon_keys=['999999999'])  # no such taxon

    @pytest.mark.asyncio
    async def test_rolls_back_and_reraises_on_failure(self, mocker):
        conn = mocker.AsyncMock()
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks._ensure_rank_columns",
            side_effect=RuntimeError("boom"),
        )

        with pytest.raises(RuntimeError, match="boom"):
            await update_ns_ranks(conn, taxon_keys=['1'])

        conn.rollback.assert_awaited_once()


class TestCreateInvasivesTable:
    @pytest.mark.asyncio
    async def test_loads_data(
        self, setup_gbif_schema, conn, mocker
    ):
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.get_invasives_dataset',
            new=mocker.AsyncMock(return_value='/tmp/fake_occurrence.txt'),
        )

        # We can safely assume this shape for the invasives dataset output,
        # given our testing of prep_invasives_dataset
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.prep_invasives_dataset',
            new=mocker.AsyncMock(return_value=pd.DataFrame([{
                'taxon_id': 1,
                'scientific_name': 'Animalia',
                'kingdom': 'Animalia',
                'phylum': None,
                'class': None,
                'order': None,
                'family': None,
                'taxon_rank': 'kingdom',
                'scientific_name_authorship': 'test',
                'vernacular_name': 'Animalia',
                'taxonomic_status': 'accepted',
                'taxon_remarks': None,
                'license': None,
                'rights_holder': None,
                'bibliographic_citation': None,
                'references': None,
                'institution_code': None,
                'dataset_id': 'fb60bbd0-205f-4ffe-9a5b-1c97de7af8aa',
                'dataset_name': 'test_dataset',
                'taxon_id_link': None,
            }]))
        )

        await fill_invasives_table(conn)

        result = await execute_psql_query(
            conn,
            sql.SQL(
                "SELECT * FROM {t}").format(t=sql.Identifier(US_INVASIVES_TABLE.name)),
            fetch='all', dict_cursor=True,
        )
        assert result
        assert len(result) == 1  # matches however many rows are fed in

        # Now with empty df
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.prep_invasives_dataset',
            new=mocker.AsyncMock(return_value=pd.DataFrame([]))
        )
        # With truncate=True, table should be truncated
        await fill_invasives_table(conn, truncate=True)
        # Now, with no records to add, table should be empty
        result = await execute_psql_query(
            conn,
            sql.SQL(
                "SELECT * FROM {t}").format(t=sql.Identifier(US_INVASIVES_TABLE.name)),
            fetch='all', dict_cursor=True,
        )
        assert result is not None
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_exception_raises(self, conn, mocker):
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.get_invasives_dataset',
            new=mocker.AsyncMock(
                side_effect=RuntimeError('big huge network error')),
        )
        mocker.patch('backend.jobs.tasks.taxon_tasks.db_logger')
        with pytest.raises(Exception):
            await fill_invasives_table(conn)


class TestUpdateInvasives:
    @pytest.mark.asyncio
    async def test_flags_invasives(self, conn, occurrence_filter_data):
        # ID of species in occurrence_filter_data fixture
        taxon_id = 5035741

        await insert_rows(
            [{
                'taxon_id': taxon_id,
                'scientific_name': 'Animalia',
                'kingdom': 'Animalia',
                'phylum': None,
                'class': None,
                'order': None,
                'family': None,
                'taxon_rank': 'kingdom',
                'scientific_name_authorship': 'test',
                'vernacular_name': 'Animalia',
                'taxonomic_status': 'accepted',
                'taxon_remarks': None,
                'license': None,
                'rights_holder': None,
                'bibliographic_citation': None,
                'references': None,
                'institution_code': None,
                'dataset_id': 'fb60bbd0-205f-4ffe-9a5b-1c97de7af8aa',
                'dataset_name': 'test_dataset',
                'taxon_id_link': None,
            }],
            US_INVASIVES_TABLE.name,
            conn
        )

        await update_invasives(conn)

        get_invasive_query = sql.SQL("""
            SELECT us_invasive FROM {taxa_table}
            WHERE taxon_id = {taxon_id}
        """).format(
            taxa_table=sql.Identifier(TX_TAXA_TABLE.name),
            taxon_id=sql.Literal(taxon_id)
        )
        result = await execute_psql_query(conn, get_invasive_query, fetch='one')
        assert result and result[0] == True

    @pytest.mark.asyncio
    async def test_clears_non_invasives(self, conn, occurrence_filter_data):
        taxon_id = 5035741

        set_invasive_query = sql.SQL("""
            UPDATE {full_taxa_table}
            SET us_invasive = true
            WHERE taxon_id = {taxon_id}
        """).format(
            full_taxa_table=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            taxon_id=sql.Literal(taxon_id)
        )
        await execute_psql_query(conn, set_invasive_query)
        # Update tx_taxa
        await refresh_materialized_view(conn, TX_TAXA_TABLE.name)

        # Taxon should be marked as invasive
        get_invasive_query = sql.SQL("""
            SELECT us_invasive FROM {taxa_table}
            WHERE taxon_id = {taxon_id}
        """).format(
            taxa_table=sql.Identifier(TX_TAXA_TABLE.name),
            taxon_id=sql.Literal(taxon_id)
        )
        result = await execute_psql_query(conn, get_invasive_query, fetch='one')
        assert result and result[0] == True

        # Run update_invasives with no invasives
        await update_invasives(conn)
        # Now our taxon should be listed as non-invasive
        result = await execute_psql_query(conn, get_invasive_query, fetch='one')
        assert result and result[0] is False

    @pytest.mark.asyncio
    async def test_raises_on_exception(self, conn, mocker):
        mocker.patch(
            'backend.jobs.tasks.taxon_tasks.execute_psql_query',
            new=mocker.AsyncMock(
                side_effect=RuntimeError('big huge network error')),
        )
        with pytest.raises(RuntimeError):
            await update_invasives(conn)


@pytest.fixture
async def temp_backbone_table(conn):
    temp_table_name = 'temp_test_backbone'
    await execute_psql_query(conn, sql.SQL(
        "CREATE TEMP TABLE {temp} (LIKE {backbone} INCLUDING DEFAULTS)"
    ).format(
        temp=sql.Identifier(temp_table_name),
        backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
    ))

    async def _insert(**overrides):
        taxon_id = overrides.get('taxon_id', 5555555)
        row = {
            'scientific_name': 'test taxon',
            'canonical_name': 'test taxon',
            'taxon_id': taxon_id,
            'accepted_name_usage_id': taxon_id,
            'parent_name_usage_id': None,
            'taxon_rank': 'species',
            'us_invasive': True,
            'taxonomic_status': 'accepted',
            **overrides,
        }
        columns = list(row.keys())
        values = list(row.values())
        insert_query = sql.SQL(
            "INSERT INTO {temp} ({cols}) VALUES ({placeholders})"
        ).format(
            temp=sql.Identifier(temp_table_name),
            cols=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )
        await execute_psql_query(conn, insert_query, values)
        return row

    return temp_table_name, _insert


class TestReplaceBackbone:
    @pytest.mark.asyncio
    async def test_backbone_fully_replaced(self, conn, occurrence_filter_data, temp_backbone_table):
        select_query = sql.SQL(
            "SELECT * FROM {backbone}"
        ).format(backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name))

        pre_rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )
        assert pre_rows

        pre_ids = {r['taxon_id'] for r in pre_rows}
        assert 5555555 not in pre_ids
        assert len(pre_ids) > 0

        temp_table_name, insert_row = temp_backbone_table
        await insert_row(taxon_id=5555555)

        await _replace_backbone(conn, temp_table_name)

        post_rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )
        assert post_rows

        post_ids = {r['taxon_id'] for r in post_rows}
        # Old rows are gone and new ones are added
        assert pre_ids.isdisjoint(post_ids)
        assert post_ids == {5555555}

    @pytest.mark.asyncio
    async def test_materialized_views_populated_after_replace(self, conn, setup_gbif_schema, temp_backbone_table):
        temp_table_name, insert_row = temp_backbone_table
        await insert_row(taxon_id=5555557)

        await insert_rows(
            rows=[
                {
                    'gbif_id': 1,
                    'taxon_key': 5555557,
                    'accepted_taxon_key': 5555557,
                    'collection_start_date': '2020-03-04',
                    'collection_end_date': '2020-03-05',
                    'kingdom_key': 1,
                    'family_key': None,
                    'genus_key': None,
                    'species_key': 5555557,
                    'dataset_key': 'dataset-a',
                    'institution_code': 'TxState',
                    'coordinate_uncertainty_in_meters': 100,
                    'geometry': 'POINT(-97.7431 30.2672)'
                },
            ],
            table_name=GBIF_OBSERVATIONS_TABLE.name,
            conn=conn
        )

        await insert_rows(
            rows=[
                {
                    'observation_id': 1,
                    'region_id': '435ebf14-5173-466c-8afb-32ddaaa3b253',
                    'region_type': 'county'
                }
            ],
            table_name=OBSERVATION_REGIONS_TABLE.name,
            conn=conn
        )

        await _replace_backbone(conn, temp_table_name)

        # Check that tx_taxa gets refreshed with new information
        tx_taxa_query = sql.SQL(
            "SELECT * FROM {tx_taxa} WHERE taxon_id = {taxon_id}"
        ).format(
            tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
            taxon_id=sql.Literal(5555557)
        )
        tx_taxa_rows = await execute_psql_query(
            conn, tx_taxa_query, fetch='all', dict_cursor=True
        )
        assert tx_taxa_rows

        # Check that taxon_presence_table is refreshed with new information
        region_presence_query = sql.SQL(
            "SELECT * FROM {presence_table} WHERE accepted_taxon_key={taxon_id}"
        ).format(
            presence_table=sql.Identifier(TAXON_PRESENCE_TABLE.name),
            taxon_id=sql.Literal(5555557)
        )
        region_presence_rows = await execute_psql_query(
            conn, region_presence_query, fetch='all', dict_cursor=True
        )
        assert region_presence_rows


class TestUpdateBackbone:
    @pytest.mark.asyncio
    async def test_update_backbone_fetches_backbone(self, mocker, conn):
        # Keep an eye on the fetch call
        fetch_backbone = mocker.patch(
            "backend.jobs.tasks.taxon_tasks._fetch_backbone",
            new=mocker.AsyncMock(return_value='na'),
        )
        # Patch to error out of the function early
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.pd.read_csv",
            side_effect=RuntimeError,
        )

        with pytest.raises(RuntimeError):
            await update_backbone(conn)

        fetch_backbone.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_backbone_skips_fetch(self, mocker, conn, tmp_path):
        # Make a little fake tsv
        fp = tmp_path / "backbone.tsv"
        fp.write_text("id\n1\n")

        # Keep an eye on the fetch call
        fetch_backbone = mocker.patch(
            "backend.jobs.tasks.taxon_tasks._fetch_backbone",
            new=mocker.AsyncMock(return_value=str(fp)),
        )
        # Patch to error out of the function early
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.pd.read_csv",
            side_effect=RuntimeError,
        )

        with pytest.raises(RuntimeError):
            await update_backbone(conn, fp)

        fetch_backbone.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_backbone_rolls_back_on_error(self, mocker, conn):
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.pd.read_csv",
            side_effect=RuntimeError,
        )
        rollback = mocker.patch.object(
            conn, "rollback", new=mocker.AsyncMock()
        )
        commit = mocker.patch.object(
            conn, "commit", new=mocker.AsyncMock()
        )

        with pytest.raises(RuntimeError):
            await update_backbone(conn, fp="unused")

        rollback.assert_awaited_once()
        commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_backbone_end_to_end(self, conn, setup_gbif_schema, tmp_path):
        # Create simple test row
        fp = tmp_path / "backbone.tsv"
        fp.write_text(
            "taxonID\tscientificName\tkingdom\tphylum\tclass\ttaxonRank\tspecificEpithet\tinfraspecificEpithet\n"
            "5555558\tTurris invicta\tAnimalia\tMollusca\tGastropoda\tspecies\tTurris\tinvicta"
        )

        # Use test row for update
        await update_backbone(conn, fp=str(fp))

        # Attempt to select taxon from test row
        select_query = sql.SQL("SELECT * FROM {backbone} WHERE taxon_id = {taxon_id}").format(
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            taxon_id=sql.Literal('5555558')
        )
        rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )
        # Assert that a row was selected
        assert rows
