"""
Integration tests for backend.sql.occurrence_filters
(create_occurrence_taxon_filter, create_occurrence_filter_sql)

These exercise the composed SQL against the real test schema rather than
mocking psycopg's sql.Composed output, since the whole point of these
functions is the SQL they produce actually being correct against real
tables (gbif_observations, taxon_lineage, tx_taxa, observation_regions).
"""
import uuid

import pytest
from psycopg import sql
import pytest_asyncio

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.queries.occurrence import (
    create_occurrence_filter_sql,
    create_occurrence_taxon_filter,
)
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.models.occurrence import OccurrenceFilters


# Shared fixture data
#
# Backbone shape used across these tests:
#
#   FORM_SUPER   (superfamily "Formicoidea", no observations at this rank directly)
#     └── HYM_FAM (family "Formicidae")
#           └── ATTA (genus Atta)
#                 └── ATTATX (species Atta texana)                [obs: 1]
#                       └── ATTASUB (subspecies Atta texana falseyi) [obs: 3]
#                             └── ATTAFRM (form Atta texana f. formi) [obs: 7]
#
#   ATTASYN (species Trachymyrmex cowboyii, SYNONYM of ATTASUB)     [obs: 4]
#   WILDCRD (family Madeitupidae, no invert relation to Atta)       [obs: 5]
#   INV0001 (species, us_invasive = true)                           [obs: 10]

