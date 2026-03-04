import type { FiltersState } from '../contexts/filtersContext';
import type { EstimateMetrics, RawEstimateMetrics } from '../types/api';

export async function getDownload(
    endpoint: string,
    filename: string,
    body: object,
    estimate: boolean,
    onProgress?: (bytesReceived: number) => void
): Promise<EstimateMetrics | number | null> {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...body,
                estimate,
            }),
        });
        if (!response.ok)
            throw new Error(`Response status: ${response.status}`);
        if (estimate) {
            const result: RawEstimateMetrics = await response.json();
            const estimateMetrics: EstimateMetrics = {
                sizeEstimate: result.size_estimate,
                rowCount: result.row_count,
            };
            return estimateMetrics;
        } else {
            const reader = response.body!.getReader();
            let receivedLength = 0;
            const chunks: Uint8Array<ArrayBuffer>[] = [];
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                chunks.push(value);
                receivedLength += value.length;
                if (onProgress) onProgress(receivedLength);
            }
            const blob = new Blob(chunks);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();

            window.URL.revokeObjectURL(url);
            return null;
        }
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Thin wrapper for specific, allowed downloads
export async function getOccurrenceDownload(
    taxonID: number,
    includeINat: FiltersState['includeINat'],
    dateStart: FiltersState['dateStart'],
    dateEnd: FiltersState['dateEnd'],
    dataProviders: FiltersState['dataProviders'],
    includeInvasives: boolean,
    estimate: boolean,
    onProgress?: (received: number) => void
) {
    return getDownload(
        'server/downloads/get_occurrence_download',
        'occurrence_download.tsv',
        {
            taxon_ids: [taxonID],
            include_inat: includeINat,
            date_start: dateStart,
            date_end: dateEnd,
            data_providers: dataProviders,
            include_invasives: includeInvasives,
        },
        estimate,
        onProgress
    );
}

export async function getTaxaDownload(
    taxonIDs: number[],
    includeINat: FiltersState['includeINat'],
    nSRanks: FiltersState['nSRanks'],
    estimate: boolean,
    onProgress?: (received: number) => void
) {
    taxonIDs = taxonIDs.length > 0 ? taxonIDs : [1];
    return getDownload(
        'server/downloads/get_ranked_taxa_download',
        'taxa_download.tsv',
        {
            taxon_ids: taxonIDs,
            include_inat: includeINat,
            ns_ranks: nSRanks,
        },
        estimate,
        onProgress
    );
}

// export async function getOccurrenceDownload(
//     taxonID: number,
//     includeINat: FiltersState['includeINat'],
//     dateStart: FiltersState['dateStart'],
//     dateEnd: FiltersState['dateEnd'],
//     dataProviders: FiltersState['dataProviders'],
//     estimate: boolean
// ) {
//     try {
//         const response = await fetch(
//             'server/downloads/get_occurrence_download',
//             {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({
//                     taxon_ids: [taxonID],
//                     include_inat: includeINat,
//                     date_start: dateStart,
//                     date_end: dateEnd,
//                     data_providers: dataProviders,
//                     estimate: estimate,
//                 }),
//             }
//         );
//         if (!response.ok) {
//             throw new Error(`Response status: ${response.status}`);
//         }
//         if (estimate) {
//             const result: RawEstimateMetrics = await response.json();
//             const estimateMetrics: EstimateMetrics = {
//                 sizeEstimate: result.size_estimate,
//                 rowCount: result.row_count,
//             };
//             return estimateMetrics;
//         } else {
//             const blob = await response.blob();
//             const url = window.URL.createObjectURL(blob);

//             const a = document.createElement('a');
//             a.href = url;
//             a.download = 'occurrence_download.tsv';
//             a.click();

//             window.URL.revokeObjectURL(url);
//             return null;
//         }
//     } catch (error) {
//         console.error(error);
//         return null;
//     }
// }

// export async function getTaxaDownload(
//     taxonIDs: number[],
//     includeINat: FiltersState['includeINat'],
//     nSRanks: FiltersState['nSRanks'],
//     estimate: boolean
// ) {
//     try {
//         taxonIDs = taxonIDs.length > 0 ? taxonIDs : [1];
//         const response = await fetch(
//             'server/downloads/get_ranked_taxa_download',
//             {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({
//                     taxon_ids: taxonIDs,
//                     include_inat: includeINat,
//                     ns_ranks: nSRanks,
//                     estimate: estimate,
//                 }),
//             }
//         );
//         if (!response.ok) {
//             throw new Error(`Response status: ${response.status}`);
//         }
//         if (estimate) {
//             const result: RawEstimateMetrics = await response.json();
//             const estimateMetrics: EstimateMetrics = {
//                 sizeEstimate: result.size_estimate,
//                 rowCount: result.row_count,
//             };
//             return estimateMetrics;
//         } else {
//             const blob = await response.blob();
//             const url = window.URL.createObjectURL(blob);

//             const a = document.createElement('a');
//             a.href = url;
//             a.download = 'taxa_download.tsv';
//             a.click();

//             window.URL.revokeObjectURL(url);
//             return null;
//         }
//     } catch (error) {
//         console.error(error);
//         return null;
//     }
// }
