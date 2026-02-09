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
