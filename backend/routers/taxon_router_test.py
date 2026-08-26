from psycopg import sql
import pytest
import pytest_asyncio
import inspect

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.jobs.tasks.view_tasks import refresh_materialized_view
from backend.models.occurrence import OccurrenceFilters
from backend.routers.taxon_router import get_qualified_taxa


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    # Values to insert into backbone table, then brought into tx_taxa mat view
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
        {
            'scientific_name': 'Atta texana falseyi',
            'canonical_name': 'Atta texana falseyi',
            'taxon_id': '9999999',
            'accepted_name_usage_id': '9999999',
            'taxon_rank': 'subspecies',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        {
            'scientific_name': 'Trachymyrmex cowboyii',
            'canonical_name': 'Trachymyrmex cowboyii',
            'taxon_id': '9999998',
            'accepted_name_usage_id': '9999999',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'synonym',
        },
        {
            'scientific_name': 'Madeitupidae',
            'canonical_name': 'Madeitupidae',
            'taxon_id': '9999997',
            'accepted_name_usage_id': None,
            'taxon_rank': 'family',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
        },
        {
            'scientific_name': 'Outofnames igiveupus',
            'canonical_name': 'Outofnames igiveupus',
            'taxon_id': '9999996',
            'accepted_name_usage_id': '1323108',
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'synonym',
        }
    ]
    # tx_taxa only includes those taxa with observations
    occ = [
        {
            'gbif_id': 1,
            'taxon_key': '5035741',
            'accepted_taxon_key': '5035741',
            'collection_start_date': '2021-03-04',
            'kingdom_key': '1',
            'family_key': '4342',
            'genus_key': '1323108',
            'species_key': '5035741',
        },
        {
            'gbif_id': 2,
            'taxon_key': '1323108',
            'accepted_taxon_key': '1323108',
            'collection_start_date': '2022-03-04',
            'kingdom_key': '1',
            'family_key': '4342',
            'genus_key': '1323108',
            'species_key': None
        },
        {
            'gbif_id': 3,
            'taxon_key': '9999999',
            'accepted_taxon_key': '9999999',
            'collection_start_date': '2023-03-04',
            'kingdom_key': '1',
            'family_key': '4342',
            'genus_key': '1323108',
            'species_key': '9999999',
        },
        {
            'gbif_id': 4,
            'taxon_key': '9999998',
            'accepted_taxon_key': '9999999',
            'collection_start_date': '2024-03-04',
            'kingdom_key': '1',
            'family_key': '4342',
            'genus_key': '1323108',
            'species_key': '9999998',
        },
        {
            'gbif_id': 5,
            'taxon_key': '9999997',
            'accepted_taxon_key': '9999997',
            'collection_start_date': '2025-03-04',
            'kingdom_key': 1,
            'family_key': None,
            'genus_key': None,
            'species_key': None
        },
        {
            'gbif_id': 6,
            'taxon_key': '9999996',
            'accepted_taxon_key': '1323108',
            'collection_start_date': '2026-03-04',
            'kingdom_key': '1',
            'family_key': '4342',
            'genus_key': '1323108',
            'species_key': '9991111',
        }
    ]

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)


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
        assert all(search_term in r['canonical_name'].lower() for r in results)

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
        assert all('species' not in r['taxon_rank'] for r in results)
        assert all('subspecies' not in r['taxon_rank'] for r in results)

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
        assert results[0]['taxon_id'] == '9999999'

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
        assert results[0]['taxon_id'] == '1323108'


