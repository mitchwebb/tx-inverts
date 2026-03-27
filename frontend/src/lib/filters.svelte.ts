import {
    SIDEBAR_FILTER_META,
    type FilterDomain,
} from '../constants/sidebarFilters';
import { type FiltersState } from '../contexts/filtersContext';
import type { RouterPath } from '../contexts/routerContext';

// TODO: This isn't the clearest function and could be improved
// Using the passed current filters state, determine the number of active filters
// Optionally, count only those filters with a defined domain or path
export function countActiveFilters(
    filters: FiltersState,
    domain?: FilterDomain | null, // Include only filters relevant to domain
    path?: RouterPath | null // Include only filters relevant to path
): number {
    let filterCount = 0;

    for (const [filterKey, meta] of Object.entries(SIDEBAR_FILTER_META)) {
        if (meta.count === false) continue;

        const value = filters[filterKey as keyof FiltersState];
        // Check if value is default value (special case for arrays)
        const isDefault = Array.isArray(value)
            ? Array.isArray(meta.default) &&
              value.length === (meta.default as any[]).length &&
              value.every((v, i) => v === (meta.default as any[])[i])
            : value === meta.default;
        if (
            !isDefault &&
            (!domain || meta.domain.includes(domain)) && // Domain value check
            (!path || meta.path.includes(path)) // Path value check
        ) {
            console.warn(value, filterKey);
            filterCount++;
        }
    }

    return filterCount;
}
