import type { FiltersState } from '../contexts/filtersContext';

export function buildTileURL(taxonID: string, filters: FiltersState): string {
    const query = new URLSearchParams();
    query.set('include_inat', String(filters.includeINat));
    query.set('taxon_id', String(taxonID));

    if (
        filters.coordUncertainty !== null &&
        filters.coordUncertainty !== undefined
    ) {
        query.set('coord_uncertainty', String(filters.coordUncertainty));
    }
    if (filters.dateStart !== null && filters.dateStart !== undefined) {
        query.set('date_start', filters.dateStart.toISOString());
    }
    if (filters.dateEnd !== null && filters.dateEnd !== undefined) {
        query.set('date_end', filters.dateEnd.toISOString());
    }
    if (filters.datasets) {
        for (const d of filters.datasets.filter((d) => d != null)) {
            query.append('datasets', d);
        }
    }

    return `${window.location.origin}/server/occurrence/tiles/{z}/{x}/{y}.mvt?${query.toString()}`;
}
