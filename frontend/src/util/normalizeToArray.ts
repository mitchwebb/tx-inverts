/**
 * Helper to normalize str/int to str[]/int[]
 *
 * @param val - Value or array you wish to cast to array
 * @returns Array
 */
export function normalizeToArray(
    val: number[] | string[] | number | string | null
): (number | string)[] {
    if (val == null) return [];
    return Array.isArray(val) ? val : [val];
}
