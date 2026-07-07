import { beforeEach, describe, expect, test } from 'vitest';
import { makeIDCollection } from './collection.svelte';

type Item = { id: number; name: string };
const getID = (item: Item) => item.id;

// Tests that use our beforeEach basic collection
describe('BasicIDCollectionTests', () => {
    let collection: ReturnType<typeof makeIDCollection<Item, number>>;
    beforeEach(() => {
        collection = makeIDCollection(getID);
        collection.add({ id: 1, name: 'foo' });
        collection.add({ id: 3, name: 'bar' });
        collection.add({ id: 2, name: 'baz' });
    });

    test('Collection adds and retrieves items', () => {
        expect(collection.items).toHaveLength(3);
        expect(collection.get(2)?.name).toBe('baz');
    });

    test('Collection.ids lists ids in order', () => {
        expect(collection.ids).toEqual([1, 3, 2]);
    });

    test('Collection.remove removes items', () => {
        collection.remove(3);
        expect(collection.items).toHaveLength(2);
        expect(collection.ids).toEqual([1, 2]);
    });

    test('Collection.clear clears items', () => {
        collection.clear();
        expect(collection.items).toHaveLength(0);
    });

    test('IDCollection.get returns undefined on missing', () => {
        const missingItem = collection.get(1000);
        expect(missingItem).toEqual(undefined);
    });
});

// Test that collection.add uses onAdd callback when provided
test('Collection.add uses callback', () => {
    const called: number[] = [];
    const onAdd = async (id: number) => {
        called.push(id);
    };
    const collectionWithCallback = makeIDCollection(getID, onAdd);
    collectionWithCallback.add({ id: 25, name: 'foo' });

    expect(called).toEqual([25]);
});
