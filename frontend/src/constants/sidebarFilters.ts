import {
    initialFiltersState,
    type FiltersState,
} from '../contexts/filtersContext';

// The scope of a given filter--whether it targets taxa or observation data
// This is used to trigger certain warnings
export type FiltersDomain = 'observations' | 'taxa';

// Grab defaults from initial state object
const FILTER_DEFAULTS = initialFiltersState;

export type SidebarFilterMetaItem<T = unknown> = {
    default: T;
    domain: FiltersDomain[];
    count: boolean;
    group?: string;
    isActive?: (value: T) => boolean;
};

// Collection of sidebar filters and their defaults, as well as whether or not they
// should be counted with tallying applied filters
export const SIDEBAR_FILTER_META: Record<
    keyof FiltersState,
    SidebarFilterMetaItem<any>
> = {
    nSRanks: {
        default: FILTER_DEFAULTS.nSRanks,
        domain: ['taxa'],
        count: true,
    },
    datasets: {
        default: FILTER_DEFAULTS.datasets,
        domain: ['observations', 'taxa'],
        count: true,
    },
    dateEnd: {
        default: FILTER_DEFAULTS.dateEnd,
        domain: ['observations', 'taxa'],
        count: true,
        group: 'dateRange',
    },
    dateStart: {
        default: FILTER_DEFAULTS.dateStart,
        domain: ['observations', 'taxa'],
        count: true,
        group: 'dateRange',
    },
    includeINat: {
        default: FILTER_DEFAULTS.includeINat,
        domain: ['observations'],
        count: true,
    },
    taxonRank: {
        default: FILTER_DEFAULTS.taxonRank,
        domain: ['taxa'],
        count: true,
    },
    regions: {
        default: FILTER_DEFAULTS.regions,
        domain: ['taxa'],
        count: true,
        isActive: (value) => value.ids.length > 0,
    },
    coordUncertainty: {
        default: FILTER_DEFAULTS.coordUncertainty,
        domain: ['observations'],
        count: true,
    },
} satisfies {
    [K in keyof FiltersState]: SidebarFilterMetaItem<FiltersState[K]>;
};

export const FILTER_KEYS = Object.keys(
    SIDEBAR_FILTER_META
) as (keyof FiltersState)[];

export const TAXA_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) =>
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes('taxa')
);

export const OCCURRENCE_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) =>
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes(
        'observations'
    )
);
