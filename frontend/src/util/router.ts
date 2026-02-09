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
    toURL(value) {
        return value === null || value.length === 0 ? null : value.map(String);
    },
    fromURL(values) {
        return values;
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
