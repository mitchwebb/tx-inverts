import { getContext, setContext } from 'svelte';
import type { NSValues, TaxonInfo } from '../types/api';
import { makeIDCollection } from '../util/collection.svelte';

export const activeTaxaStateKey = 'taxa';

export type ActiveTaxon = {
    color: string;
    taxonLoading: boolean;
    taxonError: boolean;
    dateCountsLoading: boolean;
    dateRangeLoading: boolean;
    datasetCountsLoading: boolean;
    nSValuesLoading: boolean;
    lastLoadedID: number | null;
    taxonID: number;
    info: TaxonInfo;
    nSValues: NSValues;
    datasetCounts: Record<string, number> | null;
    dateMin: Date | null;
    dateMax: Date | null;
    dateCounts: Record<string, number>[] | null;
};

// Default state for nSValues
export const EMPTY_NS_VALUES: NSValues = {
    numberOfOccurrences: null,
    rangeExtentKm2: null,
    areaOfOccupancy1Km2Bins: null,
    areaOfOccupancy4Km2Bins: null,
    observationCount: null,
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
    subgenus: null,
    species: null,
    subspecies: null,
    usInvasive: null,
    taxonomicStatus: null,
    commonNames: null,
    nSRankDB: null,
    nSRankDBNoINat: null,
};

export const initialTaxonState: ActiveTaxon = {
    taxonID: 0, // Placeholder
    color: 'orange',
    taxonLoading: false,
    taxonError: true,
    dateCountsLoading: false,
    dateRangeLoading: false,
    datasetCountsLoading: false,
    nSValuesLoading: false,
    lastLoadedID: null,
    info: EMPTY_TAXON_INFO, // Values retrieved from get_taxon_info call
    nSValues: {
        numberOfOccurrences: null,
        areaOfOccupancy4Km2Bins: null,
        areaOfOccupancy1Km2Bins: null,
        rangeExtentKm2: null,
        observationCount: null,
    }, // Values retrieved get_ns_metrics call
    datasetCounts: null,
    dateMin: null, // Minimum obs date in db
    dateMax: null, // Max obs date in db
    dateCounts: null,
};

export type ActiveTaxaState = {
    taxa: ReturnType<typeof makeIDCollection<ActiveTaxon, number>>;
    getNextColor: () => string;
};

export const initialActiveTaxaState: ActiveTaxaState = {
    taxa: makeIDCollection<ActiveTaxon, number>((t) => t.taxonID), // Dummy collection
    getNextColor: () => '',
};

export function setActiveTaxaContext(activeTaxaState: ActiveTaxaState) {
    setContext(activeTaxaStateKey, activeTaxaState);
}

export function getActiveTaxaContext(): ActiveTaxaState {
    return getContext(activeTaxaStateKey) as ActiveTaxaState;
}
