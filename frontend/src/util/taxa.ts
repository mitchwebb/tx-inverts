import { italicizedRanks, type ItalicizedRank } from '../constants/taxa';
import type { TaxonomicRank } from '../types/taxa';

/**
 * Helper to check if a provided value is a member of italicizedRanks
 *
 * @param value
 * @returns
 */
export function isItalicizedRank(
    value: TaxonomicRank | null
): value is ItalicizedRank {
    return (
        typeof value === 'string' &&
        italicizedRanks.includes(value.toLowerCase() as ItalicizedRank)
    );
}

/**
 * Helper to check if taxonRank is in 'species', 'subspecies', 'variety', or 'form'
 *
 * @param taxonRank
 * @returns boolean
 */
export function rankIsSpeciesOrBelow(taxonRank: TaxonomicRank): boolean {
    return ['species', 'subspecies', 'variety', 'form'].includes(taxonRank);
}
