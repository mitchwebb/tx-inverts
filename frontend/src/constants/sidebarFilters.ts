import {
    initialFiltersState,
    type FiltersState,
} from '../contexts/filtersContext';
import type { RouterPath } from '../contexts/routerContext';

// The scope of a given filter--whether it targets taxa or observation data
// This is used to trigger certain warnings
export type FilterDomain = 'observations' | 'taxa';

// Grab defaults from initial state object
const FILTER_DEFAULTS = initialFiltersState;

type SidebarFilterMetaItem = {
    path: RouterPath[]; // Notes which page a filter belongs to (they can belong ot multiple)
    default: unknown;
    domain: FilterDomain[];
    count: boolean;
};

// Collection of sidebar filters and their defaults, as well as whether or not they
// should be counted with tallying applied filters
export const SIDEBAR_FILTER_META: Record<
    keyof FiltersState,
    SidebarFilterMetaItem
> = {
    nSRanks: {
        path: ['/rankings'],
        default: FILTER_DEFAULTS.nSRanks,
        domain: ['taxa'],
        count: true,
    },
    dataProviders: {
        path: ['/map'],
        default: FILTER_DEFAULTS.dataProviders,
        domain: ['observations'],
        count: true,
    },
    dateEnd: {
        path: ['/map', '/rankings'],
        default: FILTER_DEFAULTS.dateEnd,
        domain: ['observations', 'taxa'],
        count: true,
    },
    dateStart: {
        path: ['/map', '/rankings'],
        default: FILTER_DEFAULTS.dateStart,
        domain: ['observations', 'taxa'],
        count: true,
    },
    includeINat: {
        path: ['/map', '/rankings', '/taxa'],
        default: FILTER_DEFAULTS.includeINat,
        domain: ['observations'],
        count: true,
    },
    taxonRank: {
        path: ['/rankings'],
        default: FILTER_DEFAULTS.taxonRank,
        domain: ['taxa'],
        count: true,
    },
    counties: {
        path: ['/rankings'],
        default: FILTER_DEFAULTS.counties,
        domain: ['taxa'],
        count: false,
    },
    parks: {
        path: ['/rankings'],
        default: FILTER_DEFAULTS.parks,
        domain: ['taxa'],
        count: false,
    },
    region: {
        path: ['/rankings'],
        default: FILTER_DEFAULTS.region,
        domain: ['taxa'],
        count: false,
    },
} satisfies {
    [K in keyof FiltersState]: {
        path: RouterPath[];
        default: FiltersState[K];
        domain: FilterDomain[];
        count: boolean;
    };
};

export const FILTER_KEYS = Object.keys(
    SIDEBAR_FILTER_META
) as (keyof FiltersState)[];

export const TAXA_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) => SIDEBAR_FILTER_META[key].domain.includes('taxa'));

export const OCCURRENCE_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) => SIDEBAR_FILTER_META[key].domain.includes('observations'));
