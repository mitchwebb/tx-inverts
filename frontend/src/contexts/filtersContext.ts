import { getContext, setContext } from 'svelte';
import type { NSRank } from '../types/api';
import type { Provider } from '../constants/mapLegendKeys';
import type { TaxonomicRank } from '../types/taxa';

export const filtersStateKey = 'filters';

export type FiltersState = {
    taxonRank: TaxonomicRank | null;
    includeINat: boolean;
    dataProviders: Provider[] | null;
    nSRanks: NSRank[] | null;
    dateStart: string | null;
    dateEnd: string | null;
};

export const initialFiltersState: FiltersState = {
    taxonRank: null,
    includeINat: true,
    dataProviders: null,
    nSRanks: null,
    dateStart: null,
    dateEnd: null,
};

export function setFiltersContext(taxonState: FiltersState) {
    setContext(filtersStateKey, taxonState);
}

export function getFiltersContext(): FiltersState {
    return getContext(filtersStateKey) as FiltersState;
}
