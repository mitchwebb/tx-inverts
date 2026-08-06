# Taxon related API endpoints
from backend.db.queries.occurrence import create_occurrence_filter_sql
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.models.occurrence import OccurrenceFilters
from fastapi import Request, APIRouter, HTTPException
from backend.data_util.execute_psql_query import execute_psql_query
from backend.models.api import MultiTaxaObsRequestParams
from psycopg import sql
from backend.core.logging import api_logger
from backend.models.taxa import TaxonInfo, TaxonSuggestion, TaxonTreeNode


taxon_router = APIRouter()


@taxon_router.get('/taxon_search_suggest',)
async def search_taxon(request: Request, search_term: str, exclude_species: bool = False) -> list[TaxonSuggestion]:
    """
    Get taxon search suggestions given a search term. 
    Only searches for beginnings of words.
    Can conditionally exclude species results (specialized use for parent taxon filtering).

    Returns only accepted/doubtful taxa, resolving synonyms automatically.

    Args:
        request (fastapi.Request): FastAPI request object
        search_term (str): String/substring to use for search
        exclude_species (bool): If True, only return taxa of rank Genus and higher (default = False)

    Returns:
        list[TaxonSuggestion]: List of taxon suggestions (scientific_name, canonical_name, taxon_id, taxon_rank, us_invasive, taxonomic_status)
            ordered alphabetically
    """

    # Handle species exclusion (or lack thereof)
    exclude_species_section = sql.SQL("")
    if exclude_species:
        exclude_species_section = sql.SQL(
            "AND COALESCE(a.taxon_rank, t.taxon_rank) NOT IN ('species', 'subspecies')"
        )

    # Search by substring (case insensitive)
    # Resolve to accepted_name_usage_id, use this information instead, if available
    # This effectively hides synonyms from search (Searching "Protoxaea texana" shows result for "Mesoxaea texana" instead)
    query = sql.SQL("""
        SELECT DISTINCT ON (COALESCE(a.taxon_id, t.taxon_id))
            COALESCE(a.scientific_name, t.scientific_name) AS scientific_name,
            COALESCE(a.canonical_name, t.canonical_name) AS canonical_name,
            COALESCE(a.taxon_id, t.taxon_id) AS taxon_id,
            COALESCE(a.taxon_rank, t.taxon_rank) AS taxon_rank,
            COALESCE(a.us_invasive, t.us_invasive) AS us_invasive,
            COALESCE(a.taxonomic_status, t.taxonomic_status) AS taxonomic_status
        FROM {tx_taxa} t
        LEFT JOIN {tx_taxa} a
            ON t.accepted_name_usage_id = a.taxon_id
        WHERE
            t.canonical_name ~* {search_term}
            AND COALESCE(a.taxonomic_status, t.taxonomic_status) IN ('accepted', 'doubtful')
            {exclude_species_section}
        ORDER BY
            COALESCE(a.taxon_id, t.taxon_id),
            COALESCE(a.canonical_name, t.canonical_name)
        LIMIT 10;
    """).format(
        tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
        search_term=sql.Literal('\\m' + search_term.lower()),
        exclude_species_section=exclude_species_section
    )
    try:
        async with request.app.state.db_pool.connection() as conn:
            results = await execute_psql_query(conn, query, fetch='all', dict_cursor=True) or []
            return [TaxonSuggestion(**row) for row in results]
    except Exception as e:
        api_logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@taxon_router.get('/get_taxon_info')
