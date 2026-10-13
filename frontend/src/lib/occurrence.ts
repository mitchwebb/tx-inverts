import { datasets } from '../contexts/Datasets';
import type {
    ActiveTaxon,
    initialActiveTaxaState,
} from '../contexts/activeTaxaContext';
import type { FiltersState } from '../contexts/filtersContext';
import type { RawDateRange } from '../types/api';
import { serializeFilters } from '../util/requests';

// Get observation counts for each dataset for current taxon
export async function getDatasetCounts(
    taxonID: ActiveTaxon['taxonID'],
    filters: FiltersState
) {
    try {
        const response = await fetch('/server/occurrence/get_dataset_counts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_id: taxonID,
                ...serializeFilters(filters),
            }),
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        const result: ActiveTaxon['datasetCounts'] = json;
        return result;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Logic for loading data datasets structure into browser
export async function loadDatasets() {
    const url = `server/occurrence/get_datasets`;
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();

        type RawDataset = {
            dataset_key: string;
            dataset_title: string;
        };

        const result: RawDataset[] = json.datasets;
        if (result) {
            const map = Object.fromEntries(
                result.map((d) => [
                    d.dataset_key,
                    {
                        datasetTitle: d.dataset_title,
                    },
                ])
            );
            datasets.set(map);
        }
        return;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Fetches observation date ranges based on current taxon and inat inclusion
export async function getObservationDates(
    taxonID: ActiveTaxon['taxonID'],
    filters: FiltersState
) {
    try {
        const response = await fetch(
            'server/occurrence/get_observation_dates',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    taxon_id: taxonID,
                    ...serializeFilters(filters),
                }),
            }
        );
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();

        const result: RawDateRange = json;

        return { minDate: result.min_date, maxDate: result.max_date };
    } catch (error) {
        console.error(error);
        return null;
    }
}

export async function getDateCounts(
    taxonID: ActiveTaxon['taxonID'],
    filters: FiltersState
) {
    try {
        const response = await fetch('server/occurrence/get_date_counts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_id: taxonID,
                ...serializeFilters(filters),
            }),
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json: Record<string, number>[] = await response.json();
        return json;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Calculate occurrence totals for each dataset for currently active taxa
export function getDatasetCountTotals(
    taxaContext: typeof initialActiveTaxaState
): Record<string, number> {
    const totals = Object.values(taxaContext.taxa.items).reduce(
        (acc, taxon) => {
            if (!taxon.datasetCounts) return acc;
            for (const [dataset, count] of Object.entries(
                taxon.datasetCounts
            )) {
                acc[dataset] = (acc[dataset] ?? 0) + count;
            }
            return acc;
        },
        {} as Record<string, number>
    );
    return totals;
}
