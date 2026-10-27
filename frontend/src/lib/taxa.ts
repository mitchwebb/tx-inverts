import { taxaTree } from '../contexts/TaxaTree';
import type { ActiveTaxon } from '../contexts/activeTaxaContext';
import type { FiltersState } from '../contexts/filtersContext';
import type { BackboneNode, RawNSValues, TaxonInfo } from '../types/api';
import { serializeFilters } from '../util/requests';
import { registerRequest, resolveRequest } from './requestRegistry';

// Get taxon info (triggered by change in taxonContext.activeTaxonID)
export async function getTaxonInfo(taxonID: ActiveTaxon['taxonID']) {
    const url = `/server/taxon/get_taxon_info?taxon_id=${taxonID}`;

    const controller = registerRequest(taxonID, 'getTaxonInfo');

    try {
        const response = await fetch(url, {
            signal: controller.signal,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            const result = await response.json();
            const detail = result?.detail ?? 'Unknown error';
            throw new Error(detail);
        }
        return (await response.json()) as TaxonInfo;
    } finally {
        resolveRequest(taxonID, 'getTaxonInfo', controller);
    }
}

// Get nSMetrics of activeSpecies (plus observationCount since it's convenient)
export async function getNSMetrics(
    taxonID: ActiveTaxon['taxonID'],
    filters: FiltersState
) {
    const controller = registerRequest(taxonID, 'getNSMetrics');

    const nSMetricsURL = '/server/ranking/get_ns_metrics';
    try {
        const response = await fetch(nSMetricsURL, {
            signal: controller.signal,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_id: taxonID,
                ...serializeFilters(filters),
            }),
        });
        if (!response.ok) {
            const result = await response.json();
            const detail = result?.detail ?? 'Unknown error';
            throw new Error(detail);
        }
        return (await response.json()) as RawNSValues;
    } finally {
        resolveRequest(taxonID, 'getNSMetrics', controller);
    }
}

// Logic for loading backbone structure into browser
export async function loadBackbone() {
    const url = 'server/taxon/get_backbone';
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const tree: BackboneNode[] = await response.json();

        if (tree) {
            const taxaMap = new Map(tree.map((node) => [node.taxonID, node]));
            taxaTree.set(taxaMap);
        }
        return;
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Get list of qualified taxon_ids from backend, given various taxon/observation filters
// DOES NOT filter by parent taxa (uses Animalia explicitly)
export async function getQualifiedTaxa(
    filters: Partial<FiltersState>,
    signal?: AbortSignal
) {
    const url = 'server/taxon/get_qualified_taxa';
    try {
        const response = await fetch(url, {
            signal,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                taxon_ids: ['N'],
                ...serializeFilters(filters),
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
