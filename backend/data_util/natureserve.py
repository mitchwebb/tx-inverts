from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.geometries import TEXAS_GEOMETRY_TABLE
from backend.models.api_types import NSRank
from psycopg import Connection, sql
from backend.routers.taxa import TaxonomicRank
import psycopg
from backend.core.sql import create_occurrence_filter
from backend.models.sql import SingleTaxonOccurrenceFilter
from backend.core.logging import api_logger


def calculate_rank(number_of_occurrences, range_extent, area_of_occupancy) -> NSRank:
    """
        Given the minimum key three values, calculate NatureServe-type rank of a species

        args:
            number_of_occurrences (int): Count of occurrences of a species
            range_extent (int): Range extent of a given species in km2
            area_of_occupancy (int): Area of occupancy of a given species
        returns:
            ns_rank (NSRank): NatureServe-type rank of species
    """
    points = 0

    # If all values are 0, species is data deficient
    # NatureServe doesn't actually have this ranking. This would be presumed extinct
    if (number_of_occurrences == 0 and range_extent == 0 and area_of_occupancy == 0):
        return "u"

    # According to IUCN, range_extent should be AT LEAST equal to area_of_occupancy
    if (range_extent < area_of_occupancy):
        range_extent = area_of_occupancy

    # If one of these values exists, all of them must at this point
    if (number_of_occurrences == 0 or range_extent == 0 or area_of_occupancy == 0):
        return "u"

    if number_of_occurrences == 0:  # NatureServe Z Value
        points += 0.00
    elif 0 < number_of_occurrences <= 5:  # NatureServe A Value
        points += 0.00
    elif 5 < number_of_occurrences <= 20:  # NatureServe B Value
        points += 1.38
    elif 20 < number_of_occurrences <= 80:  # NatureServe C Value
        points += 2.75
    elif 80 < number_of_occurrences <= 300:  # NatureServe D Value
        points += 4.13
    elif 300 < number_of_occurrences:  # NatureServe E Value
        points += 5.50

    # These point values are doubled, as NatureServe gives them a weight of 2
    if area_of_occupancy == 0:  # NatureServe Z Value
        points += 0.00 * 2
    elif 0 < area_of_occupancy <= 1:  # NatureServe A Value
        points += 0.00 * 2
    elif 1 < area_of_occupancy <= 2:  # NatureServe B Value
        points += 0.69 * 2
    elif 2 < area_of_occupancy <= 5:  # NatureServe C Value
        points += 1.38 * 2
    elif 5 < area_of_occupancy <= 25:  # NatureServe D Value
        points += 2.06 * 2
    elif 25 < area_of_occupancy <= 125:  # NatureServe E Value
        points += 2.75 * 2
    elif 125 < area_of_occupancy <= 500:  # NatureServe F Value
        points += 3.44 * 2
    elif 500 < area_of_occupancy <= 2500:  # NatureServe G Value
        points += 4.13 * 2
    elif 2500 < area_of_occupancy <= 12500:  # NatureServe H Value
        points += 4.81 * 2
    elif 12500 < area_of_occupancy:  # NatureServe I Value
        points += 5.50 * 2

    if range_extent == 0:  # NatureServe Z Value
        points += 0.00
    elif 0 < range_extent <= 100:  # NatureServe A Value
        points += 0.00
    elif 100 < range_extent <= 250:  # NatureServe B Value
        points += 0.79
    elif 250 < range_extent <= 1000:  # NatureServe C Value
        points += 1.57
    elif 1000 < range_extent <= 5000:  # NatureServe D Value
        points += 2.36
    elif 5000 < range_extent <= 20000:  # NatureServe E Value
        points += 3.14
    elif 20000 < range_extent <= 200000:  # NatureServe F Value
        points += 3.93
    elif 200000 < range_extent <= 2500000:  # NatureServe G Value
        points += 4.71
    elif 2500000 < range_extent:  # NatureServe H Value
        points += 5.50

    three_average_score = points / 4

    # This is terminology taken from NatureServe ranking calculator
    # In this case, 'range' refers to the difference between low/high
    # ranking estimates.
    # With our parameters, there is no estimate range, hence 'zero_range'
    zero_range_rank = 0

    if three_average_score <= 1.5:
        zero_range_rank = 1
    elif three_average_score <= 2.5:
        zero_range_rank = 2
    elif three_average_score <= 3.5:
        zero_range_rank = 3
    elif three_average_score <= 4.5:
        zero_range_rank = 4
    elif three_average_score > 4.5:
        zero_range_rank = 5

    return (zero_range_rank)