# Region UUIDs — fixed and readable so test assertions can reference them
# without recomputing anything at read time
REGION_A_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
REGION_B_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    # Values to insert into backbone table, then brought into tx_taxa mat view
    taxa = [
        {'scientific_name': 'Formicoidea', 'canonical_name': 'Formicoidea',
         'parent_name_usage_id': 'HYM', 'taxon_id': 'FORM_SUPER',
         'accepted_name_usage_id': None, 'taxon_rank': 'superfamily',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        {'scientific_name': 'Formicidae', 'canonical_name': 'Formicidae',
         'parent_name_usage_id': 'FORM_SUPER', 'taxon_id': 'HYM_FAM',
         'accepted_name_usage_id': None, 'taxon_rank': 'family',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        {'scientific_name': 'Atta', 'canonical_name': 'Atta',
         'parent_name_usage_id': 'HYM_FAM', 'taxon_id': 'ATTA',
         'accepted_name_usage_id': None, 'taxon_rank': 'genus',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        {'scientific_name': 'Atta texana', 'canonical_name': 'Atta texana',
         'parent_name_usage_id': 'ATTA', 'taxon_id': 'ATTATX',
         'accepted_name_usage_id': 'ATTATX', 'taxon_rank': 'species',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        {'scientific_name': 'Atta texana falseyi', 'canonical_name': 'Atta texana falseyi',
         'parent_name_usage_id': 'ATTATX', 'taxon_id': 'ATTASUB',
         'accepted_name_usage_id': 'ATTASUB', 'taxon_rank': 'subspecies',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        {'scientific_name': 'Atta texana f. formi', 'canonical_name': 'Atta texana f. formi',
         'parent_name_usage_id': 'ATTASUB', 'taxon_id': 'ATTAFRM',
         'accepted_name_usage_id': 'ATTAFRM', 'taxon_rank': 'form',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        # Synonym pointing at the subspecies as its accepted usage
        {'scientific_name': 'Trachymyrmex cowboyii', 'canonical_name': 'Trachymyrmex cowboyii',
         'parent_name_usage_id': 'ATTA', 'taxon_id': 'ATTASYN',
         'accepted_name_usage_id': 'ATTASUB', 'taxon_rank': 'species',
         'us_invasive': False, 'taxonomic_status': 'synonym'},

        # Unrelated family, used to prove lineage filter excludes non-descendants
        {'scientific_name': 'Madeitupidae', 'canonical_name': 'Madeitupidae',
         'parent_name_usage_id': 'HYM', 'taxon_id': 'WILDCRD',
         'accepted_name_usage_id': None, 'taxon_rank': 'family',
         'us_invasive': False, 'taxonomic_status': 'accepted'},

        # Flagged invasive, sibling species under Atta
        {'scientific_name': 'Atta invasiva', 'canonical_name': 'Atta invasiva',
         'parent_name_usage_id': 'ATTA', 'taxon_id': 'INV0001',
         'accepted_name_usage_id': 'INV0001', 'taxon_rank': 'species',
         'us_invasive': True, 'taxonomic_status': 'accepted'},
    ]

    occ = [
        # 1: Direct species observation
        {'gbif_id': 1, 'taxon_key': 'ATTATX', 'accepted_taxon_key': 'ATTATX',
         'collection_start_date': '2021-03-04', 'collection_end_date': '2021-03-04',
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': 50},

        # 3: Direct subspecies observation
        {'gbif_id': 3, 'taxon_key': 'ATTASUB', 'accepted_taxon_key': 'ATTASUB',
         'collection_start_date': '2023-03-04', 'collection_end_date': '2023-03-04',
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': None},

        # 4: Observed under a synonym taxon_key, resolved to the subspecies
        {'gbif_id': 4, 'taxon_key': 'ATTASYN', 'accepted_taxon_key': 'ATTASUB',
         'collection_start_date': '2024-03-04', 'collection_end_date': '2024-03-04',
         'institution_code': 'iNaturalist', 'dataset_key': 'DS_B',
         'coordinate_uncertainty_in_meters': 5000},

        # 5: Unrelated family, must never match Atta-rooted taxon_ids
        {'gbif_id': 5, 'taxon_key': 'WILDCRD', 'accepted_taxon_key': 'WILDCRD',
         'collection_start_date': '2025-03-04', 'collection_end_date': '2025-03-04',
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': None},

        # 7: Form-level observation, child of subspecies ATTASUB
        {'gbif_id': 7, 'taxon_key': 'ATTAFRM', 'accepted_taxon_key': 'ATTAFRM',
         'collection_start_date': '2026-03-04', 'collection_end_date': '2026-03-04',
         'institution_code': 'TxCol', 'dataset_key': 'DS_B',
         'coordinate_uncertainty_in_meters': None},

        # 8: No collection_start_date -- must always be excluded
        {'gbif_id': 8, 'taxon_key': 'ATTATX', 'accepted_taxon_key': 'ATTATX',
         'collection_start_date': None, 'collection_end_date': None,
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': None},

        # 9: Coordinate uncertainty above any threshold we'll test
        {'gbif_id': 9, 'taxon_key': 'ATTATX', 'accepted_taxon_key': 'ATTATX',
         'collection_start_date': '2021-06-01', 'collection_end_date': '2021-06-01',
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': 100000},

        # 10: Invasive species, under Atta genus
        {'gbif_id': 10, 'taxon_key': 'INV0001', 'accepted_taxon_key': 'INV0001',
         'collection_start_date': '2021-07-01', 'collection_end_date': '2021-07-01',
         'institution_code': 'TxCol', 'dataset_key': 'DS_A',
         'coordinate_uncertainty_in_meters': None},
    ]

    observation_regions = [
        {'observation_id': 1, 'region_id': REGION_A_ID},
        {'observation_id': 4, 'region_id': REGION_B_ID},
    ]

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)
    await insert_rows(observation_regions, OBSERVATION_REGIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)


async def _run_filter(conn, filters: OccurrenceFilters, skip_taxa: bool = False) -> set[int]:
    """Create the filter, run it against gbif_observations, return matching gbif_ids."""
    clause = create_occurrence_filter_sql(filters, skip_taxa=skip_taxa)
    query = sql.SQL("SELECT gbif_id FROM {gbif_observations} WHERE {clause}").format(
        gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        clause=clause,
    )
    result = await execute_psql_query(conn, query, dict_cursor=True, fetch='all')
    return {r['gbif_id'] for r in result} if result else set()


@pytest.mark.asyncio
class TestCreateOccurrenceTaxonFilter:

    async def test_default_animalia_excludes_invasive(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """No taxon restriction, but invasive taxa dropped."""
        result = await _run_filter(conn, OccurrenceFilters())
        assert 10 not in result  # invasive, excluded by default
        # Everything else present (8 excluded by date, tested separately)
        assert {1, 3, 4, 5, 7, 9} == result

    async def test_default_animalia_include_invasives_true(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(include_invasives=True))
        assert 10 in result

    async def test_species_level_taxon_id_matches_self(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """Test that filtering on the species itself returns its own direct observation."""
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTATX']))
        assert 1 in result
        assert 5 not in result

    async def test_species_level_taxon_id_includes_subspecies_and_form_descendants(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        Filtering on the species must also grab subspecies observation (3),
        the synonym-resolved subspecies observation (4), and the
        form-under-subspecies observation (7) -- This tests taxon_lineage past
        the GBIF rank_key columns.
        """
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTATX']))
        assert {1, 3, 4, 7, 9} == result
        assert 5 not in result

    async def test_subspecies_level_taxon_id_includes_form_child(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        Filtering directly on the subspecies must still grab the form
        observation nested beneath it.
        """
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTASUB']))
        assert 7 in result
        assert 3 in result

    async def test_form_level_taxon_id_matches_only_itself(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTAFRM']))
        assert result == {7}

    async def test_superfamily_level_taxon_id_with_no_direct_observations(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        FORM_SUPER (superfamily) has zero observations keyed directly to it and no
        dedicated rank column in gbif_observations. It must still resolve via
        the recursive lineage walk to every descendant observation, including
        the form-level one.
        """
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['FORM_SUPER']))
        assert {1, 3, 4, 7, 9} == result

    async def test_unrelated_family_taxon_id_excludes_atta_lineage(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """Just a little sanity check since a lot of these wind up with the same set"""
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['WILDCRD']))
        assert result == {5}

    async def test_multiple_taxon_ids_return_all(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTAFRM', 'WILDCRD']))
        assert {5, 7} == result
        assert 1 not in result
        assert 3 not in result

    async def test_invasive_species_excluded_when_matched_via_ancestor(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        Filtering on the genus (ancestor of the invasive species) should
        still drop the invasive observation
        """
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['ATTA']))
        assert 10 not in result
        assert {1, 3, 4, 7, 9} == result

    # TODO: Is this exactly what we want? Seems counterintuitive.
    async def test_invasive_species_included_when_directly_requested(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        If the requested taxon_id is the invasive taxon, its observations 
        are included even with include_invasives=False.
        """
        result = await _run_filter(conn, OccurrenceFilters(taxon_ids=['INV0001']))
        assert result == {10}

    async def test_invasive_included_everywhere_with_include_invasives_true(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(
            conn, OccurrenceFilters(
                taxon_ids=['ATTA'], include_invasives=True)
        )
        assert 10 in result

    async def test_taxon_ids_normalized_from_single_string(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """normalize_to_list should accept a bare string, not just a list."""
        clause = create_occurrence_taxon_filter(
            'ATTATX', include_invasives=True)
        assert clause is not None  # compiles without raising; behavior covered above


@pytest.mark.asyncio
class TestCreateOccurrenceFilterSql:

    async def test_skip_taxa_bypasses_taxon_and_invasive_logic(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """
        skip_taxa=True is a no-op on taxon filtering -- invasive observation (10)
        should appear despite no include_invasives override.
        """
        result = await _run_filter(conn, OccurrenceFilters(), skip_taxa=True)
        assert 10 in result

    async def test_missing_collection_start_date_always_excluded(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(), skip_taxa=True)
        assert 8 not in result

    async def test_exclude_inaturalist_when_include_inat_false(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(include_inat=False), skip_taxa=True)
        assert 4 not in result   # institution_code = 'iNaturalist'
        assert 1 in result

    async def test_include_inaturalist_when_include_inat_true(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(include_inat=True), skip_taxa=True)
        assert 4 in result

    async def test_date_start_filters_earlier_observations(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(
            conn, OccurrenceFilters(date_start='2023-01-01'), skip_taxa=True
        )
        assert 1 not in result   # 2021-03-04
        assert 3 in result       # 2023-03-04

    async def test_date_end_filters_later_observations(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(
            conn, OccurrenceFilters(date_end='2021-12-31'), skip_taxa=True
        )
        assert 1 in result
        assert 3 not in result

    async def test_datasets_filter_restricts_to_named_datasets(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(conn, OccurrenceFilters(datasets=['DS_A']), skip_taxa=True)
        assert 1 in result
        assert 7 not in result   # DS_B

    async def test_coord_uncertainty_null_is_always_included(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """NULL coordinate_uncertainty must pass regardless of threshold, per
        the explicit IS NULL OR <= clause."""
        result = await _run_filter(
            conn, OccurrenceFilters(coord_uncertainty=10), skip_taxa=True
        )
        assert 3 in result  # coordinate_uncertainty_in_meters is None

    async def test_coord_uncertainty_excludes_above_threshold(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(
            conn, OccurrenceFilters(coord_uncertainty=1000), skip_taxa=True
        )
        assert 9 not in result   # 100000
        assert 1 in result       # 50

    async def test_combined_taxon_and_date_and_dataset_filters(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        """Sanity check that composed clauses AND together correctly, not just
        each in isolation -- form observation (7) matches the subspecies
        ancestor, DS_B dataset, and is after 2025."""
        result = await _run_filter(
            conn,
            OccurrenceFilters(taxon_ids=['ATTASUB'], datasets=[
                'DS_B'], date_start='2025-01-01'),
        )
        assert result == {7}

    async def test_regions_filter_returns_matching_obs(
        self, setup_gbif_schema, simple_tx_taxa, conn
    ):
        result = await _run_filter(
            conn, OccurrenceFilters(regions=[str(REGION_A_ID)]), skip_taxa=True
        )
        assert result == {1}
