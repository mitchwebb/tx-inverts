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
    '#e58606',
    '#5d69b1',
    '#52bca3',
    '#99c945',
    '#cc61b0',
    '#24796c',
    '#daa51b',
    '#2f8ac4',
    '#764e9f',
    '#ed645a',
    '#cc3a8e',
    '#a5aa99',
];
