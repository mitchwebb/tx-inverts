import {
    SIDEBAR_FILTER_META,
    type FiltersDomain,
    type SidebarFilterMetaItem,
} from '../constants/sidebarFilters';
import { type FiltersState } from '../contexts/filtersContext';

// TODO: This isn't the clearest function and could be improved
// Using the passed current filters state, determine the number of active filters
// Optionally, count only those filters with a defined domain or path
export function countActiveFilters(
    filters: FiltersState,
    domain?: FiltersDomain | null // Include only filters relevant to domain
    // path?: RouterPath | null // Include only filters relevant to path
): number {
    let activeGroups = new Set<string>();

    for (const [filterKey, meta] of Object.entries(SIDEBAR_FILTER_META)) {
        if (meta.count === false) continue;

        const value = filters[filterKey as keyof FiltersState];
        // Check if value is default value (special case for arrays)
        const isActive = meta.isActive
            ? (meta as SidebarFilterMetaItem).isActive!(value as any)
            : Array.isArray(value)
              ? value.length > 0
              : value !== meta.default;
        if (
            isActive &&
            (!domain || meta.domain.includes(domain)) // Domain value check
            // (!path || meta.path.includes(path)) // Path value check
        ) {
            const group = meta.group ?? filterKey;
            activeGroups.add(group);
        }
    }

    return activeGroups.size;
}
