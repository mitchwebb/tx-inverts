import { writable } from 'svelte/store';

export type DatasetKey = string;

export type DatasetInfo = {
    datasetTitle: string;
};

export const datasets = writable<Record<DatasetKey, DatasetInfo> | null>(null);
