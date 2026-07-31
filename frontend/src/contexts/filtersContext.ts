import { getContext, setContext } from 'svelte';
import type { NSRank, RegionInfo } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';
import { makeIDCollection } from '../util/collection.svelte';

export const filtersStateKey = 'filters';

export type FiltersState = {
    taxonRank: TaxonomicRank | null;
    includeINat: boolean;
    datasets: string[];
    nSRanks: NSRank[];
    dateStart: Date | null;
    dateEnd: Date | null;
    regions: ReturnType<typeof makeIDCollection<RegionInfo, string>>; // UUIDs for all selected regions
    coordUncertainty: number | null;
};

export const initialFiltersState: FiltersState = {
    taxonRank: null,
    includeINat: true,
    datasets: [],
    nSRanks: [],
    dateStart: null,
    dateEnd: null,
    regions: makeIDCollection<RegionInfo, string>((r) => r.id), // Dummy collection
    coordUncertainty: null,
};

export function setFiltersContext(taxonState: FiltersState) {
    setContext(filtersStateKey, taxonState);
}

export function getFiltersContext(): FiltersState {
    return getContext(filtersStateKey) as FiltersState;
}
