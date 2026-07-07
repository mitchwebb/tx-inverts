/**
 * Creates a reactive, ordered collection of items with unique IDs.
 *
 * @template T - The item type
 * @template ID - The ID type (string or number)
 * @param getID - Function that extracts a unique ID from an item
 * @param onAdd - Optional async callback fired after an item is added, receives the new item's ID
 * @returns Collection object with the following properties and methods:
 * - `items` — reactive array of all items in insertion order
 * - `ids` — array of all item IDs in insertion order
 * - `get(id)` — returns the item with the given ID, or undefined
 * - `add(item)` — appends item and fires onAdd if provided
 * - `remove(id)` — removes item with the given ID
 * - `clear()` — removes all items
 */
export function makeIDCollection<
    T,
    ID extends number | string = number | string,
>(getID: (item: T) => ID, onAdd?: (id: ID) => Promise<void>) {
    let items = $state<T[]>([]);
    return {
        get items() {
            return items;
        },
        get ids() {
            return items.map(getID);
        },
        get(id: ID) {
            return items.find((i) => getID(i) === id);
        },
        async add(item: T) {
            items = [...items, item];
            if (onAdd) {
                await onAdd(getID(item));
            }
        },
        remove(id: ID) {
            items = items.filter((i) => getID(i) !== id);
        },
        clear() {
            items = [];
        },
    };
}
