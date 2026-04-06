// A little generator for managing contexts with type Record<string, string>[]
// where Records have a unique ID. This is a way of retaining a sorted array of objects,
// while making them easier to work with.
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
