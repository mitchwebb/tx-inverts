import { writable } from 'svelte/store';

export type InstitutionCode = string;

export type DataProviderInfo = {
    institutionName: string;
    datasetKey: string;
};

export const dataProviders = writable<Record<
    InstitutionCode,
    DataProviderInfo
> | null>(null);
