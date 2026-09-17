import uuid
from psycopg import sql
import pytest
import pytest_asyncio
import inspect

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.models.occurrence import OccurrenceFilters
from backend.routers.taxon_router import get_qualified_taxa


REGION_A_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
REGION_B_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')

TAXA = [
    {
        'scientific_name': 'Animalia', 'canonical_name': 'Animalia',
        'parent_name_usage_id': None, 'taxon_id': 'ANML',
        'accepted_name_usage_id': 'ANML', 'taxon_rank': 'kingdom',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Formicidae', 'canonical_name': 'Formicidae',
        'parent_name_usage_id': 'ANML', 'taxon_id': 'FRMCD',
        'accepted_name_usage_id': 'FRMCD', 'taxon_rank': 'family',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Atta', 'canonical_name': 'Atta',
        'parent_name_usage_id': 'FRMCD', 'taxon_id': 'ATTA',
        'accepted_name_usage_id': None, 'taxon_rank': 'genus',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Atta texana', 'canonical_name': 'Atta texana',
        'parent_name_usage_id': 'ATTA', 'taxon_id': 'ATTATX',
        'accepted_name_usage_id': 'ATTATX', 'taxon_rank': 'species',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Atta texana falseyi', 'canonical_name': 'Atta texana falseyi',
        'parent_name_usage_id': 'ATTATX', 'taxon_id': 'ATTAFALSE',
        'accepted_name_usage_id': 'ATTAFALSE', 'taxon_rank': 'subspecies',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Atta texana f. formi', 'canonical_name': 'Atta texana f. formi',
        'parent_name_usage_id': 'ATTAFALSE', 'taxon_id': 'ATTAFORMI',
        'accepted_name_usage_id': 'ATTAFORMI', 'taxon_rank': 'form',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Trachymyrmex cowboyii', 'canonical_name': 'Trachymyrmex cowboyii',
        'parent_name_usage_id': 'TRACHPARENT', 'taxon_id': 'COWBOY',
        'accepted_name_usage_id': 'ATTAFALSE', 'taxon_rank': 'species',
        'us_invasive': False, 'taxonomic_status': 'synonym',
    },
    {
        'scientific_name': 'Madeitupidae', 'canonical_name': 'Madeitupidae',
        'parent_name_usage_id': 'HYM', 'taxon_id': 'MADEUP',
        'accepted_name_usage_id': None, 'taxon_rank': 'family',
        'us_invasive': False, 'taxonomic_status': 'accepted',
    },
    {
        'scientific_name': 'Outofnames igiveupus', 'canonical_name': 'Outofnames igiveupus',
        'parent_name_usage_id': 'OUTTAPARENT', 'taxon_id': 'OUTTANAMES',
        'accepted_name_usage_id': 'ATTA', 'taxon_rank': 'species',
        'us_invasive': False, 'taxonomic_status': 'synonym',
    },
    {
        # Invasive species, same genus as ATTATX — exercises include_invasives branches
        'scientific_name': 'Solenopsis invicta', 'canonical_name': 'Solenopsis invicta',
        'parent_name_usage_id': 'ATTA', 'taxon_id': 'INVICTA',
        'accepted_name_usage_id': 'INVICTA', 'taxon_rank': 'species',
        'us_invasive': True, 'taxonomic_status': 'accepted',
    },
]

