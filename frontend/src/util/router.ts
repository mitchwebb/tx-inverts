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

export function taxaCodec(): ParamCodec<Record<number, ActiveTaxon>> {
    return {
        toURL: (taxa) => (taxa ? Object.keys(taxa).map(String) : null),
        fromURL: (_values) => undefined, // No function, onMount handles this
    };
}
