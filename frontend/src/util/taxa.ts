import { italicizedRanks, type ItalicizedRank } from '../constants/taxa';

// Helper function to check if a provided value is a member of italicizedRanks
export function isItalicizedRank(value: unknown): value is ItalicizedRank {
    return (
        typeof value === 'string' &&
        (italicizedRanks as readonly string[]).includes(value)
    );
}
