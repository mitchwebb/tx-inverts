import { getContext, setContext } from 'svelte';
import type { NSRank } from '../types/api';
import type { Provider } from '../constants/mapLegendKeys';
import type { TaxonomicRank } from '../types/taxa';
import { makeIDCollection } from '../util/collection.svelte';

export const filtersStateKey = 'filters';

export type GeoFilter = {
    id: string; // uuid
    name: string;
    regionType: 'park' | 'county' | 'ecoregion';
};

export type FiltersState = {
    taxonRank: TaxonomicRank | null;
    includeINat: boolean;
    dataProviders: Provider[];
    nSRanks: NSRank[];
    dateStart: Date | null;
    dateEnd: Date | null;
    region: ReturnType<typeof makeIDCollection<GeoFilter, string>>; // UUIDs for all selected regions
};

export const initialFiltersState: FiltersState = {
    taxonRank: null,
    includeINat: true,
    dataProviders: [],
    nSRanks: [],
    dateStart: null,
    dateEnd: null,
    region: makeIDCollection<GeoFilter, string>((r) => r.id), // Dummy collection
};

export function setFiltersContext(taxonState: FiltersState) {
    setContext(filtersStateKey, taxonState);
}

export function getFiltersContext(): FiltersState {
    return getContext(filtersStateKey) as FiltersState;
}
