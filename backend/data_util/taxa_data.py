from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.helpers import normalize_to_list
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
import pandas as pd
from typing import List
from psycopg import AsyncConnection, sql


CHORDATE_INVERTS = ('Thaliacea', 'Ascidiacea', 'Appendicularia', 'Leptocardii')
CHORDATE_INVERT_IDS = (
    # Classes
    'L2QHG',  # Thaliacea
    'B8V3P',  # Ascidiacea
    '622C5',  # Appendicularia
    'DR',     # Leptocardii
    # Subphyla
    '7NF2Q',   # Cephalochordata
    '7NF2Z',   # Tunicata
    # Phyla
    'CH2',     # Chordata
)


def inverts_mask(df: pd.DataFrame) -> pd.Series:
    """True for Animalia rows that are invertebrates (or the exceptional invert chordates)."""

    # Must be animalia
    animalia = (
        (df['kingdom'] == 'Animalia') |
        # Make sure Animalia itself gets included (Catalogue of Life leaves the 'kingdom' column as NaN)
        (df['taxonID'] == 'N')
    )

    # Exceptions to the rule of 'non-chordate'
    exceptional = (
        # Any that match class names in scientificName column
        df['scientificName'].str.split().str[0].isin(CHORDATE_INVERTS) |
        # Any that match class names in 'class' columns
        df['class'].isin(CHORDATE_INVERTS) |
        # And that match taxonID (includes parents)
        df['taxonID'].isin(CHORDATE_INVERT_IDS)
    )

    return animalia & (
        (df['phylum'] != 'Chordata') |
        exceptional
    )


async def taxon_exists(conn: AsyncConnection, taxon_id: str) -> bool:
    """Small helper to check existence of taxon_id in backbone"""

    result = await execute_psql_query(
        conn,
        sql.SQL("""
            SELECT EXISTS(
                SELECT 1 FROM {backbone}
                WHERE taxon_id = {taxon_id}
            )
        """).format(
            backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            taxon_id=sql.Literal(taxon_id)
        ),
        fetch='one'
    )

    return result[0] if result else False


async def get_observation_count(conn: AsyncConnection, taxon_ids: str | List[str]) -> int | None:
    """
    Returns the total number of GBIF observations for the given taxon ID(s).
    """

    # Normalize taxon_ids to list (handles single ints)
    taxon_ids = normalize_to_list(taxon_ids)

    query = sql.SQL("""
        SELECT COUNT(*)
        FROM {observations_table}
        WHERE taxon_key = ANY({taxon_ids})
    """).format(
        observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
        taxon_ids=sql.Literal(taxon_ids)
    )

    result = await execute_psql_query(conn, query, fetch='one')

    return int(result[0]) if result else None


def create_canonical_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Using a pandas DataFrame, add a 'canonicalName' column
    populated with scientific names WITHOUT authorship.

    This is done by combining column data or by stripping
    the scientificName column, depending on taxonRank. 

    Columns required:
        'scientificName',
        'genericName',
        'infragenericEpithet',
        'specificEpithet',
        'infraspecificEpithet',
        'taxonRank'
    """
    required_cols = {
        'scientificName',
        'genericName',
        'infragenericEpithet',
        'specificEpithet',
        'infraspecificEpithet',
        'taxonRank'
    }

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f'DataFrame is missing required columns: {missing}')

    def derive_canonical_name(row):
        taxon_rank = row['taxonRank']
        match taxon_rank:
            case 'species':
                parts = [row['genericName'], row['specificEpithet']]
            case 'subspecies':
                parts = [
                    row['genericName'],
                    row['specificEpithet'],
                    row['infraspecificEpithet']
                ]
            case _:
                if pd.isna(row['scientificName']):
                    return pd.NA
                return row['scientificName'].split(' ', 1)[0]

        # If the names we've made contain NaN parts, it has failed and we need to return NaN
        if any(pd.isna(p) for p in parts):
            return pd.NA

        return ' '.join(parts)

    df['canonicalName'] = df.apply(
        lambda row: derive_canonical_name(row), axis=1)

    return df

# # Numpy version of lineage building for backbone
# def build_lineages(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Builds taxonomic lineage columns for each taxon in the provided backbone DataFrame.

#     For each taxon, propagates ancestor taxon IDs up through the hierarchy via BFS,
#     populating one column per rank(e.g. kingdom_id, phylum_id, etc.). Synonyms are
#     routed to their accepted taxon before lineage assignment.

#     Requires the complete taxonomic backbone — partial DataFrames will produce incorrect lineages.

#     Args:
#         df(pd.DataFrame): Full taxanomic backbone from which the lineage columns will be derived

#     Return:
#         df with rank columns added, populated with respective taxon_ids
#     """

