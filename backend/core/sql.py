# Shared sql query builders used across the txinverts API

from typing import List, Optional
from backend.data_util.helpers import normalize_to_list
from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.tx_taxa import TX_TAXA_TABLE
from backend.models.sql import OccurrenceFilter
from psycopg import sql


def create_occurrence_filter(filter: OccurrenceFilter, include_invasives: Optional[bool] = False):
    """
    Takes OccurrenceFilter parameters and generates sql formatted
    clause for retrieving occurrence data

    Args:
        filter (OccurrenceFilter): Collection of parameters for filtering occurrence data

    Returns:
        occurrences_clause (str): sql.SQL() formatted clause
    """

    taxon_filter = create_occurrence_taxon_filter(
        filter.taxon_ids, include_invasives)
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
    occurrence_filter = sql.SQL('''
        {taxon_filter}
        AND ({include_inat} OR {observations_table}.institution_code != 'iNaturalist')
        {data_provider_clause}
        AND (collection_start_date) IS NOT NULL
        {date_start_clause}
        {date_end_clause}
    ''').format(
        include_inat=sql.Literal(filter.include_inat),
        data_provider_clause=data_provider_clause,
        date_start_clause=date_start_clause,
        date_end_clause=date_end_clause,
        taxon_filter=taxon_filter,
        observations_table=sql.Identifier(observations_table.name)
    )

    return occurrence_filter


# This is mostly just used in the occurrence clause, but is used in specific cases to
# create specialized requests
def create_occurrence_taxon_filter(taxon_ids: int | List[int], include_invasives: Optional[bool] = False):
    """
    Takes taxon_ids and generates sql formatted clause to find occurrences with
    matching ids in occurrences table. This matches to taxa in any rank as long
    as they match the taxon_ids somewhere in their lineage.
    This filter does not pick up invasive taxa unless the taxon_id requested
    is, itself, an invasive taxon, or include_invasives is true.

    Args:
        taxon_ids (int): Taxon ID of desired taxon
        inclue_invasives (optional, boolean): Whether to include invasives subspecies

    Returns:
        taxon_clause (str): sql.SQL() formatted clause
    """

    taxon_ids = normalize_to_list(taxon_ids)

    taxa_table = TX_TAXA_TABLE
    observations_table = GBIF_OBSERVATIONS_TABLE

    # Construct main taxon clause to search for taxon_id in each rank_id column
    # This make sure we get oddly re-classified taxa
    lineage_clause = sql.SQL('''( 
           {observations_table}.accepted_taxon_key = ANY({taxon_ids})
        OR {observations_table}.kingdom_id         = ANY({taxon_ids})
        OR {observations_table}.phylum_id          = ANY({taxon_ids})
        OR {observations_table}.class_id           = ANY({taxon_ids})
        OR {observations_table}.order_id           = ANY({taxon_ids})
        OR {observations_table}.family_id          = ANY({taxon_ids})
        OR {observations_table}.genus_id           = ANY({taxon_ids})
        OR {observations_table}.species_id         = ANY({taxon_ids})
        OR {observations_table}.subspecies_id      = ANY({taxon_ids})
        )
    ''').format(
        taxon_ids=sql.Literal(taxon_ids),
        observations_table=sql.Identifier(observations_table.name)
    )

    # Only accept taxa not labeled as invasive UNLESS the taxon_id requested is, itself, invasive
    invasive_clause = sql.SQL('''(
        NOT EXISTS (
            SELECT 1 from {taxa_table}
            WHERE {taxa_table}.taxon_id = {observations_table}.accepted_taxon_key
                AND {taxa_table}.us_invasive = true
        )
        OR {observations_table}.accepted_taxon_key = ANY({taxon_ids})
    )''').format(
        taxa_table=sql.Identifier(taxa_table.name),
        taxon_ids=sql.Literal(taxon_ids),
        observations_table=sql.Identifier(observations_table.name)
    )

    if include_invasives:
        taxon_clause = lineage_clause
    else:
        taxon_clause = sql.SQL("{lineage_clause} AND {invasive_clause}").format(
            lineage_clause=lineage_clause,
            invasive_clause=invasive_clause
        )

    return taxon_clause


DWC_OCCURRENCE_SELECT_CLAUSE = sql.SQL('''
    SELECT
        gbif_id AS "gbifID",
        access_rights AS "accessRights",
        license,
        modified,
        publisher,
        "references",
        rights_holder AS "rightsHolder",
        recorded_by AS "recordedBy",
        dataset_id AS "datasetID",
        institution_code AS "institutionCode",
        dataset_name AS "datasetName",
        information_withheld AS "informationWithheld",
        occurrence_id AS "occurrenceID",
        individual_count AS "individualCount",
        event_date AS "eventDate",
        event_time AS "eventTime",
        year,
        month,
        day,
        verbatim_event_date AS "verbatimEventDate",
        field_notes AS "fieldNotes",
        event_remarks AS "eventRemarks",
        country_code AS "countryCode",
        state_province AS "stateProvince",
        county,
        locality,
        verbatim_locality AS "verbatimLocality",
        decimal_latitude AS "decimalLatitude",
        decimal_longitude AS "decimalLongitude",
        coordinate_uncertainty_in_meters AS "coordinateUncertaintyInMeters",
        coordinate_precision AS "coordinatePrecision",
        scientific_name AS "scientificName",
        kingdom,
        phylum,
        class,
        "order",
        family,
        genus,
        species,
        subspecies,
        taxon_rank AS "taxonRank",
        taxonomic_status AS "taxonomicStatus",
        dataset_key AS "datasetKey",
        last_interpreted AS "lastInterpreted",
        issue,
        taxon_key,
        accepted_taxon_key AS "acceptedTaxonKey",
        accepted_scientific_name AS "acceptedScientificName",
        verbatim_scientific_name AS "verbatimScientificName",
        collection_start_date as "collectionStartDate",
        collection_end_date as "collectionEndDate"
    FROM {gbif_table}
''').format(gbif_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name))

DWC_TAXA_SELECT_CLAUSE = sql.SQL('''
    SELECT
        taxon_id AS "taxonID",
        dataset_id AS "datasetID",
        parent_name_usage_id AS "parentName",
        accepted_name_usage_id AS "acceptedNameUsageID",
        original_name_usage_id AS "originalNameUsageID",
        scientific_name AS "scientificName",
        scientific_name_authorship AS "scientificNameAuthorship",
        canonical_name AS "canonicalName",
        generic_name AS "genericName",
        taxon_rank AS "taxonRank",
        name_published_in AS "namePublishedIn",
        taxonomic_status AS "taxonomicStatus",
        taxon_remarks AS "taxonRemarks",
        kingdom,
        phylum,
        class,
        "order",
        family,
        genus,
        species,
        subspecies,
        ns_rank_state AS "rankState",
        ns_rank_state_no_inat AS "rankStateNoINat",
        us_invasive AS "uSInvasive"
    FROM {backbone}            
''').format(backbone=sql.Identifier(TX_TAXA_TABLE.name))
