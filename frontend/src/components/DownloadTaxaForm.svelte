<script lang="ts">
    import { getRankingsContext } from '../contexts/rankingsContext';
    import { getTaxaDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import Filters from './FiltersSection/Filters.svelte';

    const rankingsContext = getRankingsContext();

    let visibleTaxonIDs = $derived(rankingsContext.visibleTaxonIDs);

    async function requestTaxaDownload(
        getEstimate: boolean,
        onProgress?: (received: number) => void
    ) {
        const response = await getTaxaDownload(
            visibleTaxonIDs,
            getEstimate,
            onProgress
        );
        if (getEstimate && response) return response;
        return null;
    }
</script>

<div id="download-form-wrapper">
    <DownloadAndFiltersForm requestHandler={requestTaxaDownload}>
        <Filters
            domain="taxa"
            header="Download Ranked Taxa TSV"
            includeButtons={false}
        />
    </DownloadAndFiltersForm>
</div>

<style>
    #download-form-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 100%;
    }
</style>
