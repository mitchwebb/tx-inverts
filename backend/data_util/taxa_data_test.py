import pytest
import pytest_asyncio

from backend.conftest import insert_rows
from backend.data_util.taxa_data import get_observation_count, taxon_exists, derive_canonical_name
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


# Real cases from COL backbone
taxa = [
    # Odd little quoted infraclass
    {
        'scientificName': '"Lower Heterobranchia"',
        'genericName': None,
        'infragenericEpithet': None,
        'specificEpithet': None,
        'infraspecificEpithet': None,
        'taxonRank': 'infraclass',
        'scientificNameAuthorship': None,
        'expected_canonical': '"Lower Heterobranchia"'
    },
    # Broken superfamily case with authorship in scientific_name but not in authorship column
    {
        'scientificName': 'Poduroidea sensu Palacios-Vargas, 1994',
        'genericName': None,
        'infragenericEpithet': None,
        'specificEpithet': None,
        'infraspecificEpithet': None,
        'taxonRank': 'superfamily',
        'scientificNameAuthorship': None,
        'expected_canonical': 'Poduroidea'
    },
    # Normal Genus case
    {
        'scientificName': 'Campylenchia',
        'genericName': 'Campylenchia',
        'infragenericEpithet': None,
        'specificEpithet': None,
        'infraspecificEpithet': None,
        'taxonRank': 'genus',
        'scientificNameAuthorship': None,
        'expected_canonical': 'Campylenchia'
    },
    # Normal subgenus case
    {
        'scientificName': 'Culex (Melanoconion) Theobald, 1903',
        'genericName': 'Culex',
        'infragenericEpithet': 'Melanoconion',
        'specificEpithet': None,
        'infraspecificEpithet': None,
        'scientificNameAuthorship': 'Theobald, 1903',
        'taxonRank': 'subgenus',
        'expected_canonical': 'Culex (Melanoconion)'
    },
    # Normal species case with authorship
    {
        'scientificName': 'Atta texana (Buckley, 1860)',
        'genericName': 'Atta',
        'infragenericEpithet': None,
        'specificEpithet': 'texana',
        'infraspecificEpithet': None,
        'taxonRank': 'species',
        'scientificNameAuthorship': '(Buckley, 1860)',
        'expected_canonical': 'Atta texana'
    },
    # Species case where authorship appears WITHIN scientific name
    {
        'scientificName': 'Ambulyx moorei',
        'genericName': 'Ambulyx',
        'infragenericEpithet': None,
        'specificEpithet': 'moorei',
        'infraspecificEpithet': None,
        'taxonRank': 'species',
        'scientificNameAuthorship': 'moore',
        'expected_canonical': 'Ambulyx moorei'
    },
    # Normal subspecies case
    {
        'scientificName': 'Entypus texanus texanus (Cresson, 1872)',
        'genericName': 'Entypus',
        'infragenericEpithet': None,
        'specificEpithet': 'texanus',
        'infraspecificEpithet': 'texanus',
        'scientificNameAuthorship': '(Cresson, 1872)',
        'taxonRank': 'subspecies',
        'expected_canonical': 'Entypus texanus texanus'
    },
    # Normal form case
    {
        'scientificName': 'Polistes apachus f. apachus',
        'genericName': 'Polistes',
        'infragenericEpithet': None,
        'specificEpithet': 'apachus',
        'infraspecificEpithet': 'apachus',
        'scientificNameAuthorship': None,
        'taxonRank': 'form',
        'expected_canonical': 'Polistes apachus f. apachus'
    },
]


@pytest.mark.parametrize('taxon', taxa)
class TestDeriveCanonicalName:
    def test_taxon(self, taxon):
        canonical_name = derive_canonical_name(taxon)
        print(canonical_name)
        assert canonical_name == taxon['expected_canonical']
