import { expect, test } from 'vitest';
import { toggleArrayValue } from './toggleArrayValue';

const testArray = ['bug', 'bat', 'buzz'];

test('Removes unchecked item', () => {
    const array = toggleArrayValue(testArray, 'bug', false);
    expect(array).not.toContain('bug');
});

test('Adds checked item', () => {
    const array = toggleArrayValue(testArray, 'bee', true);
    expect(array).toContain('bee');
});

test('Removing missing item does nothing', () => {
    const array = toggleArrayValue(testArray, 'bee', false);
    expect(array).toEqual(testArray);
});

test('Adding present item does nothing', () => {
    const array = toggleArrayValue(testArray, 'bat', true);
    expect(array).toEqual(testArray);
});

test('Ignores undefined and "" items', () => {
    let array = toggleArrayValue(testArray, undefined, true);
    array = toggleArrayValue(array, '', true);
    expect(array).toEqual(testArray);
});
