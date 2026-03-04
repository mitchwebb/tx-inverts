import { taxaTree } from '../contexts/TaxaTree';
import type { ActiveTaxonState } from '../contexts/activeTaxonContext';
import type { FiltersState } from '../contexts/filtersContext';
import type { RawNSValues, RawTaxonInfo, TaxonNodeType } from '../types/api';
import { deduplicateStringArray } from '../util/deduplicate';

export async function getCommonNames(taxonID: ActiveTaxonState['taxonID']) {
    const commonNamesURL = `https://api.gbif.org/v1/species/${taxonID}/vernacularNames?limit=100`;
    try {
        const response = await fetch(commonNamesURL, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        // Filter for English common names
        // These parameters yield relatively sane results
        let englishNames = json.results
            .filter(
                (option: {
                    language: string;
                    source: string;
                    country: string;
                }) =>
                    (option.language === 'eng' || option.country === 'US') &&
                    (option.source ===
                        'Integrated Taxonomic Information System (ITIS)' ||
                        "Martha's Vineyard species checklist")
            )
            .map((option: { vernacularName: string }) => option.vernacularName);
        // Deduplicate English names
        englishNames = deduplicateStringArray(englishNames);
        return englishNames;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Get taxon info (triggered by change in taxonContext.activeTaxonID)
export async function getTaxonInfo(taxonID: ActiveTaxonState['taxonID']) {
    const url = '/server/taxa/get_taxon_info';
    console.log(url, taxonID);
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ taxon_ids: taxonID }),
    });

    const json = await response.json();

    if (!response.ok) {
        const detail = json?.detail ?? 'Unknown error';
        throw new Error(detail);
    }

    const result: RawTaxonInfo = json.result;
    return result;
}

let abortController = new AbortController();

// Get rangeExtent of activeSpecies (plus observationCount since it's convenient)
export async function getNSMetrics(
    taxonID: ActiveTaxonState['taxonID'],
    includeINat: FiltersState['includeINat'],
    dateStart: FiltersState['dateStart'],
    dateEnd: FiltersState['dateEnd'],
    dataProviders: FiltersState['dataProviders']
) {
    // Cancel previous request if necessary
    if (abortController) abortController.abort();
    abortController = new AbortController();

    const rangeExtentURL = '/server/natureserve/get_ns_metrics';
    const signal = abortController.signal;
    const response = await fetch(rangeExtentURL, {
        signal,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            taxon_ids: taxonID,
            include_inat: includeINat,
            date_start: dateStart,
            date_end: dateEnd,
            data_providers: dataProviders,
        }),
    });
    const json = await response.json();

    if (!response.ok) {
        const detail = json?.detail ?? 'Unknown error';
        throw new Error(detail);
    }

    return json.result as RawNSValues;
}

// Logic for loading backbone structure into browser
export async function loadBackbone() {
    const url = `server/taxa/get_backbone`;
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        const result: TaxonNodeType[] = json.taxa;
        if (result) {
            taxaTree.set(result);
        }
        return;
    } catch (error) {
        console.error(error);
        return null;
    }
}
