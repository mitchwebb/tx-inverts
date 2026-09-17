import uuid

import pandas as pd
import pytest
import pytest_asyncio
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.jobs.tasks.taxon_tasks import update_ns_ranks, fill_invasives_table, update_invasives, _ensure_rank_columns, _replace_backbone, update_backbone, fill_vernacular_names_table
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.vernacular_names import VERNACULAR_NAMES_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import sql
from backend.conftest import insert_rows

import datetime

# Region UUIDs — fixed and readable so test assertions can reference them
# without recomputing anything at read time
REGION_A_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
REGION_B_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')

taxa = [
    {
        # non-invasive species, matches family 4342 for lineage/ancestor tests
        'scientific_name': 'Atta texana',
        'canonical_name': 'Atta texana',
        'taxon_id': 5035741,
        'accepted_name_usage_id': 5035741,
        'parent_name_usage_id': 4342,
        'taxon_rank': 'species',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
    },
    {
        # family row — required for taxon_lineage to resolve ancestor_id=4342
        # when a test filters by family-level taxon_id
        'scientific_name': 'Formicidae',
        'canonical_name': 'Formicidae',
        'taxon_id': 4342,
        'accepted_name_usage_id': 4342,
        'parent_name_usage_id': 1,
        'taxon_rank': 'family',
        'us_invasive': False,
        'taxonomic_status': 'accepted'
    },
    {
        # invasive species, same family — exercises include_invasives branches
        'scientific_name': 'Solenopsis invicta',
        'canonical_name': 'Solenopsis invicta',
        'taxon_id': 9999001,
        'accepted_name_usage_id': 9999001,
        'parent_name_usage_id': 4342,
        'taxon_rank': 'species',
        'us_invasive': True,
        'taxonomic_status': 'accepted'
    },
]