# TODO: Minimum convex polygon vs a-hull (https://help.natureserve.org/biotics/Content/Record_Management/Element_Files/Element_Ranking/ERANK_Definitions_of_Extent_of_Occurrence_and_Area_of_Occupancy.htm)
# TODO: Round up Range Extent to match AOO minimum
# Separated from router to allow command line or other direct access
async def calculate_ns_values(
    conn: Connection,
    filters: SingleTaxonOccurrenceFilter,
    taxon_rank: TaxonomicRank = 'species'
) -> dict | None:
    """
        Fetch range extent area (km²), number of occurrences,
        total observation count, and area of occupancy bins (4km²)
        for a requested taxon_id.

        Args:
            conn (Connection): async DB connection or context manager supporting async with
            filters (SingleTaxonOccurrenceFilter): Occurrence filters, with taxon_ids being a single taxon_id
            taxon_rank (TaxonomicRank): The rank of the queried taxon, defaults to 'species'

        Returns:
            dict with keys 'range_extent_km2',
                           'number_of_occurrences',
                           'observation_count',
                           'area_of_occupancy_4km2_bins',
                           'area_of_occupancy_1km2_bins'
            or None if no data found
    """

    try:
        occurrence_filter = create_occurrence_filter(filters, skip_taxa=True)

        # Occurrences is only a useful metric for species and subspecies
        # We'll include genus as well, because why not
        compute_occurrences = taxon_rank in {"genus", "species", "subspecies"}

        if compute_occurrences:
            obs_source = sql.SQL('''(
                SELECT 
                    geometry,
                    geom_5070,
                    ST_ClusterDBSCAN(geom_5070, eps := 1000, minpoints := 1) OVER () AS cluster_id
                FROM filtered_obs
            ) clustered''')
            occ_expression = sql.SQL("COUNT(DISTINCT cluster_id)")
        else:
            obs_source = sql.SQL("filtered_obs")
            occ_expression = sql.SQL("NULL::bigint")

        query = sql.SQL('''
            WITH matching_taxa AS MATERIALIZED (
                SELECT accepted_taxon_key
                FROM taxon_lineage
                WHERE ancestor_id = {taxon_id}
            ),
            filtered_obs AS MATERIALIZED (
                SELECT 
                    {occurrence_table}.geometry, 
                    ST_Transform({occurrence_table}.geometry, 5070) AS geom_5070,
                    {occurrence_table}.accepted_taxon_key
                FROM {occurrence_table}
                JOIN matching_taxa t ON {occurrence_table}.accepted_taxon_key = t.accepted_taxon_key
                WHERE {occurrence_filter}
            ),
            region AS (
                SELECT geometry
                FROM {tx_table}
                WHERE state = 'Texas'
            ),
            values AS (
                SELECT
                    COUNT(*) AS observation_count,
                    {occ_expression} AS number_of_occurrences,
                    COUNT(DISTINCT ST_SnapToGrid(geom_5070, 2000, 2000)) AS a4_cells,
                    COUNT(DISTINCT ST_SnapToGrid(geom_5070, 1000, 1000)) AS a1_cells,
                    ST_Collect(geometry) AS geom_collection
                FROM {obs_source}
            ),
            hull AS (
                SELECT ST_ConvexHull(geom_collection) AS geometry
                FROM values
            )
            SELECT
                COALESCE(
                    ST_Area(
                        ST_Transform(
                            ST_Intersection(hull.geometry, region.geometry),
                            5070
                        )
                    ) / 1e6,
                    0
                ) AS range_extent_km2,
                values.observation_count,
                values.number_of_occurrences,
                values.a4_cells AS area_of_occupancy_4km2_bins,
                values.a1_cells AS area_of_occupancy_1km2_bins
            FROM values, hull, region
        ''').format(
            tx_table=sql.Identifier(TEXAS_GEOMETRY_TABLE.name),
            taxon_id=sql.Literal(filters.taxon_id),
            include_inat=sql.Literal(filters.include_inat),
            occurrence_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            occurrence_filter=occurrence_filter,
            obs_source=obs_source,
            occ_expression=occ_expression
        )

        print(query.as_string(conn))

        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            await cur.execute("SET LOCAL work_mem = '256MB'")
            await cur.execute(query, ())
            result = await cur.fetchone()
            return result
    except Exception as e:
        api_logger.exception(e)
