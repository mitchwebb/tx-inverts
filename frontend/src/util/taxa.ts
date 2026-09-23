import { italicizedRanks, type ItalicizedRank } from '../constants/taxa';
import type { TaxonomicRank } from '../types/taxa';

// Helper function to check if a provided value is a member of italicizedRanks
export function isItalicizedRank(
    value: TaxonomicRank | null
): value is ItalicizedRank {
    return (
        typeof value === 'string' &&
        italicizedRanks.includes(value.toLowerCase() as ItalicizedRank)
    );
}