occ = [
    {
        # baseline row — passes every filter at defaults
        'gbif_id': 1, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2020-03-04', 'collection_end_date': '2020-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',  # Austin, TX
    },
    {
        # iNaturalist origin — tests include_inat=False exclusion
        'gbif_id': 2, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2021-03-04', 'collection_end_date': '2021-03-05',
        'dataset_key': 'dataset-b', 'institution_code': 'iNaturalist',
        'coordinate_uncertainty_in_meters': 50,
        # Dallas, TX — far enough to swing extent if included
        'geometry': 'POINT(-96.7970 32.7767)',
    },
    {
        # collection_start_date NULL — tests hardcoded IS NOT NULL clause
        'gbif_id': 3, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': None, 'collection_end_date': None,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # second dataset_key, distinct date, tagged to REGION_B_ID
        'gbif_id': 4, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2019-03-04', 'collection_end_date': '2019-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': None,  # tests "IS NULL OR <=" branch
        'geometry': 'POINT(-95.3698 29.7604)',  # Houston, TX
    },
    {
        # coordinate_uncertainty_in_meters == 0 — tests `is None` vs falsy bug
        'gbif_id': 5, 'taxon_key': 5035741, 'accepted_taxon_key': 5035741,
        'collection_start_date': '2022-01-01', 'collection_end_date': '2022-01-02',
        'dataset_key': 'dataset-b', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 0,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # invasive taxon — tests include_invasives true/false branches
        'gbif_id': 6, 'taxon_key': 9999001, 'accepted_taxon_key': 9999001,
        'collection_start_date': '2022-06-01', 'collection_end_date': '2022-06-02',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
]

observation_regions = [
    {'observation_id': 1, 'region_id': REGION_A_ID},
    {'observation_id': 4, 'region_id': REGION_B_ID},
]


@pytest_asyncio.fixture()
async def occurrence_filter_data(conn):
    """
    Minimal shared dataset covering every branch in
    create_occurrence_filter_sql and create_occurrence_taxon_filter.
    """
    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)
    await insert_rows(observation_regions, OBSERVATION_REGIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)

    return conn


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
            assert f.taxon_ids == ['42']  # Mock value
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
        taxon_id = '5035741'
        await update_ns_ranks(conn, taxon_keys=[taxon_id])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state, ns_rank_state_no_inat
                FROM {backbone} WHERE taxon_id = {taxon_id}
            """).format(
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                taxon_id=sql.Literal(taxon_id)
            ), fetch='one', dict_cursor=True,
        )

        assert result
        assert result['ns_rank_state'] is not None
        assert result['ns_rank_state_no_inat'] is not None

    @pytest.mark.asyncio
    async def test_include_inat_changes_the_rank(self, occurrence_filter_data, tx_bounding_box):
        # gbif_id=2 (taxon 5035741) is iNaturalist-origin — excluding it should
        # change occurrence count / extent enough to differ from the with-inat rank.
        conn = occurrence_filter_data
        taxon_id = '5035741'
        await update_ns_ranks(conn, taxon_keys=[taxon_id])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state, ns_rank_state_no_inat
                FROM {backbone} WHERE taxon_id = {taxon_id}
            """).format(
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                taxon_id=sql.Literal(taxon_id)
            ), fetch='one', dict_cursor=True,
        )

        assert result
        assert result['ns_rank_state'] != result['ns_rank_state_no_inat']

    @pytest.mark.asyncio
    async def test_only_species_rows_get_ranked(self, occurrence_filter_data):
        # Formicidae (4342) is taxon_rank='family' — the UPDATE's
        # WHERE ... AND taxon_rank = 'species' clause must exclude it.
        conn = occurrence_filter_data
        taxon_id = '4342'
        await update_ns_ranks(conn, taxon_keys=[taxon_id])

        result = await execute_psql_query(
            conn,
            sql.SQL("""
                SELECT ns_rank_state FROM {backbone} WHERE taxon_id = {taxon_id}
            """).format(
                backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
                taxon_id=sql.Literal(taxon_id)
            ), fetch='one', dict_cursor=True,
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
        taxon_id = '5035741'

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
        taxon_id = '5035741'

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
        assert 'FRESHTAX' not in pre_ids
        assert len(pre_ids) > 0

        temp_table_name, insert_row = temp_backbone_table
        await insert_row(taxon_id='FRESHTAX')

        await _replace_backbone(conn, temp_table_name)

        post_rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )
        assert post_rows

        post_ids = {r['taxon_id'] for r in post_rows}
        # Old rows are gone and new ones are added
        assert pre_ids.isdisjoint(post_ids)
        assert post_ids == {'FRESHTAX'}

    @pytest.mark.asyncio
    async def test_materialized_views_populated_after_replace(self, conn, setup_gbif_schema, temp_backbone_table):
        temp_table_name, insert_row = temp_backbone_table
        await insert_row(taxon_id='TESTTAX')

        await insert_rows(
            rows=[
                {
                    'gbif_id': 1,
                    'taxon_key': 'TESTTAX',
                    'accepted_taxon_key': 'TESTTAX',
                    'collection_start_date': '2020-03-04',
                    'collection_end_date': '2020-03-05',
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
            taxon_id=sql.Literal('TESTTAX')
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
            taxon_id=sql.Literal('TESTTAX')
        )
        region_presence_rows = await execute_psql_query(
            conn, region_presence_query, fetch='all', dict_cursor=True
        )
        assert region_presence_rows


class TestUpdateBackbone:
    @pytest.mark.asyncio
    async def test_update_backbone_fetches_backbone(self, mocker, conn):
        # Patch backbone version check to initiate update
        fetch_backbone = mocker.patch(
            "backend.jobs.tasks.taxon_tasks.check_backbone_is_current",
            new=mocker.AsyncMock(return_value=False),
        )
        # Keep an eye on the fetch call
        fetch_backbone = mocker.patch(
            "backend.jobs.tasks.taxon_tasks._fetch_backbone",
            new=mocker.Mock(return_value=('', '', '')),
        )
        # Patch to error out of the function early
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.pd.read_csv",
            side_effect=RuntimeError,
        )

        with pytest.raises(RuntimeError):
            await update_backbone(conn)

        fetch_backbone.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_backbone_rolls_back_on_error(self, mocker, conn):
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.check_backbone_is_current",
            side_effect=RuntimeError,
        )
        rollback = mocker.patch.object(
            conn, "rollback", new=mocker.AsyncMock()
        )
        commit = mocker.patch.object(
            conn, "commit", new=mocker.AsyncMock()
        )

        with pytest.raises(RuntimeError):
            await update_backbone(conn)

        rollback.assert_awaited_once()
        commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_backbone_end_to_end(self, conn, setup_gbif_schema, tmp_path, mocker):
        # Create simple test row
        fp = tmp_path / "backbone.tsv"
        fp.write_text(
            "taxonID\tscientificName\tkingdom\tphylum\tclass\ttaxonRank\tgenericName\tinfragenericEpithet\tspecificEpithet\tinfraspecificEpithet\n"
            "TURRISINV\tTurris invicta\tAnimalia\tMollusca\tGastropoda\tspecies\tTurris\tNull\tinvicta\tNull"
        )

        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.check_backbone_is_current",
            new=mocker.AsyncMock(return_value=False),
        )
        mocker.patch(
            "backend.jobs.tasks.taxon_tasks._fetch_backbone",
            new=mocker.Mock(return_value=(str(fp), None, "test-doi")),
        )

        mocker.patch(
            "backend.jobs.tasks.taxon_tasks.fill_vernacular_names_table",
            new=mocker.AsyncMock(),
        )

        # Use test row for update
        await update_backbone(conn)

        # Attempt to select taxon from test row
        select_query = sql.SQL("SELECT * FROM {backbone} WHERE taxon_id = {taxon_id}").format(
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            taxon_id=sql.Literal('TURRISINV')
        )
        rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )
        # Assert that a row was selected
        assert rows


