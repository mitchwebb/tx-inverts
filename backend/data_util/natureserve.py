from psycopg import Connection, sql
from backend.routers.taxa import TaxonomicRank
import psycopg
from backend.core.sql import create_occurrence_clause
from backend.models.sql import OccurrenceFilter
from backend.core.logging import data_logger


def calculate_rank(number_of_occurrences, range_extent, area_of_occupancy):
    """
        Given the minimum key three values, calculate NatureServe rank of a species

        args:
            number_of_occurrences (int): Count of occurrences of a species
            range_extent (int): Range extent of a given species in km2
            area_of_occupancy (int): Area of occupancy of a given species
    """
    points = 0

    # If all values are 0, species is data deficient
    # NatureServe doesn't actually have this ranking. This would be presumed extinct
    if (number_of_occurrences == 0 and range_extent == 0 and area_of_occupancy == 0):
        return "U"

    # According to IUCN, range_extent should be AT LEAST equal to area_of_occupancy
    if (range_extent < area_of_occupancy):
        range_extent = area_of_occupancy

    # If one of these values exists, all of them must at this point
    if (number_of_occurrences == 0 or range_extent == 0 or area_of_occupancy == 0):
        return "U"

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
    filters: OccurrenceFilter,
    taxon_rank: TaxonomicRank = 'species'
) -> dict | None:
    """
        Fetch range extent area (km²), number of occurrences, 
        total observation count, and area of occupancy bins (4km²) 
        for a requested taxon_id.

        Args:
            conn: async DB connection or context manager supporting async with
            taxon_ids: taxon key(s) to query

        Returns:
            dict with keys 'range_extent_km2', 
                           'number_of_occurrences', 
                           'observation_count', 
                           'area_of_occupancy_4km2_bins'
            or None if no data found
    """


    occurrence_clause = create_occurrence_clause(filters)

    rank_col = f'{taxon_rank}_id'

    query = sql.SQL("""
		WITH region AS (
			SELECT geometry
			FROM geometries
			WHERE geometry_name = 'Texas'
		),
		obs_points AS (
			SELECT
				ST_SetSRID(ST_MakePoint(decimal_longitude, decimal_latitude), 4326) AS geom,
				accepted_taxon_key,
                taxon_key,
                {rank_col}
			{occurrence_clause}
		),
        filtered_obs AS (
            SELECT p.geom, p.accepted_taxon_key
            FROM obs_points p, region r
            WHERE (p.{rank_col} = {taxon_id})
                AND p.geom && r.geometry
                AND ST_Intersects(p.geom, r.geometry)
        ),
		hull AS (
			SELECT
				ST_ConvexHull(ST_Collect(f.geom)) AS geom,
				COUNT(*) AS observation_count,
				COUNT(DISTINCT ROW(f.geom, f.accepted_taxon_key)) AS number_of_occurrences
			FROM filtered_obs f
		),
		aoo AS (
			SELECT COUNT(DISTINCT ST_SnapToGrid(ST_Transform(f.geom, 5070), 2000, 2000)) AS num_cells
			FROM filtered_obs f
		)
		SELECT
			COALESCE(
				ST_Area(
					ST_Transform(
						ST_Intersection(h.geom, r.geometry),
						5070
					)
				) / 1e6,
				0
			) AS range_extent_km2,
			h.observation_count,
			h.number_of_occurrences,
			a.num_cells AS area_of_occupancy_4km2_bins
		FROM hull h, region r, aoo a;
	""").format(
        taxon_id=sql.Literal(filters.taxon_id),
        rank_col=sql.Identifier(rank_col),
        include_inat=sql.Literal(filters.include_inat),
        occurrence_clause=occurrence_clause
    )

    async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(query, ())
        result = await cur.fetchone()
        return result
