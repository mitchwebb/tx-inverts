import numpy as np
from backend.data_util.execute_psql_query import execute_psql_query
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.routers.taxa import RANK_ORDER, TaxonomicRank, RANK_COLS
from collections import deque, defaultdict
import pandas as pd
from typing import List
from psycopg import Connection, sql
from backend.core.logging import data_logger


async def get_observation_count(conn: Connection, taxon_ids: int | List[int]) -> int:
    """
    Returns the total number of GBIF observations for the given taxon ID(s).
    """

    if isinstance(taxon_ids, int):
        taxon_ids = [taxon_ids]

    query = sql.SQL("""
        SELECT COUNT(*)
        FROM {observations_table}
        WHERE taxon_key = ANY({taxon_ids})
    """).format(
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        taxon_ids=sql.Literal(taxon_ids)
    )

    result = await execute_psql_query(conn, query, fetch='one')
    return result[0]


# Numpy version of lineage building for backbone
def build_lineages_numpy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds taxonomic lineage columns for each taxon in the provided backbone DataFrame.

    For each taxon, propagates ancestor taxon IDs up through the hierarchy via BFS,
    populating one column per rank (e.g. kingdom_id, phylum_id, etc.). Synonyms are
    routed to their accepted taxon before lineage assignment.

    Requires the complete taxonomic backbone — partial DataFrames will produce incorrect lineages.

    Args:
        df (pd.DataFrame): Full taxanomic backbone from which the lineage columns will be derived

    Return:
        df with rank columns added, populated with respective taxon_ids
    """

    df = df.copy().reset_index(drop=True)

    ### Convert columns to NumPy arrays for speed ###

    # Use accepted_name_usage_id as taxon_id where available, fallback to taxon_id
    # This will make sure to always route synonyms back to their accepted taxon
    taxon_ids = np.where(
        # If non-na accepted_name_usage_id
        df["accepted_name_usage_id"].notna().to_numpy(),
        df["accepted_name_usage_id"].to_numpy(),  # Use accepted_name_usage_id
        # Else, default to taxon_id (taxa with null accepted_name_usage_id have accepted taxon_id)
        df["taxon_id"].to_numpy()
    )
    parent_ids = df["parent_name_usage_id"].to_numpy()

    ### Determine Ranks ###

    # Determine ranks for each entry
    # We must use the rank of their accepted_name_usage_id taxon
    # This helps correctly place synonyms that may have moved rank

    # Add an accepted_rank column
    rank_lookup = df.set_index("taxon_id")["taxon_rank"]
    accepted_ranks = rank_lookup.reindex(
        df["accepted_name_usage_id"]).to_numpy()
    # Generate ranks column from accepted_ranks when available, fallback to taxon_rank
    ranks = np.where(
        df["accepted_name_usage_id"].notna(),
        accepted_ranks,
        df["taxon_rank"].to_numpy()
    )

    # Generate numpy array for all taxa with columns for each taxon rank
    n_taxa = len(df)
    lineage = np.full((n_taxa, len(RANK_ORDER)), np.nan, dtype="float64")

    # Map taxon_id -> row index
    id_to_idx = {taxon_id: i for i, taxon_id in enumerate(taxon_ids)}

    # Build children map (by index)
    children_map = defaultdict(list)
    roots = []
    for i, parent_id in enumerate(parent_ids):
        if not pd.isna(parent_id) and parent_id in id_to_idx:
            parent_idx = id_to_idx[parent_id]
            children_map[parent_idx].append(i)
        else:
            roots.append(i)

    # Map rank -> column index
    rank_to_col_idx = {rank: i for i, rank in enumerate(RANK_ORDER)}

    # BFS traversal
    queue = deque(roots)
    while queue:
        i = queue.popleft()
        rank = ranks[i]
        parent_id = parent_ids[i]

        # Copy parent's lineage if exists
        if not pd.isna(parent_id) and parent_id in id_to_idx:
            parent_idx = id_to_idx[parent_id]
            lineage[i, :] = lineage[parent_idx, :]

        # Overwrite own rank column
        col_idx = rank_to_col_idx.get(rank)
        if col_idx is not None:
            lineage[i, col_idx] = taxon_ids[i]

        # Enqueue children
        queue.extend(children_map.get(i, []))

    # Convert lineage numpy table -> dataframe
    lineage_df = pd.DataFrame(lineage, columns=RANK_COLS)
    # Cast to Int64
    lineage_df = lineage_df.astype("Int64")

    # Assign columns back into df (overwrites existing columns)
    df[RANK_COLS] = lineage_df.values

    return df
