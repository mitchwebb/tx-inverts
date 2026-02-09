from os import name
from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.tx_taxa import TX_TAXA_TABLE
from backend.models.sql import OccurrenceFilter
from psycopg import sql


def create_occurrence_clause(filter: OccurrenceFilter):

    taxon_filter = create_taxon_filter(filter)
    observations_table = GBIF_OBSERVATIONS_TABLE

    # If no individual data providers are selected
    if not filter.data_providers:
        data_provider_clause = sql.SQL('')  # empty condition
    else:
        provider_literals = sql.SQL(', ').join(
            sql.Literal(p) for p in filter.data_providers)
        data_provider_clause = sql.SQL('AND institution_code IN ({providers})').format(
            providers=provider_literals
        )

    if not filter.date_start:
        date_start_clause = sql.SQL('')
    else:
        date_start_clause = sql.SQL('AND collection_start_date >= {date_start}').format(
            date_start=sql.Literal(filter.date_start))

    if not filter.date_end:
        date_end_clause = sql.SQL('')
    else:
        date_end_clause = sql.SQL('AND collection_end_date <= {date_end}').format(
            date_end=sql.Literal(filter.date_end))

    # Checking each column is slightly safer than just referring to the accepted_taxon_key, as
    # GBIF doesn't ALWAYS resolve synonyms cleanly
    occurrences_clause = sql.SQL('''
        FROM gbif_observations
        WHERE 
            {taxon_filter}
            AND ({include_inat} OR {observations_table}.institution_code != 'iNaturalist')
            {data_provider_clause}
            AND (collection_start_date) IS NOT NULL
            {date_start_clause}
            {date_end_clause}

    ''').format(
        taxon_id=sql.Literal(filter.taxon_id),
        include_inat=sql.Literal(filter.include_inat),
        data_provider_clause=data_provider_clause,
        date_start_clause=date_start_clause,
        date_end_clause=date_end_clause,
        taxon_filter=taxon_filter,
        observations_table=sql.Identifier(observations_table.name)
    )

    return occurrences_clause


# Get list of providers and their specimen count for a certain taxon
# Keep provider name with 0 count if they have the taxon, but it is filtered out
def create_taxon_filter(filters: OccurrenceFilter):

    taxa_table = TX_TAXA_TABLE
    observations_table = GBIF_OBSERVATIONS_TABLE

    # Construct main taxon clause to search for taxon_id in each rank_id column
    # This make sure we get oddly re-classified taxa
    taxon_clause = sql.SQL('''( 
           {observations_table}.accepted_taxon_key = {taxon_id}
        OR {observations_table}.kingdom_id         = {taxon_id}
        OR {observations_table}.phylum_id          = {taxon_id}
        OR {observations_table}.class_id           = {taxon_id}
        OR {observations_table}.order_id           = {taxon_id}
        OR {observations_table}.family_id          = {taxon_id}
        OR {observations_table}.genus_id           = {taxon_id}
        OR {observations_table}.species_id         = {taxon_id}
        OR {observations_table}.subspecies_id      = {taxon_id}
        )
    ''').format(
        taxon_id=sql.Literal(filters.taxon_id),
        observations_table=sql.Identifier(observations_table.name)
    )

    # Only accept taxa not labeled as invasive UNLESS the taxon_id requested is, itself, invasive
    invasive_clause = sql.SQL('''(
        NOT EXISTS (
            SELECT 1 from {taxa_table}
            WHERE {taxa_table}.taxon_id = {observations_table}.accepted_taxon_key
                AND {taxa_table}.us_invasive = true
        )
        OR {taxon_id} = {observations_table}.accepted_taxon_key
    )''').format(
        taxa_table=sql.Identifier(taxa_table.name),
        taxon_id=sql.Literal(filters.taxon_id),
        observations_table=sql.Identifier(observations_table.name)
    )

    total_clause = sql.SQL("{taxon_clause} AND {invasive_clause}").format(
        taxon_clause=taxon_clause,
        invasive_clause=invasive_clause
    )

    return total_clause