class TestFillVernacularNamesTable:
    async def test_filters_to_eng_and_spa(self, conn, tmp_path):
        # Create simple test row
        fp = tmp_path / "vernacular.tsv"

        # Test tsv with an english name, a spanish name, and a german name for one species,
        # and an english name for another
        fp.write_text(
            "dwc:taxonID\tdwc:vernacularName\tdcterms:language\n"
            "AABBCC\tlittle critter\teng\n"
            "AABBCC\tbichito\tspa\n"
            "AABBCC\ttierchen\tger\n"
            "AABBDD\tbig critter\teng\n"
        )

        await fill_vernacular_names_table(conn, fp)

        select_query = sql.SQL("SELECT * FROM {vernacular_names}").format(
            vernacular_names=sql.Identifier(VERNACULAR_NAMES_TABLE.name))

        rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )

        assert rows
        languages = {row['language'] for row in rows}
        assert languages == {'eng', 'spa'}
        assert 'ger' not in languages

        # Double check and verify that German vernacular name was filtered out
        vernacular_names = {row['vernacular_name'] for row in rows}
        assert 'tierchen' not in vernacular_names

    async def test_truncates_old_data(self, conn, tmp_path):
        # Insert some values to imitate the table already having data
        insert_query = sql.SQL("""
            INSERT INTO {vernacular_names} (taxon_id, language, vernacular_name)
                VALUES ('AABBCC', 'eng', 'stale data')
            """).format(vernacular_names=sql.Identifier(VERNACULAR_NAMES_TABLE.name))

        await execute_psql_query(conn, insert_query, fetch=None)

        select_query = sql.SQL("SELECT * FROM {vernacular_names}").format(
            vernacular_names=sql.Identifier(VERNACULAR_NAMES_TABLE.name))

        rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )

        assert rows
        assert rows[0]['vernacular_name'] == 'stale data'

        # Create simple test row
        fp = tmp_path / "vernacular.tsv"

        fp.write_text(
            "dwc:taxonID\tdwc:vernacularName\tdcterms:language\n"
            "AABBDD\tfresh data\teng\n"
        )

        await fill_vernacular_names_table(conn, fp)

        rows = await execute_psql_query(
            conn, select_query, fetch='all', dict_cursor=True
        )

        assert rows
        assert len(rows) == 1
        assert rows[0]['vernacular_name'] == 'fresh data'
