from httpx import ASGITransport, AsyncClient
import psycopg
from psycopg import sql
import pytest
import pandas as pd
import pytest_asyncio

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.jobs.tasks.views import refresh_materialized_view
from backend.main import app


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):
    # Values to insert into backbone table, then brought into tx_taxa mat view
    taxa = [
        {
            'scientific_name': 'Atta texana',
            'canonical_name': 'Atta texana',
            'taxon_id': 5035741,
            'accepted_name_usage_id': 5035741,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
        },
        {
            'scientific_name': 'Atta',
            'canonical_name': 'Atta',
            'taxon_id': 1323108,
            'accepted_name_usage_id': None,
            'taxon_rank': 'genus',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': None
        },
        {
            'scientific_name': 'Atta texana falseyi',
            'canonical_name': 'Atta texana falseyi',
            'taxon_id': 9999999,
            'accepted_name_usage_id': 9999999,
            'taxon_rank': 'subspecies',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9999999,
        },
        {
            'scientific_name': 'Trachymyrmex cowboyii',
            'canonical_name': 'Trachymyrmex cowboyii',
            'taxon_id': 9999998,
            'accepted_name_usage_id': 9999999,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'synonym',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9999998,
        },
        {
            'scientific_name': 'Madeitupidae',
            'canonical_name': 'Madeitupidae',
            'taxon_id': 9999997,
            'accepted_name_usage_id': None,
            'taxon_rank': 'family',
            'us_invasive': False,
            'taxonomic_status': 'accepted',
            'kingdom_id': 1,
            'family_id': None,
            'genus_id': None,
            'species_id': None
        },
        {
            'scientific_name': 'Outofnames igiveupus',
            'canonical_name': 'Outofnames igiveupus',
            'taxon_id': 9999996,
            'accepted_name_usage_id': 1323108,
            'taxon_rank': 'species',
            'us_invasive': False,
            'taxonomic_status': 'synonym',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9991111,
        }
    ]
    # tx_taxa only includes those taxa with observations
    occ = [
        {
            'gbif_id': 1,
            'taxon_key': 5035741,
            'accepted_taxon_key': 5035741,
            'collection_start_date': '2021-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 5035741,
        },
        {
            'gbif_id': 2,
            'taxon_key': 1323108,
            'accepted_taxon_key': 1323108,
            'collection_start_date': '2022-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': None
        },
        {
            'gbif_id': 3,
            'taxon_key': 9999999,
            'accepted_taxon_key': 9999999,
            'collection_start_date': '2023-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9999999,
        },
        {
            'gbif_id': 4,
            'taxon_key': 9999998,
            'accepted_taxon_key': 9999999,
            'collection_start_date': '2024-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9999998,
        },
        {
            'gbif_id': 5,
            'taxon_key': 9999997,
            'accepted_taxon_key': 9999997,
            'collection_start_date': '2025-03-04',
            'kingdom_id': 1,
            'family_id': None,
            'genus_id': None,
            'species_id': None
        },
        {
            'gbif_id': 6,
            'taxon_key': 9999996,
            'accepted_taxon_key': 1323108,
            'collection_start_date': '2026-03-04',
            'kingdom_id': 1,
            'family_id': 4342,
            'genus_id': 1323108,
            'species_id': 9991111,
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
            '/taxa/taxon_search_suggest',
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
            '/taxa/taxon_search_suggest',
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
            '/taxa/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': False},
        )

        assert response.status_code == 200
        results = response.json()

        # Our fake synonym gets resolved to its accepted_name_usage_id taxon
        assert len(results) == 1
        assert results[0]['taxon_id'] == 9999999

    @pytest.mark.asyncio
    async def test_ignore_mid_string_search(self, setup_gbif_schema, simple_tx_taxa, client):
        search_term = 'exana'
        response = await client.get(
            '/taxa/taxon_search_suggest',
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
            '/taxa/taxon_search_suggest',
            params={'search_term': search_term, 'exclude_species': True},
        )

        assert response.status_code == 200
        results = response.json()

        # Should return result for searched taxon resolved to higher taxon
        assert len(results) == 1
        assert results[0]['taxon_id'] == 1323108


class TestGetTaxonInfo:
    @pytest.mark.asyncio
    async def test_get_taxon_info_returns_correct_fields(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxa/get_taxon_info', params={'taxon_id': 5035741})

        assert response.status_code == 200
        result = response.json()
        assert result['canonical_name'] == 'Atta texana'
        assert result['taxon_rank'] == 'species'

    @pytest.mark.asyncio
    async def test_missing_taxon_returns_404(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxa/get_taxon_info', params={'taxon_id': 0})

        assert response.status_code == 404


class TestGetBackbone:
    @pytest.mark.asyncio
    async def test_get_flat_backbone(self, setup_gbif_schema, simple_tx_taxa, client):
        response = await client.get('/taxa/get_backbone', params={})

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
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        response = await client.post('/taxa/get_qualified_taxa', json={
            'taxon_ids': [1323108],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': None,
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set([9999999, 1323108, 5035741])

    @pytest.mark.asyncio
    async def test_regions_filter(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)

        # Create observations regions records
        regions = [
            {'observation_id': 1, 'region_id': '435ebf14-5173-466c-8afb-32ddaaa3b253',
                'region_type': 'county'},  # Add occ 1 (acc_taxon_id: 5035741)
            {'observation_id': 2, 'region_id': 'bf8131cd-ebc8-41c1-b17f-766eec7e48fc',
                'region_type': 'county'},  # Add occ 2 (acc_taxon_id: 1323108)
            {'observation_id': 6, 'region_id': '435ebf14-5173-466c-8afb-32ddaaa3b253',
                'region_type': 'county'},  # Add occ 6 (acc_taxon_id: 1323108)
        ]
        regions_query = sql.SQL('''
            INSERT INTO {regions_table} ({fields})
            VALUES ({placeholders})
        ''').format(
            regions_table=sql.Identifier(OBSERVATION_REGIONS_TABLE.name),
            fields=sql.SQL(', ').join(
                map(sql.Identifier, list(regions[0].keys()))),
            placeholders=sql.SQL(', ').join(
                sql.Placeholder() * len(list(regions[0].keys())))
        )

        for row in regions:
            await execute_psql_query(conn, regions_query, tuple(row.values()))

        await refresh_materialized_view(conn, TAXON_PRESENCE_TABLE.name)

        response = await client.post('/taxa/get_qualified_taxa', json={
            'taxon_ids': [1],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['435ebf14-5173-466c-8afb-32ddaaa3b253'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set([1323108, 5035741])

        response = await client.post('/taxa/get_qualified_taxa', json={
            'taxon_ids': [1],  # Target parent taxon
            'include_inat': True,
            'date_start': None,
            'date_end': None,
            'datasets': None,
            'regions': ['bf8131cd-ebc8-41c1-b17f-766eec7e48fc'],
        })

        assert response.status_code == 200
        results = response.json()
        assert set(results) == set([1323108])

    async def test_no_matches_returns_empty_list(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        response = await client.post('/taxa/get_qualified_taxa', json={
            'taxon_ids': [123456789], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        assert response.status_code == 200
        assert response.json() == []

    async def test_no_duplicate_taxon_ids_in_response(self, setup_gbif_schema, simple_tx_taxa, conn, client):
        await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)
        response = await client.post('/taxa/get_qualified_taxa', json={
            'taxon_ids': [9999999], 'include_inat': True,
            'date_start': None, 'date_end': None, 'datasets': None, 'regions': None,
        })
        results = response.json()
        assert len(results) == len(set(results))
