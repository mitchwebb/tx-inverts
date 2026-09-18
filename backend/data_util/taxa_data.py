from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.helpers import normalize_to_list
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
import pandas as pd
from typing import List
from psycopg import AsyncConnection, sql
import re


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


def derive_canonical_name(row: pd.Series):
    """
    Derive canonicalName column information.

    This is done by combining column data or by stripping
    the scientificName column, depending on taxonRank. 

    Columns required:
        'scientificName',
        'genericName',
        'infragenericEpithet',
        'specificEpithet',
        'infraspecificEpithet',
        'taxonRank',
        'scientificNameAuthorship'
    """

    taxon_rank = row['taxonRank']

    match taxon_rank:
        case 'species':
            parts = [row['genericName'], row['specificEpithet']]

        # Subgenus with (Genus (Subgenus)) format
        case 'subgenus':
            if pd.isna(row['infragenericEpithet']):
                return pd.NA
            parts = [
                row['genericName'],
                f'({row['infragenericEpithet']})'
            ]

        case 'subspecies':
            parts = [
                row['genericName'],
                row['specificEpithet'],
                row['infraspecificEpithet']
            ]

        # Form with (Genus species f. form) format
        case 'form':
            parts = [
                row['genericName'],
                row['specificEpithet'],
                'f.',
                row['infraspecificEpithet']
            ]
        # Last ditch effort to strip authorship (after all polynomial cases have been addressed)
        case _:
            sci_name = row['scientificName']
            if pd.isna(sci_name):
                return pd.NA

            authorship = row['scientificNameAuthorship']

            # If authorship found within scientific name (as a whole, not a
            # substring of another word), strip it and use that output
            stripped_sci_name = None
            if pd.notna(authorship):
                pattern = rf'\s*\b{re.escape(authorship)}\b\s*'
                match_found = re.search(pattern, sci_name)
                if match_found:
                    stripped_sci_name = re.sub(pattern, ' ', sci_name).strip()

            # If we got a stripped name, use it
            if stripped_sci_name is not None:
                parts = [stripped_sci_name]
            # Else check if scientific name is quoted (use quoted section)
            elif sci_name.startswith('"'):
                end = sci_name.find('"', 1)
                parts = [sci_name[:end + 1]] if end != -1 else [sci_name]
            # Else, imperfect selection of first part of scientific name
            else:
                # This helps for cases where scientific name contains authorship, but authorship column is None
                parts = [row['scientificName'].split(' ', 1)[0]]

    # If the names we've made contain NaN parts, it has failed and we need to return NaN
    if any(pd.isna(p) for p in parts):
        return pd.NA

    return ' '.join(parts)


def create_canonical_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Using a pandas DataFrame, add a 'canonicalName' column
    populated with scientific names WITHOUT authorship.

    Columns required:
        'scientificName',
        'genericName',
        'infragenericEpithet',
        'specificEpithet',
        'infraspecificEpithet',
        'taxonRank',
        'scientificNameAuthorship'
    """
    required_cols = {
        'scientificName',
        'genericName',
        'infragenericEpithet',
        'specificEpithet',
        'infraspecificEpithet',
        'taxonRank',
        'scientificNameAuthorship'
    }

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f'DataFrame is missing required columns: {missing}')

    df['canonicalName'] = df.apply(
        lambda row: derive_canonical_name(row), axis=1)

    return df
