import pytest

from backend.data_util.taxa import build_lineages, get_observation_count
import pandas as pd


class TestGetObservationCount:
    # Make sure get_observation_count returns count on successful query
    async def test_result_returns_row(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa.execute_psql_query',
                     return_value=(2, ))
        result = await get_observation_count(mock_conn, 334272)
        assert result == 2

    # Make sure get_observation_count returns None on empty query
    async def test_empty_result_returns_none(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa.execute_psql_query',
                     return_value=None)
        result = await get_observation_count(mock_conn, 403258)
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
            'accepted_name_usage_id': 3, 'taxon_rank': 'species'},
        # Synonym pointing to species
        {'taxon_id': 6, 'parent_name_usage_id': 2,
            'accepted_name_usage_id': 3, 'taxon_rank': 'species'},
    ])


class TestBuildLineages:
    def test_basic_lineage(self, simple_backbone):
        result = build_lineages(simple_backbone)
        row = result[result['taxon_id'] == 3].iloc[0]
        assert row['kingdom_id'] == 1
        assert row['phylum_id'] == 2
