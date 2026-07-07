import { expect, expectTypeOf, test } from 'vitest';
import { normalizeToArray } from './normalizeToArray';

test('Array passes through', () => {
    const array = ['Xylocopa', 'Osmia', 'Melissodes'];
    const normalizedArray = normalizeToArray([
        'Xylocopa',
        'Osmia',
        'Melissodes',
    ]);
    expect(normalizedArray).toEqual(array);
});

test('Item normalizes to array', () => {
    const normalizedArray = normalizeToArray('Halictus');
    expect(normalizedArray).toEqual(['Halictus']);
    expectTypeOf(normalizedArray).toBeArray;
});

test('Null normalizes to empty array', () => {
    const normalizedArray = normalizeToArray(null);
    expect(normalizedArray).toEqual([]);
    expectTypeOf(normalizedArray).toBeArray;
});
