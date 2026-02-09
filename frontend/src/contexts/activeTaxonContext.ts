import { getContext, setContext } from 'svelte';
import type { NSValues, TaxonInfo } from '../types/api';
import type { Provider } from '../constants/mapLegendKeys';

export const activeTaxonStateKey = 'taxa';

export type ActiveTaxonStateType = {
    taxonLoading: boolean;
    taxonError: boolean;
    observationMetricsLoading: boolean;
    nSValuesLoading: boolean;
    lastLoadedID: number | null;
    taxonID: number | null;
    taxonInfo: TaxonInfo;
    nSValues: NSValues;
    providerCounts: Record<Provider, number> | null;
    dateMin: string | null;
    dateMax: string | null;
};

// Default state for taxon_info (used for resetting)
export const EMPTY_TAXON_INFO: TaxonInfo = {
    acceptedTaxonID: null,
    canonicalName: null,
    taxonRank: null,
    scientificNameAuthorship: null,
    kingdom: null,
    phylum: null,
    class: null,
    order: null,
    superfamily: null,
    family: null,
    subfamily: null,
    genus: null,
    species: null,
    subspecies: null,
    usInvasive: null,
    taxonomicStatus: null,
    commonNames: null,
    nSRankDB: null,
    nSRankDBNoINat: null,
    nSRankLocal: null,
};

export const initialTaxonState: ActiveTaxonStateType = {
    taxonLoading: false,
    taxonError: true,
    observationMetricsLoading: false,
    nSValuesLoading: false,
    lastLoadedID: null,
    taxonID: null,
    taxonInfo: EMPTY_TAXON_INFO, // Values retrieved from get_taxon_info call
    nSValues: {
        numberOfOccurrences: null,
        areaOfOccupancy4Km2Bins: null,
        rangeExtentKm2: null,
        observationCount: null,
    }, // Values retrieved get_ns_values call
    providerCounts: null,
    dateMin: null, // Minimum obs date in db
    dateMax: null, // Max obs date in db
};

export function setActiveTaxonContext(activeTaxonState: ActiveTaxonStateType) {
    setContext(activeTaxonStateKey, activeTaxonState);
}

export function getActiveTaxonContext(): ActiveTaxonStateType {
    return getContext(activeTaxonStateKey) as ActiveTaxonStateType;
}
