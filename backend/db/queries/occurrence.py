# Shared sql query builders used across the txinverts API
from typing import List, Optional
from backend.data_util.helpers import normalize_to_list
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from psycopg import sql
from backend.models.occurrence import OccurrenceFilters


def create_occurrence_filter_sql(filter: OccurrenceFilters, skip_taxa: bool = False) -> sql.SQL | sql.Composed:
    """
    Takes OccurrenceFilters parameters and generates sql formatted
    clause for retrieving occurrence data

    Args:
        filter (OccurrenceFilters): Collection of parameters for filtering occurrence data
        skip_taxa (bool): Skips taxa filter if True, defaults to False

    Returns:
        occurrences_clause (sql.Composed | sql.SQL): a sql occurrence clause
    """

    # Create taxon_filter (unless skip_taxa == True, then set to 'TRUE' as a no-op condition)
    taxon_filter = sql.SQL("TRUE") if skip_taxa else create_occurrence_taxon_filter(
        filter.taxon_ids,
        filter.include_invasives
    )

    # If no individual datasets are selected, datasets_clause is empty
    if not filter.datasets:
        datasets_clause = sql.SQL("")
    # Else, require dataset_key in datasets filter
    else:
        dataset_literals = sql.SQL(", ").join(
            sql.Literal(p) for p in filter.datasets)
        datasets_clause = sql.SQL("AND dataset_key IN ({datasets})").format(
            datasets=dataset_literals
        )

    # If date_start provided, add clause, else skip
    if not filter.date_start:
        date_start_clause = sql.SQL("")
    else:
        date_start_clause = sql.SQL("AND collection_start_date >= {date_start}").format(
            date_start=sql.Literal(filter.date_start))

    # Same with date_end
    if not filter.date_end:
        date_end_clause = sql.SQL("")
    else:
        date_end_clause = sql.SQL("AND collection_end_date <= {date_end}").format(
            date_end=sql.Literal(filter.date_end))

    # If coord_uncertainty provided, add clause, else skip
    if filter.coord_uncertainty is None:
        uncertainty_clause = sql.SQL("")
    else:
        uncertainty_clause = sql.SQL(
            "AND (coordinate_uncertainty_in_meters IS NULL OR coordinate_uncertainty_in_meters <= {coord_uncertainty})"
        ).format(coord_uncertainty=sql.Literal(filter.coord_uncertainty))

    # If regions provided, add clause, else skip
    if not filter.regions:
        region_clause = sql.SQL("")
    else:
        region_literals = sql.SQL(", ").join(
            sql.Literal(r) for r in filter.regions)
        # Observations_regions_table contains each occurrence record matched to region_ids
        region_clause = sql.SQL("""
            AND EXISTS (
                SELECT 1 FROM {regions_table} r
                WHERE r.observation_id = {observations_table}.gbif_id
                AND r.region_id IN ({regions})
            )
        """).format(
            regions_table=sql.Identifier(OBSERVATION_REGIONS_TABLE.name),
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            regions=region_literals
        )

    # Piece it together
    occurrence_filter = sql.SQL("""
        {taxon_filter}
        AND ({include_inat} OR {observations_table}.institution_code != 'iNaturalist')
        {datasets_clause}
        AND (collection_start_date) IS NOT NULL
        {date_start_clause}
        {date_end_clause}
        {uncertainty_clause}
        {region_clause}
    """).format(
        include_inat=sql.Literal(filter.include_inat),
        datasets_clause=datasets_clause,
        date_start_clause=date_start_clause,
        date_end_clause=date_end_clause,
        region_clause=region_clause,
        taxon_filter=taxon_filter,
        uncertainty_clause=uncertainty_clause,
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
    )

    return occurrence_filter


# This is mostly just used in the occurrence clause, but is used in specific cases to
# create specialized requests
def create_occurrence_taxon_filter(taxon_ids: str | List[str] = 'N', include_invasives: Optional[bool] = False) -> sql.Composed | sql.SQL:
    """
    Takes taxon_ids and generates sql formatted clause to find occurrences with
    matching ids in occurrences table. This matches to taxa in any rank as long
    as they match the taxon_ids somewhere in their lineage.
    This filter does not pick up invasive taxa unless the taxon_id requested
    is, itself, an invasive taxon, or include_invasives is true.

    Args:
        taxon_ids (int | List[int]): Taxon ID of desired taxon. Defaults to 'N' (Animalia)
        include_invasives (bool): If True, invasive taxa are included in results. Defaults to False.

    Returns:
        full_taxon_clause (sql.Composed | sql.SQL): A sql clause for use in a WHERE body
    """

    # Normalize taxon_ids value to a list (in case an int was provided)
    taxon_ids = normalize_to_list(taxon_ids)

    # If no taxon_ids provided (Animalia), skip
    if taxon_ids == ['N']:
        # If include_invasives, skip with 'TRUE' no-op
        if include_invasives:
            return sql.SQL('TRUE')
        # Else, include just simplified invasives clause
        else:
            return sql.SQL("""
                NOT EXISTS (
                    SELECT 1 FROM {taxa_table}
                    WHERE {taxa_table}.taxon_id = {observations_table}.accepted_taxon_key
                    AND {taxa_table}.us_invasive = true
                )
            """).format(
                taxa_table=sql.Identifier(TX_TAXA_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            )

    # Construct main taxon clause to search for taxon_id in each rank_id column
    # This make sure we get oddly re-classified taxa
    lineage_clause = sql.SQL("""
        EXISTS (
            SELECT 1
            FROM {lineage_table} tl
            WHERE tl.accepted_taxon_key = {observations_table}.accepted_taxon_key
              AND tl.ancestor_id = ANY({taxon_ids})
        )
    """).format(
        lineage_table=sql.Identifier(TAXON_LINEAGE_TABLE.name),
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        taxon_ids=sql.Literal(taxon_ids)
    )

    # If we're including invasives, just return lineage_clause
    if include_invasives:
        return lineage_clause

    # Only accept taxa not labeled as invasive UNLESS the taxon_id requested is, itself, invasive
    invasive_clause = sql.SQL("""(
        NOT EXISTS (
            SELECT 1 from {taxa_table}
            WHERE {taxa_table}.taxon_id = {observations_table}.accepted_taxon_key
                AND {taxa_table}.us_invasive = true
        )
        OR {observations_table}.accepted_taxon_key = ANY({taxon_ids})
    )""").format(
        taxa_table=sql.Identifier(TX_TAXA_TABLE.name),
        taxon_ids=sql.Literal(taxon_ids),
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
    )

    full_taxon_clause = sql.SQL("{lineage_clause} AND {invasive_clause}").format(
        lineage_clause=lineage_clause,
        invasive_clause=invasive_clause
    )

    return full_taxon_clause
