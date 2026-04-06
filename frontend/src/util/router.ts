import type { ActiveTaxon } from '../contexts/activeTaxaContext';
import type { ParamCodec } from '../types/router';

/**
 * URL/CONTEXT CODECS
 * These should be used to transfer params between URL and Contexts
 */
export const numberCodec = (
    defaultValue: number | null = null
): ParamCodec<number | null> => ({
    toURL(value) {
        if (value == null || value === defaultValue) return null;
        return [String(value)];
    },
    fromURL(values) {
        if (values.length === 0) return defaultValue;
        const n = Number(values[0]);
        return Number.isNaN(n) ? defaultValue : n;
    },
});

export const booleanCodec = (defaultValue: boolean): ParamCodec<boolean> => ({
    toURL(value) {
        return value === defaultValue ? null : [String(value)];
    },
    fromURL(values) {
        if (values.length === 0) return defaultValue;
        return values[0] === 'true';
    },
});

export const stringArrayCodec = (): ParamCodec<string[]> => ({
    toURL(values) {
        return values === null || values.length === 0
            ? null
            : [...new Set(values)].map(String);
    },
    fromURL(values) {
        return [...new Set(values)];
    },
});

export const numberArrayCodec = (): ParamCodec<number[]> => ({
    toURL(values) {
        return values === null || values.length === 0
            ? null
            : [...new Set(values)].map(String);
    },
    fromURL(values) {
        return [...new Set(values.map(Number))];
    },
});

export const stringCodec = (
    defaultValue: string | null = null
): ParamCodec<string | null> => ({
    toURL(value) {
        if (value === null || value === defaultValue) return null; // omit defaults
        return [value];
    },
    fromURL(values) {
        if (!values || values.length === 0) return defaultValue;
        return values[0]; // just take the first
    },
});

export const dateCodec = (
    defaultValue: Date | null = null
): ParamCodec<Date | null> => ({
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
// These require special fromURL handling, and therefor return nothing in this codec
export function iDObjectCodec(): ParamCodec<any> {
    return {
        toURL: (value) => {
            if (!value) return null;
            const keys = value.ids ?? Object.keys(value);
            return keys.length ? keys.map(String) : null;
        },
        fromURL: (_values) => undefined,
    };
}
