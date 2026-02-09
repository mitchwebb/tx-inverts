/**
 * Simple helper to check for valid URL
 *
 * @param str - Proposed URL string
 * @returns bool
 */
export function isValidURL(str: string): boolean {
    try {
        new URL(str);
        return true;
    } catch {
        return false;
    }
}
