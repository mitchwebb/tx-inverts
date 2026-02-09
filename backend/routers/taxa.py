import time
from backend.core.exception_handler import InvalidTaxonRankError, TaxonNotFoundError
from fastapi import Request, APIRouter, HTTPException
from pydantic import BaseModel
from backend.data_util.execute_psql_query import execute_psql_query
from backend.models.api_types import TaxonRequest, TextData
from typing import Literal
from psycopg import sql
import time

router = APIRouter()


async def get_taxon_rank(conn, taxon_id):
    query = sql.SQL('''
        SELECT taxon_rank
        FROM tx_taxa
        WHERE taxon_id = {taxon_id}
    ''').format(taxon_id=sql.Literal(taxon_id))

    async with execute_psql_query(conn, query, (), fetch='one', dict_cursor=True) as result:
        if result is None:
            raise TaxonNotFoundError(f'No taxon found for taxon_id={taxon_id}')

        taxon_rank = result['taxon_rank']

        if taxon_rank is None:
            raise InvalidTaxonRankError(
                f'taxon_rank is NULL for taxon_id={taxon_id}'
            )

        if taxon_rank not in RANK_ORDER:
            raise InvalidTaxonRankError(
                f'Invalid taxon_rank "{taxon_rank}" for taxon_id={taxon_id}'
            )

        return taxon_rank


# Provide search suggestions based on taxon search
# Returns only accepted/doubtful taxa, resolving synonyms automatically
@router.post("/search_suggest",)
async def search(data: TextData, request: Request):
    search_term = data.text
    query = '''
        SELECT DISTINCT ON (COALESCE(a.taxon_id, t.taxon_id))
            COALESCE(a.scientific_name, t.scientific_name) AS scientific_name,
            COALESCE(a.taxon_id, t.taxon_id) AS taxon_id,
            COALESCE(a.taxon_rank, t.taxon_rank) AS taxon_rank,
            COALESCE(a.us_invasive, t.us_invasive) AS us_invasive,
            COALESCE(a.taxonomic_status, t.taxonomic_status) AS taxonomic_status
        FROM tx_taxa t
        LEFT JOIN tx_taxa a
            ON t.accepted_name_usage_id = a.taxon_id
        WHERE 
            t.canonical_name ~* %s
            AND COALESCE(a.taxonomic_status, t.taxonomic_status) IN ('accepted', 'doubtful')
        ORDER BY
                COALESCE(a.taxon_id, t.taxon_id),
            COALESCE(a.canonical_name, t.canonical_name)
        LIMIT 10;
    '''
    start = time.time()
    try:
        async with request.app.state.db_pool.connection() as conn:
            async with execute_psql_query(conn, query, ('\\m' + search_term.lower(), ), 'all', dict_cursor=True) as results:
                end = time.time()
                print(end - start)
                results = [dict(row) for row in results]
                return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TODO: Let's get some timing going, this isn't acceptable
@router.post("/get_taxon_info")
async def search(data: TaxonRequest, request: Request):
    taxon_id = data.taxon_id
    print(taxon_id)

    taxon_query = '''
        SELECT
            canonical_name,
            scientific_name_authorship,
            accepted_name_usage_id,
            kingdom,
            phylum,
            class,
            "order",
            family,
            genus,
            species,
            subspecies,
            taxon_rank,
            us_invasive,
            taxonomic_status,
            ns_rank_state,
            ns_rank_state_no_inat
        FROM tx_taxa
        WHERE taxon_id = %s
    '''
    start = time.time()
    try:
        # Get taxon info
        async with request.app.state.db_pool.connection() as conn:
            async with execute_psql_query(conn, taxon_query, (taxon_id,), 'one', dict_cursor=True) as taxon_result:
                end = time.time()
                print(end - start)
                if not taxon_result:
                    raise HTTPException(
                        status_code=404, detail="Taxon not found")
            print('taxoninfo DONE')
            return {
                "result": {
                    **taxon_result,
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

RANK_ORDER = [
    'kingdom',
    'phylum',
    'class',
    'order',
    'family',
    'genus',
    'species',
    'subspecies'
]

type TaxonomicRank = Literal[
    'kingdom',
    'phylum',
    'class',
    'order',
    'family',
    'genus',
    'species',
    'subspecies'
]

RANK_COLS = [f"{r}_id" for r in RANK_ORDER]


def get_child_rank(parent_rank: TaxonomicRank):
    try:
        index = RANK_ORDER.index(parent_rank)
        return RANK_ORDER[index + 1]
    except (ValueError, IndexError):
        return None


class TaxaChildrenRequest(BaseModel):
    parent_id: int
    parent_rank: TaxonomicRank


# Get flat backbone for frontend (excludes synonyms)
@router.get("/get_backbone")
async def get_backbone(request: Request):
    query = '''
        SELECT
                        taxon_id,
                        taxon_rank,
                        parent_name_usage_id,
            accepted_name_usage_id,
                        canonical_name,
                        scientific_name_authorship,
                        ns_rank_state,
            ns_rank_state_no_inat,
            taxonomic_status,
            us_invasive,
            phylum,
            class,
            "order",
            family
                FROM tx_taxa
        WHERE taxonomic_status IN ('accepted', 'doubtful')
                ORDER BY taxon_rank, canonical_name
    '''
    start = time.perf_counter()
    async with request.app.state.db_pool.connection() as conn:
        async with execute_psql_query(conn, query, fetch='all', dict_cursor=True) as result:
            end = time.perf_counter()
            print(f"Query time: {end - start:.4f}s")
            if not result:
                raise HTTPException(
                    status_code=404, detail='Backbone not retrieved')
            tree = result
            return {
                "taxa": tree
            }
