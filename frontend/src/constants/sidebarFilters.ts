import {
    initialFiltersState,
    type FiltersStateType,
} from '../contexts/filtersContext';

// FilterPath notes which page a filter belongs to (they can belong ot multiple)
export type FilterPath = ('taxa' | 'rankings' | 'map')[];

// The scope of a given filter--whether it targets taxa or observation data
// This is used to trigger certain warnings
export type FilterDomain = 'observations' | 'taxa';

// Grab defaults from initial state object
const FILTER_DEFAULTS = initialFiltersState;

// Collection of sidebar filters and their defaults, as well as whether or not they
// should be counted with tallying applied filters
export const SIDEBAR_FILTER_META = {
    nSRanks: {
        path: ['rankings'],
        default: FILTER_DEFAULTS.nSRanks,
        domain: 'taxa',
        count: true,
    },
    dataProviders: {
        path: ['map'],
        default: FILTER_DEFAULTS.dataProviders,
        domain: 'observations',
        count: true,
    },
    dateEnd: {
        path: ['map'],
        default: FILTER_DEFAULTS.dateEnd,
        domain: 'observations',
        count: true,
    },
    dateStart: {
        path: ['map'],
        default: FILTER_DEFAULTS.dateStart,
        domain: 'observations',
        count: true,
    },
    includeINat: {
        path: ['map', 'rankings', 'taxa'],
        default: FILTER_DEFAULTS.includeINat,
        domain: 'observations',
        count: true,
    },
    taxonRank: {
        path: ['rankings'],
        default: FILTER_DEFAULTS.taxonRank,
        domain: 'taxa',
        count: true,
    },
    filteredTaxonID: {
        path: ['rankings'],
        default: FILTER_DEFAULTS.filteredTaxonID,
        domain: 'taxa',
        count: true,
    },
    filteredCanonicalName: {
        path: ['rankings'],
        default: FILTER_DEFAULTS.filteredCanonicalName,
        domain: 'taxa',
        count: false,
    },
} satisfies {
    [K in keyof FiltersStateType]: {
        path: FilterPath;
        default: FiltersStateType[K];
        domain: FilterDomain;
        count: boolean;
    };
};

export const FILTER_KEYS = Object.keys(
    SIDEBAR_FILTER_META
) as (keyof FiltersStateType)[];
