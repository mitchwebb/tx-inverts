import { normalizeString } from './textHelpers';

/**
 * Deduplicates string array, ignoring capitals, spaces, and special characters.
 *
 * Uses normalizeString for normalization
 *
 * @param array - Array of strings
 * @returns A new array with only unique strings based on normalized values. Uses the spacing/characters found in first version of each string.
 */
export function deduplicateStringArray(array: string[]): string[] {
    const seen = new Set<string>();
    return array.filter((item) => {
        const normalized = normalizeString(item);
        if (seen.has(normalized)) return false;
        seen.add(normalized);
        return true;
    });
}