async def get_taxon_info(taxon_id: int, request: Request) -> TaxonInfo:
    """
    Get assorted taxon info for a given taxon_id

    Args:
        taxon_id (int): GBIF taxonID of desired taxon
        request (fastapi.Request): FastAPI request object

    Returns:
        TaxonInfo:
                canonical_name,
                scientific_name_authorship,
                accepted_name_usage_id,
                kingdom,
                phylum,
                taxon_class,
                order,
                family,
                genus,
                species,
                subspecies,
                taxon_rank,
                us_invasive,
                taxonomic_status,
                ns_rank_state,
                and ns_rank_state_no_inat
            of retrieved species
    """

    try:
        taxon_query = sql.SQL("""
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
            WHERE taxon_id = {taxon_id}
        """).format(taxon_id=sql.Literal(taxon_id))

        # Get taxon info
        async with request.app.state.db_pool.connection() as conn:
            taxon_result = await execute_psql_query(
                conn, taxon_query, fetch='one', dict_cursor=True)

    except Exception as e:
        api_logger.exception(f"Issue getting taxon info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if taxon_result is None:
        raise HTTPException(
            status_code=404, detail="Taxon not found")

    return TaxonInfo(**taxon_result)


# Get flat backbone for frontend (excludes synonyms)
@taxon_router.get('/get_backbone')
async def get_backbone(request: Request) -> list[TaxonTreeNode]:
    """
    Get backbone from tx_taxa table (excluding synonyms)

    Args:
        request (fastapi.Request): FastAPI request object

    Returns:
        list[TaxonTreeNode]:
            A list of taxon information, used for creating/navigating/displaying
            taxaTree on frontend
    """

    try:
        query = sql.SQL("""
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
                family,
                genus
            FROM {tx_taxa}
            WHERE taxonomic_status IN ('accepted', 'doubtful')
                    ORDER BY taxon_rank, canonical_name
        """).format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))

        async with request.app.state.db_pool.connection() as conn:
            result = await execute_psql_query(conn, query, fetch='all', dict_cursor=True) or []
        return [TaxonTreeNode(**row) for row in result]

    except HTTPException:
        raise
    except Exception as e:
        api_logger.exception("Issue getting taxon info: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Get list of qualified taxon_ids based on various filters
@taxon_router.post('/get_qualified_taxa')
async def get_qualified_taxa(params: MultiTaxaObsRequestParams, request: Request):
    """
    Get list of taxon ids of taxa represented in observations data given
    various observation filters (MultiTaxaObsRequestParams)

    Args:
        params (MultiTaxaObsRequestParams): Various params for filtering observation data
        request (fastapi.Request): FastAPI request object

    Returns:
        list[int]: List of qualified taxon ids
    """

    api_logger.info("Getting qualified taxa...")

    try:
        # Create occurrence filter item
        filter_payload = OccurrenceFilters(
            taxon_ids=params.taxon_ids,  # Derive qualified taxa from ALL taxa
            include_inat=params.include_inat,
            date_start=params.date_start,
            date_end=params.date_end,
            datasets=params.datasets,
            coord_uncertainty=params.coord_uncertainty,
            include_invasives=params.include_invasives
            # EXCLUDE regions—use the special join below
        )

        # Create occurrence filter sql chunk
        occurrence_filter = create_occurrence_filter_sql(filter_payload)

        # If regions specified, include special taxa-by-region join
        # This asks whether a taxon is found in the region, avoiding filtering each occurrence
        if params.regions:
            region_literals = sql.SQL(', ').join(
                sql.Literal(r) for r in params.regions)
            region_join = sql.SQL("""
                JOIN {presence_table} p 
                ON {observations_table}.accepted_taxon_key = p.accepted_taxon_key
                AND p.region_id IN ({regions})
            """).format(
                presence_table=sql.Identifier(TAXON_PRESENCE_TABLE.name),
                regions=region_literals,
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            )
        else:
            region_join = sql.SQL("")

        # Piece together the full query
        occurrence_query = sql.SQL("""
            SELECT DISTINCT {observations_table}.accepted_taxon_key
            FROM {observations_table}
            {region_join}
            WHERE {occurrence_filter}
        """).format(
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter,
            region_join=region_join
        )

        async with request.app.state.db_pool.connection() as conn:
            result = await execute_psql_query(conn, occurrence_query, fetch='all') or []
            taxon_ids = set(r[0] for r in result)

            return taxon_ids

    except Exception as e:
        api_logger.exception("Issue getting qualified taxa: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
