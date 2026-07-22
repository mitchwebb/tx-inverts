import pytest
import pytest_asyncio
import pandas as pd
import io

from backend.conftest import insert_rows
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.jobs.tasks.views import refresh_materialized_view
from backend.routers.downloads_router import download_table_and_stream, estimate_tsv_download_size

from psycopg import sql

taxa = [
    {
        'scientific_name': 'Atta texana',
        'canonical_name': 'Atta texana',
        'taxon_id': 5035741,
        'accepted_name_usage_id': 5035741,
        'parent_name_usage_id': 4342,
        'taxon_rank': 'species',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1323108,
        'species_id': 5035741,
    },
    {
        'scientific_name': 'Formicidae',
        'canonical_name': 'Formicidae',
        'taxon_id': 4342,
        'accepted_name_usage_id': 4342,
        'parent_name_usage_id': 1,
        'taxon_rank': 'family',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': None,
        'species_id': None
    },
    {
        'scientific_name': 'Scolopendridae',
        'canonical_name': 'Scolopendridae',
        'taxon_id': 4084,
        'accepted_name_usage_id': 4084,
        'parent_name_usage_id': 1,
        'taxon_rank': 'family',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4084,
        'genus_id': None,
        'species_id': None
    },
    {
        'scientific_name': 'Aphaenogaster cockerelli',
        'canonical_name': 'Aphaenogaster cockerelli',
        'taxon_id': 1315867,
        'accepted_name_usage_id': 1315867,
        'parent_name_usage_id': 1315863,
        'taxon_rank': 'species',
        'us_invasive': False,
        'taxonomic_status': 'accepted',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1315863,
        'species_id': 1315867,
    },
]

# Include some observations with range_extent adding up to 50km2 (rounded)
occ = [
    {
        'gbif_id': 1,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2020-03-04',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1323108,
        'species_id': 5035741,
    },
    {
        'gbif_id': 2,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2021-03-04',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1323108,
        'species_id': 5035741,
    },
    {
        'gbif_id': 3,
        'taxon_key': 5035741,
        'accepted_taxon_key': 5035741,
        'collection_start_date': '2019-03-04',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1323108,
        'species_id': 5035741,
    },
    {
        'gbif_id': 4,
        'taxon_key': 1315867,
        'accepted_taxon_key': 1315867,
        'collection_start_date': '2019-03-04',
        'kingdom_id': 1,
        'family_id': 4342,
        'genus_id': 1315863,
        'species_id': 1315867,
    }
]


@pytest_asyncio.fixture
async def simple_tx_taxa(conn):

    await insert_rows(taxa, GBIF_INVERTS_BACKBONE.name, conn)
    await insert_rows(occ, GBIF_OBSERVATIONS_TABLE.name, conn)

    await refresh_materialized_view(conn, TX_TAXA_TABLE.name)
    await refresh_materialized_view(conn, TAXON_LINEAGE_TABLE.name)


def _occ_taxa_query() -> sql.Composed:
    return sql.SQL("""
        SELECT o.gbif_id, o.collection_start_date, t.scientific_name
        FROM {occ} o
        JOIN {taxa} t ON t.taxon_id = o.taxon_key
        ORDER BY o.gbif_id
    """).format(
        occ=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        taxa=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
    )


async def _collect(agen) -> bytes:
    """Helper for collecting and concatenating chunks from stream."""
    return b''.join([chunk async for chunk in agen])


class TestDownloadTableAndStream:
    @pytest.mark.asyncio
    async def test_csv_output_has_header_and_comma_delimited_rows(self, test_pool, simple_tx_taxa):
        data = await _collect(download_table_and_stream(test_pool, _occ_taxa_query(), format='csv'))
        lines = data.decode().strip().split('\n')
        assert lines[0] == 'gbif_id,collection_start_date,scientific_name'
        assert len(lines) == 5  # header + 4 occurrence rows
        assert lines[1].split(',')[0] == '1'

    @pytest.mark.asyncio
    async def test_tsv_output_has_header_and_tab_delimited_rows(self, test_pool, simple_tx_taxa):
        data = await _collect(download_table_and_stream(test_pool, _occ_taxa_query(), format='tsv'))
        lines = data.decode().strip().split('\n')
        assert lines[0] == 'gbif_id\tcollection_start_date\tscientific_name'
        assert len(lines) == 5  # header + 4 occurrence rows
        assert lines[1].split('\t')[0] == '1'

    @pytest.mark.asyncio
    async def test_empty_result_set_still_yields_header_only(self, test_pool, simple_tx_taxa):
        query = sql.SQL("""
            SELECT gbif_id FROM {occ} WHERE gbif_id = -1
        """).format(occ=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name))

        data = await _collect(download_table_and_stream(test_pool, query, format='csv'))
        assert data.decode().strip() == 'gbif_id'

    @pytest.mark.asyncio
    async def test_streams_multiple_chunks_for_large_result(self, test_pool):
        # Generate large query response for streaming
        query = sql.SQL("""
            SELECT gs AS gbif_id, repeat('x', 200) AS filler
            FROM generate_series(1, 200000) AS gs
        """)

        chunks = [c async for c in download_table_and_stream(test_pool, query, format='csv')]
        # Make sure we are getting more than one chunk
        # This shouldn't change, but is an easy check
        assert len(chunks) > 1