#     # Reset indexes (normal indexes are used later, and no need to preserve old indexes)
#     df = df.copy().reset_index(drop=True)

#     ### Convert columns to NumPy arrays for speed ###

#     # Use accepted_name_usage_id as taxon_id where available, fallback to taxon_id
#     # This will make sure to always route synonyms back to their accepted taxon
#     taxon_ids = np.where(
#         # If non-na accepted_name_usage_id
#         df['accepted_name_usage_id'].notna().to_numpy(),
#         df['accepted_name_usage_id'].to_numpy(),  # Use accepted_name_usage_id
#         # Else, default to taxon_id (taxa with null accepted_name_usage_id have accepted taxon_id)
#         df['taxon_id'].to_numpy()
#     ).tolist()
#     parent_ids = df['parent_name_usage_id'].to_numpy()

#     ### Determine Ranks ###

#     # Determine ranks for each entry
#     # We must use the rank of their accepted_name_usage_id taxon
#     # This helps correctly place synonyms that may have moved rank

#     # Add an accepted_rank column
#     rank_lookup = df.set_index('taxon_id')['taxon_rank']
#     accepted_ranks = rank_lookup.reindex(
#         df['accepted_name_usage_id']).to_numpy()
#     # Generate ranks column from accepted_ranks when available, fallback to taxon_rank
#     ranks = np.where(
#         df['accepted_name_usage_id'].notna(),
#         accepted_ranks,
#         df['taxon_rank'].to_numpy()
#     )

#     # Generate numpy array for all taxa with columns for each taxon rank
#     n_taxa = len(df)
#     lineage = np.full((n_taxa, len(RANK_ORDER)), np.nan, dtype=object)

#     # Map taxon_id -> row index
#     id_to_idx = {df['taxon_id'].iloc[i]: i for i in range(n_taxa)}

#     # Build children map (by index)
#     children_map = defaultdict(list)
#     roots = []
#     for i, parent_id in enumerate(parent_ids):
#         if not pd.isna(parent_id) and parent_id in id_to_idx:
#             parent_idx = id_to_idx[parent_id]
#             children_map[parent_idx].append(i)
#         else:
#             roots.append(i)

#     # Map rank -> column index
#     rank_to_col_idx = {rank: i for i, rank in enumerate(RANK_ORDER)}

#     # BFS traversal
#     queue = deque(roots)
#     while queue:
#         i = queue.popleft()
#         rank = str(ranks[i])
#         parent_id = parent_ids[i]

#         # Copy parent's lineage if exists
#         if not pd.isna(parent_id) and parent_id in id_to_idx:
#             parent_idx = id_to_idx[parent_id]
#             lineage[i, :] = lineage[parent_idx, :]

#         # Overwrite own rank column
#         col_idx = rank_to_col_idx.get(rank)
#         if col_idx is not None:
#             lineage[i, col_idx] = taxon_ids[i]

#         # Enqueue children
#         queue.extend(children_map.get(i, []))

#     # Convert lineage numpy table -> dataframe
#     lineage_df = pd.DataFrame(lineage, columns=RANK_COLS)

#     # Assign columns back into df (overwrites existing columns)
#     df[RANK_COLS] = lineage_df.values

#     return df
