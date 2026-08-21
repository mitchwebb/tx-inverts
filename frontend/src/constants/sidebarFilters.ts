import {
    initialFiltersState,
    type FiltersState,
} from '../contexts/filtersContext';

// The scope of a given filter--whether it targets taxa or observation data
// This is used to trigger certain warnings
export type FiltersDomain = 'observations' | 'taxa';

// Grab defaults from initial state object
const FILTER_DEFAULTS = initialFiltersState;

/**
 * Information for a given sidebar filter, helping control its behavior across the app
 * @param default - Filter default value, used to determine if activation or to reset
 * @param domain - Domain of given filter, used to identify what type of information it affects
 * @param count - Whether or not filter should be visually 'counted' when active on our sidebar
 * @param affectsRankMetrics - Whether or not given filter should trigger NSMetric recalculation
 * @param group - Filter group, can be used to couple multiple filters when counting active filters
 * @param read - Optional accessor override for non-primitive fields, used to call value in $effect
 * @param isActive - Optional way of determining the state of the filter for non-primitive fields
 */
export type SidebarFilterMetaItem<T = unknown> = {
    default: T;
    domain: FiltersDomain[];
    count: boolean;
    affectsRankMetrics: boolean;
    group?: string;
    read?: (value: T) => unknown; // reactive accessor override for non-primitive fields
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
        affectsRankMetrics: false,
        count: true,
    },
    datasets: {
        default: FILTER_DEFAULTS.datasets,
        domain: ['observations', 'taxa'],
        affectsRankMetrics: true,
        count: true,
    },
    dateEnd: {
        default: FILTER_DEFAULTS.dateEnd,
        domain: ['observations', 'taxa'],
        affectsRankMetrics: true,
        count: true,
        group: 'dateRange',
    },
    dateStart: {
        default: FILTER_DEFAULTS.dateStart,
        domain: ['observations', 'taxa'],
        affectsRankMetrics: true,
        count: true,
        group: 'dateRange',
    },
    includeINat: {
        default: FILTER_DEFAULTS.includeINat,
        domain: ['observations', 'taxa'],
        affectsRankMetrics: true,
        count: true,
    },
    taxonRank: {
        default: FILTER_DEFAULTS.taxonRank,
        domain: ['taxa'],
        affectsRankMetrics: false,
        count: true,
    },
    regions: {
        default: FILTER_DEFAULTS.regions,
        domain: ['taxa'],
        affectsRankMetrics: false,
        count: true,
        isActive: (value) => value.ids.length > 0,
        read: (value) => value.ids,
    },
    coordUncertainty: {
        default: FILTER_DEFAULTS.coordUncertainty,
        domain: ['observations', 'taxa'],
        affectsRankMetrics: true,
        count: true,
    },
} satisfies {
    [K in keyof FiltersState]: SidebarFilterMetaItem<FiltersState[K]>;
};

// Collection of all filter keys
export const FILTER_KEYS = Object.keys(
    SIDEBAR_FILTER_META
) as (keyof FiltersState)[];

// Collection of taxa-domain filter keys
export const TAXA_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) =>
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes('taxa')
);

// Collection of observations-domain filter keys
export const OCCURRENCE_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) =>
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes(
        'observations'
    )
);

// Collection of all rank-affecting filter keys
export const RANK_AFFECTING_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) => SIDEBAR_FILTER_META[key].affectsRankMetrics);

// Accessor function for kicking off reactivity for rank-affecting filters
// to be used in an $effect
export function getRankAffectingFilterValues(
    filters: FiltersState,
    exclude: (keyof FiltersState)[] = []
) {
    const excluded = new Set(exclude);
    return Object.fromEntries(
        RANK_AFFECTING_FILTER_KEYS.filter((key) => !excluded.has(key)).map(
            (key) => {
                const meta = SIDEBAR_FILTER_META[key];
                const raw = filters[key];
                return [key, meta.read ? meta.read(raw as never) : raw];
            }
        )
    ) as Pick<FiltersState, (typeof RANK_AFFECTING_FILTER_KEYS)[number]>;
}
