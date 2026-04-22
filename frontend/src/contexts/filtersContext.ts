import { getContext, setContext } from 'svelte';
import type { NSRank, RegionInfo } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';
import { makeIDCollection } from '../util/collection.svelte';

export const filtersStateKey = 'filters';

export type FiltersState = {
    taxonRank: TaxonomicRank | null;
    includeINat: boolean;
    dataProviders: string[];
    nSRanks: NSRank[];
    dateStart: Date | null;
    dateEnd: Date | null;
    region: ReturnType<typeof makeIDCollection<RegionInfo, string>>; // UUIDs for all selected regions
    filterTaxonIDs: number[];
};

export const initialFiltersState: FiltersState = {
    taxonRank: null,
    includeINat: true,
    dataProviders: [],
    nSRanks: [],
    dateStart: null,
    dateEnd: null,
    region: makeIDCollection<RegionInfo, string>((r) => r.id), // Dummy collection
    filterTaxonIDs: [],
};

export function setFiltersContext(taxonState: FiltersState) {
    setContext(filtersStateKey, taxonState);
}

export function getFiltersContext(): FiltersState {
    return getContext(filtersStateKey) as FiltersState;
}