OCC = [
    {
        # Baseline row — passes every filter at defaults
        'gbif_id': 1, 'taxon_key': 'ATTATX', 'accepted_taxon_key': 'ATTATX',
        'collection_start_date': '2021-03-04', 'collection_end_date': '2021-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',  # Austin, TX
    },
    {
        # Direct genus-level observation, iNaturalist origin
        'gbif_id': 2, 'taxon_key': 'ATTA', 'accepted_taxon_key': 'ATTA',
        'collection_start_date': '2022-03-04', 'collection_end_date': '2022-03-05',
        'dataset_key': 'dataset-b', 'institution_code': 'iNaturalist',
        'coordinate_uncertainty_in_meters': 50,
        'geometry': 'POINT(-96.7970 32.7767)',  # Dallas, TX
    },
    {
        # Subspecies-level observation
        'gbif_id': 3, 'taxon_key': 'ATTAFALSE', 'accepted_taxon_key': 'ATTAFALSE',
        'collection_start_date': '2023-03-04', 'collection_end_date': '2023-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # Observed under a synonym taxon_key, resolved to the subspecies;
        # NULL coordinate_uncertainty — tests "IS NULL OR <=" branch
        'gbif_id': 4, 'taxon_key': 'COWBOY', 'accepted_taxon_key': 'ATTAFALSE',
        'collection_start_date': '2024-03-04', 'collection_end_date': '2024-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': None,
        'geometry': 'POINT(-95.3698 29.7604)',  # Houston, TX
    },
    {
        # Unrelated family — must never match Atta-rooted taxon_ids
        'gbif_id': 5, 'taxon_key': 'MADEUP', 'accepted_taxon_key': 'MADEUP',
        'collection_start_date': '2025-03-04', 'collection_end_date': '2025-03-05',
        'dataset_key': 'dataset-b', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 0,  # tests `is None` vs falsy bug
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # Observed under a synonym resolving to the genus
        'gbif_id': 6, 'taxon_key': 'OUTTANAMES', 'accepted_taxon_key': 'ATTA',
        'collection_start_date': '2026-03-04', 'collection_end_date': '2026-03-05',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # Form sighting, child of subspecies — the original reported bug
        # Only iNaturalist sighting (tests inat filter)
        'gbif_id': 7, 'taxon_key': 'ATTAFORMI', 'accepted_taxon_key': 'ATTAFORMI',
        'collection_start_date': '2026-03-04', 'collection_end_date': '2026-03-05',
        'dataset_key': 'dataset-b', 'institution_code': 'iNaturalist',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # Invasive taxon — tests include_invasives true/false branches
        'gbif_id': 8, 'taxon_key': 'INVICTA', 'accepted_taxon_key': 'INVICTA',
        'collection_start_date': '2022-06-01', 'collection_end_date': '2022-06-02',
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
    {
        # Collection_start_date NULL — tests hardcoded IS NOT NULL clause
        'gbif_id': 9, 'taxon_key': 'ATTATX', 'accepted_taxon_key': 'ATTATX',
        'collection_start_date': None, 'collection_end_date': None,
        'dataset_key': 'dataset-a', 'institution_code': 'TxState',
        'coordinate_uncertainty_in_meters': 100,
        'geometry': 'POINT(-97.7431 30.2672)',
    },
]

OBSERVATION_REGIONS = [
    {'observation_id': 1, 'region_id': REGION_A_ID},
    {'observation_id': 4, 'region_id': REGION_B_ID},
]


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    """
    Taxonomy + observations covering every branch in
    create_occurrence_filter_sql / create_occurrence_taxon_filter,
    including the subspecies->form lineage case and a synonym chain.
    """
    await insert_rows(TAXA, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(OCC, GBIF_OBSERVATIONS_TABLE.name, conn)
    await insert_rows(OBSERVATION_REGIONS, OBSERVATION_REGIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)


class TestTaxonSearchSuggest:
    @pytest.mark.asyncio
    async def test_string_start_search(self, setup_gbif_schema, simple_tx_taxa, client):
        search_term = 'atta'
        response = await client.get(
            '/taxon/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': False},
        )

        assert response.status_code == 200
        results = response.json()

        # Test that there are results and that all results contain our search term in the canonical name
        assert len(results) > 0
        assert all(search_term in r['canonicalName'].lower() for r in results)

    @pytest.mark.asyncio
    async def test_search_excludes_species(self, setup_gbif_schema, simple_tx_taxa, client):
        """Test that search excludes species and subspecies when 'exclude_species' is True"""

        search_term = 'atta'
        response = await client.get(
            '/taxon/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': True},
        )

        assert response.status_code == 200
        results = response.json()

        # Test that there are results and that no results are 'species' or 'subspecies'
        assert len(results) > 0
        assert all('species' not in r['taxonRank'] for r in results)
        assert all('subspecies' not in r['taxonRank'] for r in results)

    @pytest.mark.asyncio
    async def test_search_corrects_synonyms(self, setup_gbif_schema, simple_tx_taxa, client):
        """Test that synonyms are left out of search results, and are instead resolved to their accepted taxon"""

        search_term = 'cowboy'
        response = await client.get(
            '/taxon/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': False},
        )

        assert response.status_code == 200
        results = response.json()

        # Our fake synonym gets resolved to its accepted_name_usage_id taxon
        assert len(results) == 1
        assert results[0]['taxonID'] == 'ATTAFALSE'

    @pytest.mark.asyncio
    async def test_ignore_mid_string_search(self, setup_gbif_schema, simple_tx_taxa, client):
        search_term = 'exana'
        response = await client.get(
            '/taxon/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': False},
        )

        assert response.status_code == 200
        results = response.json()

        # Should return empty results
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_searches_include_species_resolved_to_higher_taxa(self, setup_gbif_schema, simple_tx_taxa, client):
        search_term = 'igiveup'
        response = await client.get(
            '/taxon/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': True},
        )

        assert response.status_code == 200
        results = response.json()

        # Should return result for searched taxon resolved to higher taxon
        assert len(results) == 1
        assert results[0]['taxonID'] == 'ATTA'


