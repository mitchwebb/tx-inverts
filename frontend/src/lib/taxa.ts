import { taxaTree } from '../contexts/TaxaTree';
import type { ActiveTaxon } from '../contexts/activeTaxaContext';
import type { FiltersState } from '../contexts/filtersContext';
import type { RawNSValues, RawTaxonInfo, TaxonNodeType } from '../types/api';
import { deduplicateStringArray } from '../util/deduplicateArray';

/**
 * Simple request to GBIF API to get common names for a given taxonID
 * Filters to English common names from ITIS. Deduplicates using deduplicateStringArray
 * @param taxonID
 * @returns {string[]} Array of common name strings
 */
export async function getCommonNames(taxonID: ActiveTaxon['taxonID']) {
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
                    option.source ===
                        'Integrated Taxonomic Information System (ITIS)'
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
export async function getTaxonInfo(taxonID: ActiveTaxon['taxonID']) {
    const url = `/server/taxa/get_taxon_info?taxon_id=${taxonID}`;
    const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
        const result = await response.json();
        const detail = result?.detail ?? 'Unknown error';
        throw new Error(detail);
    }
    return (await response.json()) as RawTaxonInfo;
}

let abortController = new AbortController();

// Get nSMetrics of activeSpecies (plus observationCount since it's convenient)
export async function getNSMetrics(
    taxonID: ActiveTaxon['taxonID'],
    includeINat: FiltersState['includeINat'],
    dateStart: FiltersState['dateStart'],
    dateEnd: FiltersState['dateEnd'],
    datasets: FiltersState['datasets'],
    signal?: AbortSignal
) {
    // Cancel previous request if necessary
    if (abortController) abortController.abort();
    abortController = new AbortController();

    const nSMetricsURL = '/server/rankings/get_ns_metrics';
    const response = await fetch(nSMetricsURL, {
        signal,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            taxon_id: taxonID,
            include_inat: includeINat,
            date_start: dateStart?.toISOString(),
            date_end: dateEnd?.toISOString(),
            datasets: [...datasets],
        }),
    });
    if (!response.ok) {
        const result = await response.json();
        const detail = result?.detail ?? 'Unknown error';
        throw new Error(detail);
    }
    return (await response.json()) as RawNSValues;
}

// Logic for loading backbone structure into browser
export async function loadBackbone() {
    const url = 'server/taxa/get_backbone';
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const tree: TaxonNodeType[] = await response.json();

        if (tree) {
            const taxaMap = new Map(tree.map((node) => [node.taxon_id, node]));
            taxaTree.set(taxaMap);
        }
        return;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Get list of qualified taxon_ids from backend, given various taxa/observation filters
export async function getQualifiedTaxa(
    dateStart: FiltersState['dateStart'],
    dateEnd: FiltersState['dateEnd'],
    datasets: FiltersState['datasets'],
    regionIDs: string[],
    signal?: AbortSignal
) {
    const url = 'server/taxa/get_qualified_taxa';
    if (!dateStart && !dateEnd && !datasets.length && !regionIDs.length)
        return null;
    try {
        const response = await fetch(url, {
            signal,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_ids: [1],
                date_start: dateStart?.toISOString(),
                date_end: dateEnd?.toISOString(),
                datasets: [...datasets],
                regions: regionIDs,
            }),
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
}
