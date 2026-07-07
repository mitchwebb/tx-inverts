import { expect, test } from 'vitest';
import { deduplicateStringArray } from './deduplicateArray';

test('Array removes full duplicates', () => {
    let array = ['foo', 'bar', 'foo', 'baz'];
    array = deduplicateStringArray(array);
    expect(array).toHaveLength(3);
    expect(array).toEqual(['foo', 'bar', 'baz']);
});

test('Duplicate removal is case insensitive', () => {
    let array = ['foo', 'bar', 'FOo', 'baz', 'BAZ'];
    array = deduplicateStringArray(array);
    expect(array).toHaveLength(3);
    expect(array).toEqual(['foo', 'bar', 'baz']);
});

test('Duplicate removal ignores spaces', () => {
    let array = ['foo', 'bar', 'FOo', 'fo o', 'ba z', 'B AZ'];
    array = deduplicateStringArray(array);
    expect(array).toHaveLength(3);
    expect(array).toEqual(['foo', 'bar', 'ba z']);
});

test('Duplicate removal ignores special characters', () => {
    let array = ['foo', 'bar', 'FO%o', 'fo o', 'b az', 'B *AZ'];
    array = deduplicateStringArray(array);
    expect(array).toHaveLength(3);
    expect(array).toEqual(['foo', 'bar', 'b az']);
});
