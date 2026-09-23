import {
    initialFiltersState,
    type FiltersState,
} from '../contexts/filtersContext';
import type { NSRank } from '../types/api';

// The scope of a given filter--whether it targets taxa or observation data
// This is used to trigger certain warnings
export type FiltersDomain = 'observation' | 'taxon';

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
    affectsRankMetrics: boolean; // Whether or not the filter would affect ranking shown in sidebar (for reactivity)
    read?: (value: T) => unknown; // Reactive accessor override for non-primitive fields
    format: (value: T) => string | null; // Access value for display purposes
};

function isEqual(a: unknown, b: unknown): boolean {
    return JSON.stringify(a) === JSON.stringify(b);
}

export function isFilterActive<K extends keyof FiltersState>(
    key: K,
    value: FiltersState[K]
): boolean {
    const meta = SIDEBAR_FILTER_META[key];
    const compareValue = meta.read ? meta.read(value) : value;
    const compareDefault = meta.read ? meta.read(meta.default) : meta.default;
    return !isEqual(compareValue, compareDefault);
}

// Collection of sidebar filters and their defaults, as well as whether or not they
// should be counted with tallying applied filters
export const SIDEBAR_FILTER_META: Record<
    keyof FiltersState,
    SidebarFilterMetaItem<any>
> = {
    parentTaxa: {
        default: FILTER_DEFAULTS.parentTaxa,
        domain: ['taxon'],
        count: true,
        affectsRankMetrics: false,
        format: (taxa: (typeof initialFiltersState)['parentTaxa']) => {
            const canonicalNames = taxa.map((taxon) => taxon.canonicalName);
            return taxa.length > 3
                ? `${taxa.length} parent taxa`
                : `Parent Taxa: ${canonicalNames.join(', ')}`;
        },
    },
    nSRanks: {
        default: FILTER_DEFAULTS.nSRanks,
        domain: ['taxon'],
        affectsRankMetrics: false,
        count: true,
        format: (value: NSRank[]) => {
            const labels = value.filter((r) => r !== null);
            return labels.length > 2
                ? `${labels.length} conservation ranks`
                : `Ranks: (${labels.join(', ')})`;
        },
    },
    datasets: {
        default: FILTER_DEFAULTS.datasets,
        domain: ['observation', 'taxon'],
        affectsRankMetrics: true,
        count: true,
        format: (value: string[]) => {
            const labels = value.filter((r) => r !== null);
            return labels.length > 0 ? `${labels.length} datasets` : null;
        },
    },
    dateStart: {
        default: FILTER_DEFAULTS.dateStart,
        domain: ['observation', 'taxon'],
        affectsRankMetrics: true,
        count: true,
        format: (value) =>
            value ? `Starting ${value.toLocaleDateString()}` : null,
    },
    dateEnd: {
        default: FILTER_DEFAULTS.dateEnd,
        domain: ['observation', 'taxon'],
        affectsRankMetrics: true,
        count: true,
        format: (value) =>
            value ? `Ending ${value.toLocaleDateString()}` : null,
    },
    includeINat: {
        default: FILTER_DEFAULTS.includeINat,
        domain: ['observation', 'taxon'],
        affectsRankMetrics: true,
        count: true,
        format: (value) => (value ? null : 'Excluding iNat'),
    },
    regions: {
        default: FILTER_DEFAULTS.regions,
        domain: ['taxon'],
        affectsRankMetrics: false,
        count: true,
        read: (value) => value.ids,
        format: (value) => {
            const unit = value.ids.length > 1 ? 'regions' : 'region';
            return value.ids.length > 0 ? `${value.ids.length} ${unit}` : null;
        },
    },
    coordUncertainty: {
        default: FILTER_DEFAULTS.coordUncertainty,
        domain: ['observation', 'taxon'],
        affectsRankMetrics: true,
        count: true,
        format: (value) => (value ? `Max Uncertainty: ${value}m` : null),
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
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes('taxon')
);

// Collection of observations-domain filter keys
export const OCCURRENCE_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) =>
    (SIDEBAR_FILTER_META[key] as SidebarFilterMetaItem).domain.includes(
        'observation'
    )
);

// Collection of all rank-affecting filter keys
export const RANK_AFFECTING_FILTER_KEYS = (
    Object.keys(SIDEBAR_FILTER_META) as (keyof FiltersState)[]
).filter((key) => SIDEBAR_FILTER_META[key].affectsRankMetrics);

// Get keys of currently active filters (as defined by their isActive attribute)
export function getActiveFilterKeys(
    desiredKeys: (keyof FiltersState)[],
    currentFiltersState: FiltersState
): (keyof FiltersState)[] {
    return desiredKeys.filter((key) => {
        return isFilterActive(key, currentFiltersState[key]);
    });
}

// Accessor function for getting filters
// (or for kicking off reactivity for rank-affecting filters when used in an $effect)
export function getFilterValues(
    desiredKeys: (keyof FiltersState)[],
    currentFiltersState: FiltersState,
    exclude: (keyof FiltersState)[] = []
) {
    const excluded = new Set(exclude);
    return Object.fromEntries(
        desiredKeys
            .filter((key) => !excluded.has(key))
            .map((key) => {
                const meta = SIDEBAR_FILTER_META[key];
                const raw = currentFiltersState[key];
                return [key, meta.read ? meta.read(raw as never) : raw];
            })
    ) as Pick<FiltersState, (typeof FILTER_KEYS)[number]>;
}
