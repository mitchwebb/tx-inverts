import {
    isFilterActive,
    SIDEBAR_FILTER_META,
    type FiltersDomain,
} from '../constants/sidebarFilters';
import { type FiltersState } from '../contexts/filtersContext';

// Using the passed current filters state, determine the number of active filters
// Optionally, count only those filters with a defined domain or path
export function countActiveFilters(
    filters: FiltersState,
    domain?: FiltersDomain | null // Include only filters relevant to domain
    // path?: RouterPath | null // Include only filters relevant to path
): number {
    let activeFilters = new Set<string>();

    for (const [filterKey, meta] of Object.entries(SIDEBAR_FILTER_META)) {
        if (meta.count === false) continue;

        const key = filterKey as keyof FiltersState;
        const value = filters[key];
        const isActive = isFilterActive(key, value as never);

        if (
            isActive &&
            (!domain || meta.domain.includes(domain)) // Domain value check
            // (!path || meta.path.includes(path)) // Path value check
        ) {
            activeFilters.add(filterKey);
        }
    }

    return activeFilters.size;
}