class TestEstimateTSVDownloadSize:
    @pytest.mark.asyncio
    async def test_estimate_return_shape(self, conn, simple_tx_taxa):
        """
        Test that estimate returns 'size_estimate' and 'row_count' keys.
        Also test that row count matches expectations on easy query.
        """

        query = sql.SQL("""
            SELECT gbif_id FROM {occ}
        """).format(occ=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name))

        data = await estimate_tsv_download_size(conn, query)
        assert {'size_estimate', 'row_count'} == data.keys()
        assert data['row_count'] == 4

    async def test_estimate_computes_expected_size(self, conn, simple_tx_taxa):
        """
        Verify size_estimate calculation against an independently computed
        expected value
        """

        query = sql.SQL("""
            SELECT gbif_id FROM {occ}
        """).format(occ=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name))

        data = await estimate_tsv_download_size(conn, query)

        # Independently pull the same rows to compute the expected estimate
        sample_query = sql.SQL(
            "SELECT * FROM ({query}) AS t LIMIT 100").format(query=query)
        sample = await execute_psql_query(conn, sample_query, fetch='all')

        df = pd.DataFrame(sample)
        buf = io.StringIO()
        df.to_csv(buf, sep='\t', index=False)
        header_bytes = buf.getvalue().index('\n') + 1
        avg_row_bytes = (len(buf.getvalue().encode('utf-8')) -
                         header_bytes) / len(df)
        expected_size = (data['row_count'] * avg_row_bytes) + header_bytes

        assert data['size_estimate'] == pytest.approx(expected_size)


class TestGetRankedTaxaDownload:
    @pytest.mark.asyncio
    async def test_estimate_returns_size_dict(self, simple_tx_taxa, client):
        """estimate=True should return the size/row_count dict, not a stream."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                'taxon_ids': [5035741],
                'estimate': True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {'size_estimate', 'row_count'}
        assert data['row_count'] == 1  # only Atta texana is 'species' rank

    @pytest.mark.asyncio
    async def test_stream_returns_tsv_content_type_and_headers(self, simple_tx_taxa, client):
        """estimate=False should stream a TSV with correct headers."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                'taxon_ids': [5035741],
                'estimate': False,
            }
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/tab-separated-values; charset=utf-8'
        assert response.headers['content-disposition'] == 'attachment; filename=taxa_download.tsv'

    @pytest.mark.asyncio
    async def test_stream_body_contains_expected_row(self, simple_tx_taxa, client):
        """Confirm the streamed body actually contains the matched taxon, not just headers."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                'taxon_ids': [5035741],
                'estimate': False,
            }
        )
        body = response.text
        assert 'Atta texana' in body
        assert 'Formicidae' not in body  # family rank excluded, shouldn't match

    @pytest.mark.asyncio
    async def test_filters_out_non_species_subspecies_ranks(self, simple_tx_taxa, client):
        """Family-rank taxa matching taxon_id should be excluded by the rank filter."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                'taxon_ids': [4342],  # Formicidae, rank='family'
                'estimate': True,
            }
        )
        data = response.json()
        assert data['row_count'] == 0

    @pytest.mark.asyncio
    async def test_matches_on_accepted_name_usage_id(self, simple_tx_taxa, client):
        """taxon_id OR accepted_name_usage_id should both be valid match paths."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                # matches both taxon_id and accepted_name_usage_id here
                'taxon_ids': [5035741],
                'estimate': True,
            }
        )
        data = response.json()
        assert data['row_count'] == 1

    @pytest.mark.asyncio
    async def test_multiple_taxon_ids(self, simple_tx_taxa, client):
        """Multiple taxon_ids in the list should be OR'd via ANY(), not require all to match."""
        response = await client.post(
            '/downloads/get_ranked_taxa_download',
            json={
                # 2 species + 2 families
                'taxon_ids': [5035741, 1315867, 4342, 4084],
                'estimate': True,
            }
        )
        data = response.json()
        assert data['row_count'] == 2  # only the species-rank records count
