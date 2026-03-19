import { dataProviders } from '../contexts/DataProviders';
import type { ActiveTaxon } from '../contexts/activeTaxaContext';
import type { FiltersState } from '../contexts/filtersContext';
import type { RawDateRange } from '../types/api';

// Get observation counts for each provider for current taxon
export async function getProviderCounts(
    activeTaxonID: ActiveTaxon['taxonID'],
    includeINat: FiltersState['includeINat'],
    dateStart: FiltersState['dateStart'],
    dateEnd: FiltersState['dateEnd']
) {
    try {
        const response = await fetch('/server/occurrence/get_provider_counts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_ids: activeTaxonID,
                include_inat: includeINat,
                date_start: dateStart,
                date_end: dateEnd,
            }),
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        const result: ActiveTaxon['providerCounts'] = json;
        return result;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Logic for loading data providers structure into browser
export async function loadDataProviders() {
    const url = `server/occurrence/get_data_providers`;
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();

        type RawDataProvider = {
            dataset_key: string;
            publisher: string;
            institution_code: string;
        };

        const result: RawDataProvider[] = json.data_providers;
        if (result) {
            const map = Object.fromEntries(
                result.map((d) => [
                    d.institution_code,
                    {
                        institutionName: d.publisher,
                        datasetKey: d.dataset_key,
                    },
                ])
            );
            dataProviders.set(map);
        }
        return;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Fetches observation date ranges based on current taxon and inat inclusion
export async function getObservationDates(
    activeTaxonID: ActiveTaxon['taxonID'],
    includeINat: FiltersState['includeINat']
) {
    try {
        const response = await fetch(
            'server/occurrence/get_observation_dates',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    taxon_ids: activeTaxonID,
                    include_inat: includeINat,
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

// export async function downloadDWCOccurrences(
//     activeTaxonID: ActiveTaxonState['taxonID'],
//     includeINat: FiltersState['includeINat'],
//     dateStart: FiltersState['dateStart'],
//     dateEnd: FiltersState['dateEnd']
// );