class TestGetTaxonInfo:
    @pytest.mark.asyncio
    async def test_get_taxon_info_returns_correct_fields(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxon/get_taxon_info', params={'taxon_id': '5035741'})

        assert response.status_code == 200
        result = response.json()
        assert result['canonical_name'] == 'Atta texana'
        assert result['taxon_rank'] == 'species'

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
        canonical_names = [r['canonical_name'] for r in results]

        # Synonyms excluded entirely
        assert 'Trachymyrmex cowboyii' not in canonical_names
        assert 'Outofnames igiveupus' not in canonical_names

        # Accepted taxa present
        assert 'Atta texana' in canonical_names
        assert 'Atta' in canonical_names
        assert 'Atta texana falseyi' in canonical_names
        assert 'Madeitupidae' in canonical_names

        # taxonomic_status is never 'synonym'
        assert all(r['taxonomic_status'] != 'synonym' for r in results)


class TestGetQualifiedTaxa:
    @pytest.mark.asyncio
    async def test_get_children_from_higher(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['1323108'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': None,
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['9999999', '1323108', '5035741'])

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
            'taxon_ids': ['1'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['435ebf14-5173-466c-8afb-32ddaaa3b253'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['1323108', '5035741'])

        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['1'],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['bf8131cd-ebc8-41c1-b17f-766eec7e48fc'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set(['1323108'])

    async def test_no_matches_returns_empty_list(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['123456789'], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        assert response.status_code == 200
        assert response.json() == []

    async def test_no_duplicate_taxon_ids_in_response(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        response = await client.post('/taxon/get_qualified_taxa', json={
            'taxon_ids': ['9999999'], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        results = response.json()
        assert len(results) == len(set(results))

    @pytest.mark.asyncio
    async def test_each_filter_individually(self, setup_gbif_schema, occurrence_filter_data, client):
        """
        One test, one section per filter. Each section changes exactly
        one field off the base payload and checks the result set narrows
        as expected. Sections are independent — if one fails, the others
        still tell you whether their filter is fine.
        """

        base_payload = {
            # family — covers both species (5035741, 9999001)
            'taxon_ids': ['4342'],
            'include_inat': True,
            'include_invasives': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'coord_uncertainty': None,
            'regions': None,
        }

        # --- baseline: no filters beyond taxon lineage ---
        response = await client.post('/taxon/get_qualified_taxa', json=base_payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741', '9999001'}

        # --- include_invasives=False excludes taxon 9999001 (invasive) ---
        payload = {**base_payload, 'include_invasives': False}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741'}

        # --- include_inat=False excludes row 2, taxon 5035741 still
        # qualifies via rows 1/3/4 ---
        payload = {**base_payload, 'include_inat': False}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741', '9999001'}

        # --- datasets=['dataset-b'] leaves only rows 2 and 5
        # (taxon 5035741 only — row 6/9999001 is dataset-a) ---
        payload = {**base_payload, 'datasets': ['dataset-b']}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741'}

        # --- date_start excludes row 4 (2019) and row 1 (2020),
        # leaves row 5 (2022, taxon 5035741) and row 6 (2022, taxon 9999001) ---
        payload = {**base_payload, 'date_start': '2022-01-01'}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741', '9999001'}

        # --- date_end excludes row 5/row 6 (2022), leaves rows 1/2/4 (<=2021) ---
        payload = {**base_payload, 'date_end': '2021-12-31'}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741'}

        # --- coord_uncertainty=100 keeps row 1 (100) and row 4 (NULL,
        # passes via IS NULL OR), excludes nothing here since no row
        # exceeds 100 — use a tighter bound to prove exclusion ---
        payload = {**base_payload, 'coord_uncertainty': 10}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        # Only row 4 (NULL uncertainty) and row 2 (50, excluded) —
        # row 1/3/5/6 all have uncertainty=100, excluded by the <=10 bound.
        # taxon 5035741 still qualifies via row 4 (NULL); 9999001 has no
        # row under the bound, excluded.
        assert set(response.json()) == {'5035741'}

        # --- coord_uncertainty=0 explicitly: confirms `is None` check,
        # not a falsy check, on the backend. Row 5 (uncertainty=0) must
        # NOT be treated as "no filter" — only NULL or <=0 rows pass ---
        payload = {**base_payload, 'coord_uncertainty': 0}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        # taxon 5035741 passes via row 4 (NULL); taxon 9999001 has only
        # row 6 (uncertainty=100), excluded.
        assert set(response.json()) == {'5035741'}

        # --- regions=[REGION_A_ID] restricts to taxa present in that
        # region via TAXON_PRESENCE_TABLE (observation 1 tagged there) ---
        payload = {**base_payload,
                   'regions': ['11111111-1111-1111-1111-111111111111']}
        response = await client.post('/taxon/get_qualified_taxa', json=payload)
        assert response.status_code == 200
        assert set(response.json()) == {'5035741'}

    def test_get_qualified_taxa_covers_all_filters(self):
        source = inspect.getsource(get_qualified_taxa)
        fields = set(OccurrenceFilters.model_fields.keys())
        # regions are handled via TAXON_PRESENCE_TABLE join, not region_clause
        excluded = {'regions'}
        missing = [f for f in fields - excluded if f not in source]
        assert not missing, f"get_qualified_taxa is missing: {missing}"
