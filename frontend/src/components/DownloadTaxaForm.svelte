<script lang="ts">
    import { getActiveTaxaContext } from '../contexts/activeTaxaContext';
    import { getFiltersContext } from '../contexts/filtersContext';
    import { getTaxaDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import INatFilterSection from './FiltersSection/INatFilterSection.svelte';
    import RankFilterSection from './FiltersSection/RankFilterSection.svelte';
    // import TaxonFilterSection from './FiltersSection/_TaxonFilterSection.svelte';

    const filters = getFiltersContext();
    const taxaContext = getActiveTaxaContext();

    async function requestTaxaDownload(
        estimate: boolean,
        onProgress?: (received: number) => void
    ) {
        const filteredTaxonIDs = taxaContext.taxa.ids;
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
    <DownloadAndFiltersForm
        header="Download Ranked Taxa TSV"
        requestHandler={requestTaxaDownload}
    >
        <div id="taxa-download-filters">
            <!-- <TaxonFilterSection /> -->
            <INatFilterSection />
            <RankFilterSection />
        </div>
    </DownloadAndFiltersForm>
</div>

<style>
    #download-form-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 100%;
    }
    #taxa-download-filters {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
</style>
