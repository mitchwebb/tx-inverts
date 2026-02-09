/**
 * Normalizes a given string by lowercasing and removing non-letter characters.
 *
 * Useful for standardizing strings when comparing.
 *
 * @param text - Input string
 * @returns A lowercase string containing only letters (a-z) with no whitespace
 */
export function normalizeString(text: string): string {
    return text
        .toLowerCase()
        .replace(/[^a-z]/g, '') // remove all non-letter characters including spaces
        .trim();
}

/**
 * Simple helper to capitalize first letter of each word in a string
 *
 * Mostly for display purposes
 *
 * @param str - Input string or string array
 * @returns The input string or string array with each word capitalized
 */
export function capitalizeWords(words: string | string[]): string | string[] {
    function capitalize(str: string) {
        return str.replace(/\b\w/g, (char) => char.toUpperCase());
    }

    if (Array.isArray(words)) {
        return words.map(capitalize);
    }
    return capitalize(words);
}

/**
 * Simple helper to round and prepare number for display
 *
 * @param number - Input number
 * @param decimals - Number of decimal places for truncation
 * @returns Input number, rounded, with separators
 */
export function toLocaleRounded(number: number | null, decimals: number = 0) {
    // TODO: Needs to error
    if (number == null) {
        return;
    }
    const rounded = number.toFixed(decimals);
    const localeString = Number(rounded).toLocaleString();
    return localeString;
}
