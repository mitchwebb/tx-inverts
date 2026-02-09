import numpy as np
from backend.routers.taxa import RANK_ORDER, TaxonomicRank, RANK_COLS, get_taxon_rank
from collections import deque, defaultdict
import pandas as pd
from typing import List
from psycopg import Connection, sql


# async def get_all_descendant_ids(conn: Connection, taxon_id: int):
#     rank = await get_taxon_rank(conn, taxon_id)

#     rank_col = f'{rank}_id'

#     query = sql.SQL('''
#         SELECT COALESCE(accepted_name_usage_id, taxon_id)
#         FROM tx_taxa
#         WHERE {rank_col} IN (
#             SELECT taxon_id
#             FROM tx_taxa
#             WHERE accepted_name_usage_id = {taxon_id}
#         )
#     ''').format(
#         rank_col=sql.Identifier(rank_col),
#         taxon_id=sql.Literal(taxon_id)
#     )

#     async with conn.cursor() as cur:
#         await cur.execute(query)
#         result = await cur.fetchall()
#         result = [r[0] for r in result]
#         return result


async def get_observation_count(conn: Connection, taxon_ids: int | List[int]):
    query = '''
        SELECT COUNT(*)
        FROM gbif_observations
        WHERE taxon_key = ANY(%s)
    '''

    async with conn.cursor() as cur:
        await cur.execute(query, (taxon_ids, ))
        result = await cur.fetchone()
        return result[0]


def build_lineages(df: pd.DataFrame) -> pd.DataFrame:
    # parent -> [children] map
    children_map = defaultdict(list)
    roots = []

    print('Collecting root taxa...')
    # Collect roots and build lineage maps
    for taxon_id, parent in zip(df["taxon_id"].values, df["parent_name_usage_id"].values):
        if pd.notna(parent):
            children_map[parent].append(taxon_id)
        else:
            roots.append(taxon_id)

    # initialize queue with roots (kingdoms etc.)
    queue = deque(roots)
    df = df.set_index("taxon_id")

    print('Building lineage map...')
    while queue:
        taxon_id = queue.popleft()
        row = df.loc[taxon_id]
        curr_rank: TaxonomicRank = row['taxon_rank']
        curr_col = f'{curr_rank}_id'
        parent_id = row["parent_name_usage_id"]

        # copy all parent's lineage columns in one vectorized assignment
        if pd.notna(parent_id) and parent_id in df.index:
            df.loc[taxon_id, RANK_COLS] = df.loc[parent_id, RANK_COLS].values

        # overwrite own rank
        if pd.notna(curr_rank) and curr_rank in RANK_ORDER:
            df.loc[taxon_id, curr_col] = taxon_id

            # enqueue children
        for child in children_map.get(taxon_id, []):
            queue.append(child)

    return df.reset_index(drop=False)


# TODO: Could we do this --JUST-- for tx_taxa?
# TODO: We could DOWNLOAD it and run it, and then insert values, but...
def build_lineages_numpy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().reset_index(drop=True)

    # Convert columns to NumPy arrays for speed
    # Use accepted_name_usage_id where available, default to taxon_id
    # This will make sure to always route synonyms back to their accepted taxon
    taxon_ids = np.where(
        df["accepted_name_usage_id"].notna().to_numpy(),
        df["accepted_name_usage_id"].to_numpy(),
        df["taxon_id"].to_numpy()
    )
    parent_ids = df["parent_name_usage_id"].to_numpy()

    # Determine ranks for each entry using the rank of their accepted_name_usage_id taxon
    # This helps correctly place synonyms that may have moved rank

    # Safely add an accepted_rank column
    rank_lookup = df.set_index("taxon_id")["taxon_rank"]
    accepted_ranks = rank_lookup.reindex(
        df["accepted_name_usage_id"]).to_numpy()

    ranks = np.where(
        df["accepted_name_usage_id"].notna(),
        accepted_ranks,
        df["taxon_rank"].to_numpy()
    )

    n_taxa = len(df)
    lineage = np.full((n_taxa, len(RANK_ORDER)), np.nan, dtype="float64")

    # Map taxon_id -> row index
    id_to_idx = {tid: i for i, tid in enumerate(taxon_ids)}

    # Build children map (by index)
    children_map = defaultdict(list)
    roots = []
    for i, pid in enumerate(parent_ids):
        if not pd.isna(pid) and pid in id_to_idx:
            parent_idx = id_to_idx[pid]
            children_map[parent_idx].append(i)
        else:
            roots.append(i)

    # BFS traversal
    queue = deque(roots)
    while queue:
        i = queue.popleft()
        rank = ranks[i]
        parent_id = parent_ids[i]

        # Copy parent's lineage if exists
        if not pd.isna(parent_id) and parent_id in id_to_idx:
            p_idx = id_to_idx[parent_id]
            lineage[i, :] = lineage[p_idx, :]

        # Overwrite own rank column
        if pd.notna(rank) and rank in RANK_ORDER:
            col_idx = RANK_ORDER.index(rank)
            lineage[i, col_idx] = taxon_ids[i]

        # Enqueue children
        queue.extend(children_map.get(i, []))

    # convert lineage numpy -> dataframe, then to pandas nullable ints
    lineage_df = pd.DataFrame(lineage, columns=RANK_COLS)
    # vectorized cast instead of per-column loop
    lineage_df = lineage_df.astype("Int64")

    # assign columns back into df (overwrites existing ones cleanly)
    for col in RANK_COLS:
        df[col] = lineage_df[col].values

    return df
