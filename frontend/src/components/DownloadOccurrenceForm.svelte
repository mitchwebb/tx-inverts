<script lang="ts">
    import Toggle from '../common/Toggle.svelte';
    import { getActiveTaxonContext } from '../contexts/activeTaxonContext';
    import { getFiltersContext } from '../contexts/filtersContext';
    import { getOccurrenceDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import DatasetFilterSection from './FiltersSection/DatasetFilterSection.svelte';
    import DateFilterSection from './FiltersSection/DateFilterSection.svelte';
    import INatFilterSection from './FiltersSection/INatFilterSection.svelte';

    const filters = getFiltersContext();
    const taxonContext = getActiveTaxonContext();

    let includeInvasives: boolean = $state(false);

    async function requestOccurrenceDownload(
        estimate: boolean,
        onProgress?: (received: number) => void
    ) {
        // Get list of just taxonIDs from filtered taxa list
        const response = await getOccurrenceDownload(
            taxonContext.taxonID || 1,
            filters.includeINat,
            filters.dateStart,
            filters.dateEnd,
            filters.dataProviders,
            includeInvasives,
            estimate,
            onProgress
        );
        if (estimate && response) return response;
        return null;
    }

    function handleInvasivesToggle() {
        includeInvasives = !includeInvasives;
    }
</script>

<DownloadAndFiltersForm
    header="Download Occurrence Records"
    requestHandler={requestOccurrenceDownload}
>
    <div id="occurrence-download-filters">
        <div class="occurrence-taxa-wrapper">
            <div class="filters-section selected-taxa-section">
                <div class="filters-section-header">
                    <span>Selected Taxa:</span>
                </div>
                <div class="selected-taxon-content">
                    <span>{taxonContext.taxonInfo.canonicalName}</span>
                </div>
            </div>
            <div class="filters-section invasives-filter-section">
                <div class="filters-section-header">
                    <span>Invasive Taxa:</span>
                </div>
                <div class="selected-taxon-content">
                    <div class="icon invasives-toggle">
                        <Toggle
                            handler={handleInvasivesToggle}
                            checked={includeInvasives}
                        />
                    </div>
                    <span>Include Invasive Subtaxa</span>
                </div>
            </div>
        </div>
        <INatFilterSection />
        <DatasetFilterSection />
        <DateFilterSection />
    </div>
</DownloadAndFiltersForm>

<style>
    .selected-taxa-section {
        width: 50%;
    }
    .invasives-filter-section {
        width: 50%;
    }
    .invasives-toggle {
        stroke: var(--text-default);
    }
    .occurrence-taxa-wrapper {
        display: flex;
        gap: 0.5rem;
        width: 100%;
    }
    .selected-taxon-content {
        text-align: left;
        display: flex;
        gap: 0.5rem;
    }
    #occurrence-download-filters {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
</style>
