import type { URLParamCodec } from '../types/router';
import type { makeIDCollection } from './collection.svelte';

/**
 * URL/CONTEXT CODECS
 * These should be used to transfer params between URL and Contexts
 */

export const booleanURLCodec = (
    defaultValue: boolean
): URLParamCodec<boolean> => ({
    toURL(value) {
        return value === defaultValue ? null : [String(value)];
    },
    fromURL(values) {
        if (values.length === 0) return defaultValue;
        return values[0] === 'true';
    },
});

export const stringArrayURLCodec = (): URLParamCodec<string[]> => ({
    toURL(values) {
        return values === null || values.length === 0
            ? null
            : [...new Set(values)].map(String);
    },
    fromURL(values) {
        return [...new Set(values)];
    },
});

export const numberURLCodec = (): URLParamCodec<number> => ({
    toURL(value) {
        if (value === null) return null; // omit defaults
        return [value.toString()];
    },
    fromURL(values) {
        const parsed = Number(values[0]);
        return Number.isNaN(parsed) ? null : parsed;
    },
});

export const numberArrayURLCodec = (): URLParamCodec<number[]> => ({
    toURL(values) {
        return values === null || values.length === 0
            ? null
            : [...new Set(values)].map(String);
    },
    fromURL(values) {
        return [...new Set(values.map(Number))];
    },
});

export const stringURLCodec = (
    defaultValue: string | null = null
): URLParamCodec<string | null> => ({
    toURL(value) {
        if (value === null || value === defaultValue) return null; // omit defaults
        return [value];
    },
    fromURL(values) {
        if (!values || values.length === 0) return defaultValue;
        return values[0]; // just take the first
    },
});

export const dateURLCodec = (
    defaultValue: Date | null = null
): URLParamCodec<Date | null> => ({
    toURL(value) {
        if (value === null || value === defaultValue) return null; // omit defaults
        return [value.toLocaleDateString()];
    },
    fromURL(values) {
        if (!values || values.length === 0) return defaultValue;
        return new Date(values[0]); // just take the first
    },
});

// Codec to take a Record type, keyed by IDs, resulting in ID values for URL
// These require special fromURL handling, and therefor return nothing in their codec
// Though designed to work with objects made using makeIDCollection(), it also works
// with simple keyed objects, where the keys are IDs.
export function collectionObjectURLCodec(): URLParamCodec<
    | ReturnType<typeof makeIDCollection<any, string | number>>
    | Record<string | number, any>
> {
    return {
        toURL: (value) => {
            if (!value) return null;
            const keys = 'ids' in value ? value.ids : Object.keys(value);
            return keys.length ? keys.map(String) : null;
        },
        fromURL: (_values) => undefined,
    };
}
