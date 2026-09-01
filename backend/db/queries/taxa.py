# Premade taxon-related queries
from backend.constants.taxa import TAXON_RANK_ORDER
from backend.core.exception_handler import InvalidTaxonRankError, TaxonNotFoundError
from backend.data_util.execute_psql_query import execute_psql_query
from psycopg import AsyncConnection, sql

from backend.db.schema.tx_taxa import TX_TAXA_TABLE


async def get_taxon_rank(conn: AsyncConnection, taxon_id: str) -> str:
    """
    Given a taxon id, determine the taxonomic rank using the tx_taxa table
    """

    query = sql.SQL("""
        SELECT taxon_rank
        FROM {tx_taxa}
        WHERE taxon_id = {taxon_id}
    """).format(
        tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
        taxon_id=sql.Literal(taxon_id)
    )

    result = await execute_psql_query(conn, query, fetch='one', dict_cursor=True)
    if result is None:
        raise TaxonNotFoundError(f"No taxon found for taxon_id={taxon_id}")

    taxon_rank = result['taxon_rank']

    if taxon_rank is None:
        raise InvalidTaxonRankError(
            f"taxon_rank is NULL for taxon_id={taxon_id}"
        )

    if taxon_rank not in TAXON_RANK_ORDER:
        raise InvalidTaxonRankError(
            f"Invalid taxon_rank '{taxon_rank}' for taxon_id={taxon_id}"
        )

    return taxon_rank
