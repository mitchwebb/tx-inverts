import type { EstimateMetrics, RawEstimateMetrics } from '../types/api';

export async function getDownload(
    endpoint: string,
    filename: string,
    body: object,
    getEstimate: boolean,
    onProgress?: (bytesReceived: number) => void
): Promise<EstimateMetrics | number | null> {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...body,
                get_estimate: getEstimate,
            }),
        });
        if (!response.ok)
            throw new Error(`Response status: ${response.status}`);
        if (getEstimate) {
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

// // Thin wrapper for specific, allowed downloads
// export async function getOccurrenceDownload(
//     taxonIDs: number[],
//     includeINat: FiltersState['includeINat'],
//     dateStart: FiltersState['dateStart'],
//     dateEnd: FiltersState['dateEnd'],
//     datasets: FiltersState['datasets'],
//     coordUncertainty: FiltersState['coordUncertainty'],
//     includeInvasives: boolean,
//     getEstimate: boolean,
//     onProgress?: (received: number) => void
// ) {
//     return getDownload(
//         'server/downloads/get_occurrence_download',
//         'occurrence_download.tsv',
//         {
//             taxon_ids: taxonIDs,
//             include_inat: includeINat,
//             date_start: dateStart?.toISOString(),
//             date_end: dateEnd?.toISOString(),
//             datasets: datasets,
//             coordUncertainty: coordUncertainty,
//             include_invasives: includeInvasives,
//         },
//         estimate,
//         onProgress
//     );
// }

export async function getTaxaDownload(
    filteredIDs: number[],
    getEstimate: boolean,
    onProgress?: (received: number) => void
) {
    return getDownload(
        'server/downloads/get_ranked_taxa_download',
        'taxa_download.tsv',
        {
            taxon_ids: filteredIDs,
        },
        getEstimate,
        onProgress
    );
}
