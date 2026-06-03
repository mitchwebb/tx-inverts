# Taxa-related constants
from typing import Literal

RANK_ORDER = [
    'kingdom',
    'phylum',
    'class',
    'order',
    'family',
    'genus',
    'species',
    'subspecies'
]

type TaxonomicRank = Literal[
    'kingdom',
    'phylum',
    'class',
    'order',
    'family',
    'genus',
    'species',
    'subspecies'
]

RANK_COLS = [f"{r}_id" for r in RANK_ORDER]
