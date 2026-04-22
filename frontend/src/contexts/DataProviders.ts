import { writable } from 'svelte/store';

export type DatasetKey = string;

export type DataProviderInfo = {
    institutionName: string;
    institutionCode: string | null;
};

export const dataProviders = writable<Record<
    DatasetKey,
    DataProviderInfo
> | null>(null);
