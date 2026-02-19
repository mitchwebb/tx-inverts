import {
    SIDEBAR_FILTER_META,
    type FilterDomain,
} from '../constants/sidebarFilters';
import { type FiltersState } from '../contexts/filtersContext';

// Using the passed current filters state, determine the number of active filters
// Optionally, count only those filters with a defined domain
export function countActiveFilters(
    filters: FiltersState,
    domain?: FilterDomain
): number {
    let filterCount = 0;

    for (let filterKey in SIDEBAR_FILTER_META) {
        const meta = SIDEBAR_FILTER_META[filterKey as keyof FiltersState];
        if (meta.count === false) continue;

        const value = filters[filterKey as keyof FiltersState];
        if (value !== meta.default && (meta.domain === domain || !domain)) {
            filterCount++;
        }
    }

    return filterCount;
}
