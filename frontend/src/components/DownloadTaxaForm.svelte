<script lang="ts">
    import { getFiltersContext } from '../contexts/filtersContext';
    import { getTaxaDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import DateFilterSection from './FiltersSection/DateFilterSection.svelte';
    import INatFilterSection from './FiltersSection/INatFilterSection.svelte';
    import RankFilterSection from './FiltersSection/RankFilterSection.svelte';
    import TaxonFilterSection from './FiltersSection/TaxonFilterSection.svelte';

    const filters = getFiltersContext();

    async function requestTaxaDownload(estimate: boolean, onProgress?: (received: number) => void) {
        // Get list of just taxonIDs from filtered taxa list
        const filteredTaxonIDs = Object.keys(filters.filteredTaxa ?? {}).map(Number);
        const response = await getTaxaDownload(
                                    filteredTaxonIDs, 
                                    filters.includeINat, 
                                    filters.nSRanks, 
                                    estimate, 
                                    onProgress
                                );
        if (estimate && response) return response;
        return null;
    }
</script>

<div id="download-form-wrapper">
    <DownloadAndFiltersForm header="Download Ranked Taxa TSV" requestHandler={requestTaxaDownload}>
        <div id="taxa-download-filters">
            <TaxonFilterSection/>
            <RankFilterSection/>
            <INatFilterSection/>
        </div>
    </DownloadAndFiltersForm>
</div>

<style>
    #download-form-wrapper {
        /* padding: 0.75rem; */
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    #taxa-download-filters {
        display: flex;
        flex-direction: column;
        gap: .5rem;
    }
</style>