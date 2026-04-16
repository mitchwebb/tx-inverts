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
    '#E58606',
    '#5D69B1',
    '#52BCA3',
    '#99C945',
    '#CC61B0',
    '#24796C',
    '#DAA51B',
    '#2F8AC4',
    '#764E9F',
    '#ED645A',
    '#CC3A8E',
    '#A5AA99',
];
