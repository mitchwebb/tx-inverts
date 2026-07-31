import type { FiltersState } from '../contexts/filtersContext';

// api/filters.ts
export function serializeFilters(filters: FiltersState) {
    return {
        include_inat: filters.includeINat,
        date_start: filters.dateStart?.toISOString(),
        date_end: filters.dateEnd?.toISOString(),
        coord_uncertainty: filters.coordUncertainty,
        datasets: filters.datasets ? [...filters.datasets] : undefined,
        regions: filters.regions.ids,
        taxon_rank: filters.taxonRank,
        ns_ranks: filters.nSRanks,
    };
}
