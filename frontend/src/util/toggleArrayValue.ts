// Helper for adding/removing values from an array using checkboxes
// Ignores undefined and null values

export function toggleArrayValue<T>(arr: T[], value: T, checked: boolean): T[] {
    if (!value) {
        return arr;
    }
    return checked
        ? [...new Set([...arr, value])] // If checked, add value to array
        : arr.filter((v) => v !== value); // If unchecked, remove value
}
