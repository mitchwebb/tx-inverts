import pytest
import pytest_asyncio

from backend.conftest import insert_rows
from backend.data_util.taxa_data import get_observation_count, taxon_exists
import pandas as pd

from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE


class TestGetObservationCount:
    # Make sure get_observation_count returns count on successful query
    async def test_result_returns_row(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa_data.execute_psql_query',
                     return_value=(2, ))
        result = await get_observation_count(mock_conn, '334272')
        assert result == 2

    # Make sure get_observation_count returns None on empty query
    async def test_empty_result_returns_none(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa_data.execute_psql_query',
                     return_value=None)
        result = await get_observation_count(mock_conn, '403258')
        assert result == None


@pytest.fixture
def simple_backbone():
    return pd.DataFrame([
        # Kingdom (root)
        {'taxon_id': 1, 'parent_name_usage_id': None,
            'accepted_name_usage_id': None, 'taxon_rank': 'kingdom'},
        # Phylum A under kingdom
        {'taxon_id': 2, 'parent_name_usage_id': 1,
            'accepted_name_usage_id': None, 'taxon_rank': 'phylum'},
        # Phylum B under same kingdom
        {'taxon_id': 3, 'parent_name_usage_id': 1,
            'accepted_name_usage_id': None, 'taxon_rank': 'phylum'},
        # Species under phylum A
        {'taxon_id': 4, 'parent_name_usage_id': 2,
            'accepted_name_usage_id': None, 'taxon_rank': 'species'},
        # Species under phylum B
        {'taxon_id': 5, 'parent_name_usage_id': 3,
            'accepted_name_usage_id': None, 'taxon_rank': 'species'},
        # Species with no phylum
        {'taxon_id': 6, 'parent_name_usage_id': 1,
            'accepted_name_usage_id': None, 'taxon_rank': 'species'},
        # Synonym
        {'taxon_id': 7, 'parent_name_usage_id': 3,
            'accepted_name_usage_id': 5, 'taxon_rank': 'species'},
        # Synonym that resolves to a higher taxon
        {'taxon_id': 8, 'parent_name_usage_id': 1,
            'accepted_name_usage_id': 2, 'taxon_rank': 'species'},
        # Child of synonym
        {'taxon_id': 9, 'parent_name_usage_id': 7,
            'accepted_name_usage_id': None, 'taxon_rank': 'subspecies'},
    ])


# class TestBuildLineages:
#     # Test that basic lineages are successfully built
#     def test_basic_lineage(self, simple_backbone):
#         result = build_lineages(simple_backbone)
#         row_a = result[result['taxon_id'] == 4].iloc[0]
#         assert row_a['kingdom_id'] == 1
#         assert row_a['phylum_id'] == 2

#         row_b = result[result['taxon_id'] == 5].iloc[0]
#         assert row_b['kingdom_id'] == 1
#         assert row_b['phylum_id'] == 3

#         # Species with no phylum (should link straight to kingdom)
#         row_c = result[result['taxon_id'] == 6].iloc[0]
#         assert row_c['kingdom_id'] == 1
#         assert pd.isna(row_c['phylum_id'])

#     # Test that synonyms get routed correctly and get accepted rank_id
#     def test_synonym_lineage(self, simple_backbone):
#         result = build_lineages(simple_backbone)

#         row = result[result['taxon_id'] == 7].iloc[0]
#         assert row['kingdom_id'] == 1
#         assert row['phylum_id'] == 3
#         assert row['species_id'] == 5

#     # Test that synonyms are given proper rank_id when being resolved as different taxon_rank
#     def test_synonym_rank_reassignment(self, simple_backbone):
#         result = build_lineages(simple_backbone)

#         row = result[result['taxon_id'] == 8].iloc[0]

#         # species_id should now be NA, given that synonym species resolves to phylum
#         assert pd.isna(row['species_id'])
#         # phylum_id should resolve to accepted_name_usage_id
#         assert row['phylum_id'] == 2

#     # Verify that root taxa have empty ids
#     def test_root_taxa_are_empty(self, simple_backbone):
#         result = build_lineages(simple_backbone)

#         row = result[result['taxon_id'] == 1].iloc[0]

#         assert pd.isna([row['phylum_id'], row['class_id'], row['order_id'],
#                        row['family_id'], row['genus_id'], row['species_id'], row['subspecies_id']]).all()

#     # Verify that child of synonym inherits updated lineage
#     def test_synonym_child_lineage(self, simple_backbone):
#         result = build_lineages(simple_backbone)

#         row = result[result['taxon_id'] == 7].iloc[0]

#         assert row['species_id'] == 5


@pytest_asyncio.fixture
async def simple_backbone_db(conn):
    # Values to insert into backbone table
    taxa = [
        {
            'scientific_name': 'Atta texana',
            'canonical_name': 'Atta texana',
            'taxon_id': '5035741',
            'accepted_name_usage_id': '5035741',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        {
            'scientific_name': 'Atta',
            'canonical_name': 'Atta',
            'taxon_id': '1323108',
            'accepted_name_usage_id': None,
            'taxon_rank': 'genus',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
    ]

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)


class TestTaxonExists:
    async def test_existing_taxon_returns_true(self, conn, simple_backbone_db):
        result = await taxon_exists(conn, '5035741')
        assert result == True

    async def test_missing_taxon_returns_false(self, conn, simple_backbone_db):
        result = await taxon_exists(conn, '0000000')
        assert result == False
