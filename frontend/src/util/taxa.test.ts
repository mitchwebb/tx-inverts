import { expect, test } from 'vitest';
import { isItalicizedRank } from './taxa';

test('isItalicizedRank returns true', () => {
    expect(isItalicizedRank('species')).toBe(true);
    expect(isItalicizedRank('subspecies')).toBe(true);
    expect(isItalicizedRank('genus')).toBe(true);
});

test('isItalicizedRank returns false for higher taxa', () => {
    expect(isItalicizedRank('kingdom')).toBe(false);
    expect(isItalicizedRank('class')).toBe(false);
    expect(isItalicizedRank('family')).toBe(false);
});

test('isItalicizedRank ignores case', () => {
    expect(isItalicizedRank('spEcies')).toBe(true);
    expect(isItalicizedRank('SubspeCies')).toBe(true);
    expect(isItalicizedRank('KingDom')).toBe(false);
});
