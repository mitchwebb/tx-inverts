import type { TaxonomicRank } from '../types/taxa';

export type ItalicizedRank = Extract<
    TaxonomicRank,
    'genus' | 'species' | 'subspecies'
>;

export const italicizedRanks: ItalicizedRank[] = [
    'genus',
    'species',
    'subspecies',
];

export const TAXON_COLORS = [
    '#e69f00',
    '#56b4e9',
    '#009e73',
    '#bdce22',
    '#0072b2',
    '#d53c00',
    '#cc79a7',
];
