<script lang="ts">
    import { getRankingsContext } from '../contexts/rankingsContext';
    import { getTaxaDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import TaxaFilters from './FiltersSection/TaxaFilters.svelte';

    const rankingsContext = getRankingsContext();

    let visibleTaxonIDs = $derived(rankingsContext.visibleTaxonIDs);

    async function requestTaxaDownload(
        estimate: boolean,
        onProgress?: (received: number) => void
    ) {
        const response = await getTaxaDownload(
            visibleTaxonIDs,
            estimate,
            onProgress
        );
        if (estimate && response) return response;
        return null;
    }
</script>

<div id="download-form-wrapper">
    <DownloadAndFiltersForm requestHandler={requestTaxaDownload}>
        <TaxaFilters header="Download Ranked Taxa TSV" />
    </DownloadAndFiltersForm>
</div>

<style>
    #download-form-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 100%;
    }
</style>
