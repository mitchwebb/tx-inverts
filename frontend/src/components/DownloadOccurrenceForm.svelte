<script lang="ts">
    import Toggle from '../common/Toggle.svelte';
    import { getActiveTaxaContext } from '../contexts/activeTaxaContext';
    import { getFiltersContext } from '../contexts/filtersContext';
    import { getOccurrenceDownload } from '../lib/downloads';
    import DownloadAndFiltersForm from './DownloadAndFiltersForm.svelte';
    import DatasetFilterSection from './FiltersSection/DatasetFilterSection.svelte';
    import DateFilterSection from './FiltersSection/DateFilterSection.svelte';
    import INatFilterSection from './FiltersSection/INatFilterSection.svelte';

    const filters = getFiltersContext();
    const taxaContext = getActiveTaxaContext();

    let includeInvasives: boolean = $state(false);

    async function requestOccurrenceDownload(
        estimate: boolean,
        onProgress?: (received: number) => void
    ) {
        // Get list of just taxonIDs from filtered taxa list
        const response = await getOccurrenceDownload(
        taxaContext.taxa.ids.length 
            ? taxaContext.taxa.ids
            : [1],
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
                <ul class="selected-taxa-content">
                    {#each taxaContext.taxa.items as taxon}
                        <li>{taxon.info.canonicalName}</li>
                    {/each}
                </ul>
            </div>
        </div>
        <div id="toggles-section">
            <div class="inat-toggle-wrapper">
                <INatFilterSection />
            </div>

            <div class="filters-section invasives-filter-section">
                <div class="filters-section-header">
                    <span>Invasive Taxa:</span>
                </div>
                <div id="invasives-toggle-wrapper">
                    <div class="icon invasives-toggle">
                        <Toggle
                            handler={handleInvasivesToggle}
                            checked={includeInvasives}
                        />
                    </div>
                    <span> Include Invasive Taxa </span>
                </div>
            </div>
        </div>

        <DatasetFilterSection />
        <DateFilterSection />
    </div>
</DownloadAndFiltersForm>

<style>
    .inat-toggle-wrapper {
        width: 100%;
    }
    #invasives-toggle-wrapper {
        display: flex;
        gap: 1rem;
    }
    #toggles-section {
        display: flex;
        gap: 0.5rem;
    }
    .selected-taxa-content li {
        white-space: nowrap;
        margin: 1px 0;
    }
    .selected-taxa-section {
        width: 100%;
    }
    .invasives-filter-section {
        width: 100%;
        height: fit-content;
    }
    .invasives-toggle {
        stroke: var(--text-default);
    }
    .occurrence-taxa-wrapper {
        display: flex;
        gap: 0.5rem;
        width: 100%;
    }
    .selected-taxa-content {
        text-align: left;
        display: flex;
        flex-direction: column;
        margin: 0;
        height: fit-content;
        /* gap: 0.5rem; */
    }
    #occurrence-download-filters {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
</style>
