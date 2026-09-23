# Download related API endpoints
from typing import AsyncIterator, Literal
from psycopg_pool import AsyncConnectionPool
import requests
from backend.config import get_settings
from backend.db.queries.dwc import DWC_TAXA_SELECT_CLAUSE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.models.api import DownloadRequestParams
from fastapi import APIRouter, HTTPException, Request, responses
from psycopg import sql, AsyncConnection
from backend.data_util.execute_psql_query import execute_psql_query
from backend.core.logging import api_logger
import pandas as pd
import io


download_router = APIRouter()

settings = get_settings()


async def download_table_and_stream(
    pool: AsyncConnectionPool,
    query: sql.Composed | sql.Composable,
    format: Literal['csv', 'tsv'],
) -> AsyncIterator[bytes]:
    """
    Stream query results directly from Postgres using COPY TO STDOUT.

    Uses psycopg's async COPY protocol to avoid buffering the full result set
    in memory, yielding chunks as they arrive from the database.

    Args:
        pool (AsyncConnectionPool): The async connection pool to acquire a connection from.
        query (sql.Composed): A composed psycopg SQL query to copy results from.
        format (Literal['csv', 'tsv']): Output format

    Yields:
        Raw bytes chunks of the query result in the requested format, with a header row.
    """
    async with pool.connection() as conn:
        # Using raw cursor here for copy
        async with conn.cursor() as cur:
            if format == 'tsv':
                delimiter_sql = sql.Literal('\t')
            else:
                delimiter_sql = sql.Literal(',')
            copy_sql = sql.SQL("""
                COPY (
                    {query}
                ) TO STDOUT
                WITH (
                    FORMAT CSV,
                    DELIMITER {delimiter},
                    HEADER TRUE
                )
            """).format(
                query=query,
                delimiter=delimiter_sql
            )

            async with cur.copy(copy_sql) as copy:
                async for chunk in copy:
                    yield bytes(chunk)


# Although this could be adjusted to allow for csv estimation, we aren't allowing csv output
async def estimate_tsv_download_size(conn: AsyncConnection, query: sql.Composed) -> dict[str, int | float]:
    """
    Estimate the byte size and row count of a TSV export for the given query.

    Runs a full COUNT(*) then samples 100 rows to compute average row size.

    Args:
        conn (AsyncConnection): Active async Postgres connection.
        query (sql.Composed): Composed SQL query whose output will be estimated.

    Returns:
        size_estimate: Estimated total size in bytes.
        row_count: Exact row count from COUNT(*).
    """

    # Full COUNT(*) is acceptable here — query completes in a few seconds at max
    # Get accurate row count
    count_query = sql.SQL(
        "SELECT COUNT(*) FROM ({query}) AS t").format(query=query)
    result = await execute_psql_query(conn, count_query, fetch='one')
    total_rows = result[0] if result is not None else 0

    # Sample rows to get realistic avg byte size including headers
    sample_query = sql.SQL("""
        SELECT * FROM ({query}) AS t
        WHERE random() < 0.1
        LIMIT 10000
    """).format(query=query)

    sample = await execute_psql_query(conn, sample_query, fetch='all')

    df = pd.DataFrame(sample)
    buf = io.StringIO()
    df.to_csv(buf, sep='\t', index=False)
    header_bytes = buf.getvalue().index('\n') + 1
    if (len(df)):
        avg_row_bytes = (len(buf.getvalue().encode('utf-8')) -
                         header_bytes) / len(df)
    else:
        avg_row_bytes = 0

    return {
        'size_estimate': (total_rows * avg_row_bytes) + header_bytes,
        'row_count': total_rows
    }


@download_router.post('/get_ranked_taxa_download', response_model=None)
async def get_ranked_taxa_download(
    params: DownloadRequestParams,
    request: Request,
) -> responses.StreamingResponse | dict[str, int | float] | None:
    """
    Download species/subspecies matching the given taxon IDs as a TSV.

    Matches on taxon_id or accepted_name_usage_id. Returns a size estimate
    instead of streaming if params.estimate is True.

    Args:
        params (DownloadRequestParams): Request parameters including taxon_ids and estimate flag.
        request (Request): FastAPI request, used to access the db pool.

    Returns:
        StreamingResponse of the TSV, or a dict with size_estimate and row_count.
    """

    taxon_ids = params.taxon_ids
    get_estimate = params.get_estimate
    token = params.token

    query = sql.SQL("""
        {dwc_taxa_select_clause}
        WHERE (
            {taxa_table}.taxon_id = ANY({taxon_ids}) OR
            {taxa_table}.accepted_name_usage_id = ANY({taxon_ids})
        )
        AND
            taxon_rank IN ('species', 'subspecies')
    """).format(
        dwc_taxa_select_clause=DWC_TAXA_SELECT_CLAUSE,
        taxa_table=sql.Identifier(TX_TAXA_TABLE.name),
        taxon_ids=sql.Literal(taxon_ids),
    )

    try:
        if get_estimate:
            async with request.app.state.db_pool.connection() as conn:
                return await estimate_tsv_download_size(conn, query)
        else:
            validation = validate_turnstile(
                token, settings.security.turnstile_key)
            print(validation)
            if validation['success'] == True:
                print(validation)
                return responses.StreamingResponse(
                    download_table_and_stream(request.app.state.db_pool,
                                              query, format='tsv'),
                    media_type='text/tab-separated-values',
                    headers={
                        'Content-Disposition': 'attachment; filename=taxa_download.tsv'
                    }
                )
            else:
                Exception("Turnstile validation failed.")
                raise HTTPException(status_code=400, detail=str(
                    "Turnstile validation failed."))
    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


def validate_turnstile(token, secret):
    url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

    data = {
        'secret': secret,
        'response': token
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Turnstile validation error: {e}")
        return {'success': False, 'error-codes': ['internal-error']}
