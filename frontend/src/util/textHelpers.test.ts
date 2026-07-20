import { describe, expect, test } from 'vitest';
import { capitalizeWords, normalizeString } from './textHelpers';

describe('test normalizeString', () => {
    test('removes spaces, caps, and special characters', () => {
        const normalized = normalizeString('Sp aces, sp3ci@l, and CApS');
        expect(normalized).toBe('spacesspcilandcaps');
    });
});

describe('test capitalizeWords', () => {
    test('capitalizes single string', () => {
        expect(capitalizeWords('bug')).toBe('Bug');
    });
    test('capitalizes single string with multiple words', () => {
        expect(capitalizeWords('big bug')).toBe('Big Bug');
    });
    test('ignore word after dash', () => {
        expect(capitalizeWords('big-bug')).toBe('Big-bug');
    });
    test('capitalize array', () => {
        expect(capitalizeWords(['bug', 'insect', 'critter'])).toEqual(
            expect.arrayContaining(['Bug', 'Insect', 'Critter'])
        );
    });
});
