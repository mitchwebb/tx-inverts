import { beforeEach, describe, expect, test } from 'vitest';
import {
    booleanURLCodec,
    collectionObjectURLCodec,
    dateURLCodec,
    numberArrayURLCodec,
    stringArrayURLCodec,
    stringURLCodec,
} from './router';
import { makeIDCollection } from './collection.svelte';

describe('Boolean url param codec', () => {
    test('toURL returns null when value matches default', () => {
        const defaultVal = true;
        const codec = booleanURLCodec(defaultVal);
        expect(codec.toURL(defaultVal)).toBeNull();
    });

    test('toURL returns string array when value is not default', () => {
        const defaultVal = false;
        const codec = booleanURLCodec(defaultVal);
        const result = codec.toURL(!defaultVal);
        expect(result).toBeInstanceOf(Array);
        expect(result).toEqual([(!defaultVal).toString()]);
    });

    test('fromURL returns default when no values', () => {
        const defaultVal = true;
        const codec = booleanURLCodec(defaultVal);
        expect(codec.fromURL([])).toBe(defaultVal);
    });

    test('fromURL returns first value from list', () => {
        const defaultVal = false;
        const codec = booleanURLCodec(defaultVal);
        const result = codec.fromURL(['true', 'false']);
        expect(result).toBe(true);
    });
});

describe('String array url param codec', () => {
    test('toURL returns null given empty array', () => {
        const codec = stringArrayURLCodec();
        expect(codec.toURL([])).toBeNull();
    });
    test('toURL returns string array given string array', () => {
        const codec = stringArrayURLCodec();
        const result = codec.toURL(['flea', 'tick', 'louse']);
        expect(result).toEqual(['flea', 'tick', 'louse']);
        expect(result![0]).toBeTypeOf('string');
    });
    test('fromURL returns string array given string array', () => {
        const codec = stringArrayURLCodec();
        expect(codec.fromURL(['flea', 'tick', 'louse'])).toEqual([
            'flea',
            'tick',
            'louse',
        ]);
    });
});

describe('Single string url param codec', () => {
    test('toURL default value returns null', () => {
        const defaultVal = 'albopictus';
        const codec = stringURLCodec(defaultVal);
        expect(codec.toURL(defaultVal)).toBe(null);
    });
    test('toURL null returns null', () => {
        const defaultVal = 'albopictus';
        const codec = stringURLCodec(defaultVal);
        expect(codec.toURL(null)).toBe(null);
    });
    test('toURL non-default string returns string array', () => {
        const defaultVal = 'albopictus';
        const codec = stringURLCodec(defaultVal);
        const result = codec.toURL('aegypti');
        expect(result).toEqual(['aegypti']);
        expect(result).toBeInstanceOf(Array);
    });
    test('fromURL no values returns default', () => {
        const defaultVal = 'albopictus';
        const codec = stringURLCodec(defaultVal);
        const result = codec.fromURL([]);
        expect(result).toEqual(defaultVal);
    });
    test('fromURL returns first value as string', () => {
        const defaultVal = 'albopictus';
        const codec = stringURLCodec(defaultVal);
        const result = codec.fromURL(['aegypti', 'albopictus', 'buzz']);
        expect(result).toEqual('aegypti');
        expect(result).toBeTypeOf('string');
    });
});

describe('Date url param codec', () => {
    test('toURL default value returns null', () => {
        const defaultVal = new Date(1995, 7, 11);
        const codec = dateURLCodec(defaultVal);
        expect(codec.toURL(defaultVal)).toBe(null);
    });
    test('toURL null returns null', () => {
        const defaultVal = new Date(1995, 7, 11);
        const codec = dateURLCodec(defaultVal);
        expect(codec.toURL(null)).toBe(null);
    });
    test('toURL non-default date returns localeString', () => {
        const codec = dateURLCodec(new Date(1995, 7, 11));
        const nonDefaultDate = new Date(1995, 1, 27);
        const result = codec.toURL(nonDefaultDate);
        expect(result).toEqual([nonDefaultDate.toLocaleDateString()]);
        expect(result).toBeInstanceOf(Array);
    });
    test('fromURL no values returns default', () => {
        const defaultVal = new Date(1995, 7, 11);
        const codec = dateURLCodec(defaultVal);
        const result = codec.fromURL([]);
        expect(result).toBe(defaultVal);
    });
    test('fromURL non-default value returns first Date', () => {
        const defaultVal = new Date(1995, 7, 11);
        const secondaryVal = new Date(1996, 8, 12);
        const codec = dateURLCodec(defaultVal);
        const result = codec.fromURL([
            secondaryVal.toDateString(),
            defaultVal.toDateString(),
        ]);
        expect(result).toEqual(secondaryVal);
        expect(result).toBeInstanceOf(Date);
    });
});

describe('collectionObject url param codec', () => {
    type Item = { id: string | number; name: string };
    const getID = (item: Item) => item.id;
    let collection: ReturnType<typeof makeIDCollection<Item, number | string>>;
    beforeEach(() => {
        collection = makeIDCollection(getID);
        collection.add({ id: 1, name: 'foo' });
        collection.add({ id: 3, name: 'bar' });
        collection.add({ id: 2, name: 'baz' });
    });
    test('toURL collection object with ids returns id strings', () => {
        const codec = collectionObjectURLCodec();
        expect(codec.toURL(collection)).toEqual(
            expect.arrayContaining(['1', '2', '3'])
        );
    });
    test('toURL simple record with int id keys returns id strings', () => {
        const codec = collectionObjectURLCodec();
        expect(codec.toURL({ 1: 'ant', 3: 'wasp', 2: 'bee' })).toEqual(
            expect.arrayContaining(['1', '2', '3'])
        );
    });
    test('toURL simple record with string id keys returns id strings', () => {
        const codec = collectionObjectURLCodec();
        expect(
            codec.toURL({
                Scolopendra: 'heros',
                Zopherus: 'nodulosus',
                Atta: 'texana',
            })
        ).toEqual(expect.arrayContaining(['Scolopendra', 'Zopherus', 'Atta']));
    });
    test('toURL empty collection object returns null', () => {
        const emptyCollection = makeIDCollection(getID);
        const codec = collectionObjectURLCodec();
        expect(codec.toURL(emptyCollection)).toBeNull;
    });
    test('fromURL returns nothing (undefined)', () => {
        const codec = collectionObjectURLCodec();
        expect(codec.fromURL(['1', '3', '2'])).toBeUndefined;
    });
});