class TestGetTaxonInfo:
    @pytest.mark.asyncio
    async def test_get_taxon_info_returns_correct_fields(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxon/get_taxon_info', params={'taxon_id': 'ATTATX'})

        assert response.status_code == 200
        result = response.json()
        assert result['canonicalName'] == 'Atta texana'
        assert result['taxonRank'] == 'species'

    @pytest.mark.asyncio
    async def test_missing_taxon_returns_404(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxon/get_taxon_info', params={'taxon_id': '0'})

        assert response.status_code == 404


class TestGetBackbone:
    @pytest.mark.asyncio
    async def test_get_flat_backbone(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxon/get_backbone', params={})

        assert response.status_code == 200

        results = response.json()
        canonical_names = [r['canonicalName'] for r in results]

        # Synonyms excluded entirely
        assert 'Trachymyrmex cowboyii' not in canonical_names
        assert 'Outofnames igiveupus' not in canonical_names

        # Accepted taxa present
        assert 'Atta texana' in canonical_names
        assert 'Atta' in canonical_names
        assert 'Atta texana falseyi' in canonical_names
        assert 'Atta texana f. formi' in canonical_names
        assert 'Madeitupidae' in canonical_names

        # taxonomic_status is never 'synonym'
        assert all(r['taxonomicStatus'] != 'synonym' for r in results)


class TestGetQualifiedTaxa:
    @pytest.mark.asyncio
    async def test_get_children_from_higher(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['ATTA'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': None,
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['ATTAFALSE', 'ATTA', 'ATTATX', 'ATTAFORMI'])

    @pytest.mark.asyncio
    async def test_regions_filter(self, setup_gbif_schema, simple_tx_taxa, conn, client):

        # Create observations regions records
        regions = [
            {'observation_id': 1, 'region_id': '435ebf14-5173-466c-8afb-32ddaaa3b253',
                'region_type': 'county'},  # Add occ 1 (acc_taxon_id: 5035741)
            {'observation_id': 2, 'region_id': 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc',
                'region_type': 'county'},  # Add occ 2 (acc_taxon_id: 1323108)
            {'observation_id': 6, 'region_id': '435ebf14-5173-466c-8afb-32ddaaa3b253',
                'region_type': 'county'},  # Add occ 6 (acc_taxon_id: 1323108)
        ]
        regions_query = sql.SQL("""
            INSERT INTO {regions_table} ({fields})
            VALUES ({placeholders})
        """).format(
            regions_table=sql.Identifier(OBSERVATION_REGIONS_TABLE.name),
            fields=sql.SQL(', ').join(
                map(sql.Identifier, list(regions[0].keys()))),
            placeholders=sql.SQL(', ').join(
                sql.Placeholder() * len(list(regions[0].keys())))
        )

        for row in regions:
            await execute_psql_query(conn, regions_query, tuple(row.values()))

        await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)

        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['ANML'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['435ebf14-5173-466c-8afb-32ddaaa3b253'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['ATTA', 'ATTATX'])

        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['ANML'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['bf8131cd-ebc8-41c1-b17f-766eec7e48fc'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['ATTA'])

    async def test_no_matches_returns_empty_list(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['123456789'], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        assert response.status_code == 200
        assert response.json() == []

    async def test_no_duplicate_taxon_ids_in_response(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['ATTAFALSE'], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        results = response.json()
        assert len(results) == len(set(results))

    @pytest.mark.asyncio
    async def test_each_filter_individually(self, setup_gbif_schema, simple_tx_taxa, client):
        """
        One test, one section per filter. Each section changes exactly
        one field off the base payload and checks the result set narrows
        as expected.
        """

        # Baseline: no filters beyond taxon lineage.
        base_payload = {
            'taxon_ids': ['FRMCD'],
            'include_inat': True,
            'include_invasives': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'coord_uncertainty': None,
            'regions': None,
        }

        # Excluded (NULL date). Every other FRMCD-lineage taxon qualifies
        response = await client.post('/taxon/get_qualified_taxa', json=base_payload)
        assert response.status_code == 200
        assert set(response.json()) == {
            'ATTATX', 'ATTA', 'ATTAFALSE', 'ATTAFORMI', 'INVICTA'}

        # Include_invasives=False excludes INVICTA
        payload = {**base_payload, 'include_invasives': False}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {
            'ATTATX', 'ATTA', 'ATTAFALSE', 'ATTAFORMI'}

        # Include_inat=False, should exclude ATTAFORMI observation
        payload = {**base_payload, 'include_inat': False}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {
            'ATTATX', 'ATTA', 'ATTAFALSE', 'INVICTA'}

        # Datasets=['dataset-b']: only gbif 2 (ATTA), and gbif 7 (ATTAFORMI)
        # are within lineage and in dataset-b
        payload = {**base_payload, 'datasets': ['dataset-b']}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'ATTA', 'ATTAFORMI'}

        # date_start='2022-01-01' excludes gbif 1 (2021) and gbif 9
        # (NULL, always excluded). ATTATX has no other observations, so it
        # drops out entirely. Remaining: gbif 2/6 (ATTA), 3/4 (ATTAFALSE),
        # 7 (ATTAFORMI), 8 (INVICTA)
        payload = {**base_payload, 'date_start': '2022-01-01'}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {
            'ATTA', 'ATTAFALSE', 'ATTAFORMI', 'INVICTA'}

        # date_end='2021-12-31' keeps only gbif 1 (2021-03-04)
        payload = {**base_payload, 'date_end': '2021-12-31'}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'ATTATX'}

        # coord_uncertainty=10: passes NULL or <=10. Only gbif 4
        # (NULL, ATTAFALSE) qualifies within FRMCD; gbif 5 (0, MADEUP) is
        # outside the lineage entirely
        payload = {**base_payload, 'coord_uncertainty': 10}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'ATTAFALSE'}

        # coord_uncertainty=0 explicitly: confirms `is None` check, not
        # a falsy check. gbif 4 (NULL) still passes via IS NULL; gbif 5
        # would pass, but it outside lineage
        payload = {**base_payload, 'coord_uncertainty': 0}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'ATTAFALSE'}

        # regions=[REGION_A_ID]: only gbif 1 (ATTATX) is tagged REGION_A
        payload = {**base_payload, 'regions': [str(REGION_A_ID)]}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'ATTATX'}
