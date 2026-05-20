from http.client import HTTPException
from typing import Literal

from backend.db.queries.dwc import DWC_TAXA_SELECT_CLAUSE, DWC_OCCURRENCE_SELECT_CLAUSE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.models.api import DownloadRequestParams
from fastapi import APIRouter, Request, responses
from psycopg import sql, AsyncConnection
from backend.data_util.execute_psql_query import execute_psql_query
from backend.core.logging import api_logger
import pandas as pd
import io

downloads_router = APIRouter()


# # Downloads WILL include data for invasive species
# @downloads_router.post('/get_occurrence_download')
# async def get_occurrence_download(params: DownloadRequestParams, request: Request):
#     taxon_ids = params.taxon_ids
#     include_inat = params.include_inat
#     date_start = params.date_start
#     date_end = params.date_end
#     datasets = params.datasets
#     include_invasives = params.include_invasives
#     estimate = params.estimate

#     filter_payload = OccurrenceFilter(
#         taxon_ids=taxon_ids,
#         include_inat=include_inat,
#         datasets=datasets,
#         date_start=date_start,
#         date_end=date_end
#     )

#     api_logger.info('getting occurrence download...')

#     occurrence_filter = create_occurrence_filter(
#         filter_payload, include_invasives)

#     query = sql.SQL("""
#         {dwc_occurrence_select_clause}
#         WHERE
#             {occurrence_filter}
#     """).format(
#         dwc_occurrence_select_clause=DWC_OCCURRENCE_SELECT_CLAUSE,
#         occurrence_filter=occurrence_filter
#     )

#     try:
#         if estimate:
#             async with request.app.state.db_pool.connection() as conn:
#                 return await estimate_tsv_download_size(conn, query)
#         else:
#             return responses.StreamingResponse(
#                 downloadAndStream(request.app.state.db_pool,
#                                   query, format='tsv'),
#                 media_type='text/tab-separated-values',
#                 headers={
#                     'Content-Disposition': 'attachment; filename=taxa_download.tsv'
#                 }
#             )
#     except Exception as e:
#         api_logger.exception(e)
#         raise HTTPException(status_code=500, detail=str(e))


@downloads_router.post('/get_ranked_taxa_download')
async def get_ranked_taxa_download(params: DownloadRequestParams, request: Request):
    taxon_ids = params.taxon_ids
    estimate = params.estimate

    taxa_table = TX_TAXA_TABLE

    query = sql.SQL("""
        {dwc_taxa_select_clause}
        WHERE
            {taxa_table}.taxon_id = ANY({taxon_ids}) OR
            {taxa_table}.accepted_name_usage_id = ANY({taxon_ids})
        AND
            taxon_rank IN ('species', 'subspecies')
    """).format(
        dwc_taxa_select_clause=DWC_TAXA_SELECT_CLAUSE,
        taxa_table=sql.Identifier(taxa_table.name),
        taxon_ids=sql.Literal(taxon_ids),
    )

    try:
        if estimate:
            async with request.app.state.db_pool.connection() as conn:
                return await estimate_tsv_download_size(conn, query)
        else:
            return responses.StreamingResponse(
                downloadTableAndStream(request.app.state.db_pool,
                                       query, format='tsv'),
                media_type='text/tab-separated-values',
                headers={
                    'Content-Disposition': 'attachment; filename=taxa_download.tsv'
                }
            )
    except Exception as e:
        api_logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


async def downloadTableAndStream(pool, query: str, format: Literal['csv', 'tsv']):
    async with pool.connection() as conn:
        # Using raw cursor here for copy
        async with conn.cursor() as cur:
            if format == 'tsv':
                delimiter_sql = sql.SQL("E'\\t'")
            else:
                delimiter_sql = sql.SQL("','")
            copy_sql = sql.SQL("""
                COPY (
                    {query}
                ) TO STDOUT
                WITH (
                    FORMAT CSV,
                    DELIMITER {delimiter},
                    HEADER TRUE
                )
            """).format(query=query, delimiter=delimiter_sql)

            async with cur.copy(copy_sql) as copy:
                async for chunk in copy:
                    yield chunk


async def estimate_tsv_download_size(conn: AsyncConnection, query: sql.Composed):
    # Get accurate row count
    count_query = sql.SQL(
        "SELECT COUNT(*) FROM ({query}) AS t").format(query=query)
    result = await execute_psql_query(conn, count_query, fetch='one')
    total_rows = result[0]

    # Sample a few rows to get realistic avg byte size including headers
    sample_query = sql.SQL(
        "SELECT * FROM ({query}) AS t LIMIT 100").format(query=query)

    sample = await execute_psql_query(conn, sample_query, fetch='all')

    df = pd.DataFrame(sample)
    buf = io.StringIO()
    df.to_csv(buf, sep='\t', index=False)
    header_bytes = buf.getvalue().index('\n') + 1
    if (len(df)):
        avg_row_bytes = (buf.tell() - header_bytes) / len(df)
    else:
        avg_row_bytes = 0

    return {
        'size_estimate': (total_rows * avg_row_bytes) + header_bytes,
        'row_count': total_rows
    }
