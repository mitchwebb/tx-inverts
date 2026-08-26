# Taxa-related constants
from typing import Literal

RANK_ORDER = [
    'kingdom',
    'phylum',
    'subphylum',
    'class',
    'subclass',
    'infraclass',
    'subterclass',
    'superorder',
    'order',
    'superfamily',
    'family',
    'subfamily',
    'tribe',
    'subtribe',
    'genus',
    'subgenus',
    'species',
    'subspecies'
]

type TaxonomicRank = Literal[
    'kingdom',
    'phylum',
    'subphylum',
    'class',
    'subclass',
    'infraclass',
    'subterclass',
    'superorder',
    'order',
    'superfamily',
    'family',
    'subfamily',
    'tribe',
    'subtribe',
    'genus',
    'subgenus',
    'species',
    'subspecies'
]

RANK_COLS = [f'{r}_key' for r in RANK_ORDER]
