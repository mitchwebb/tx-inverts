<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import Toggle from '../../common/Toggle.svelte';
    import type { FiltersDomain } from '../../constants/sidebarFilters';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { datasets } from '../../contexts/Datasets';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import { toggleArrayValue } from '../../util/toggleArrayValue';

    type DatasetFilterProps = {
        header?: string;
        domain?: FiltersDomain;
        showCounts?: boolean;
    };

    const {
        header = 'Datasets',
        showCounts = true,
        domain = 'observations',
    }: DatasetFilterProps = $props();

    const filtersContext = getFiltersContext();
    const taxaContext = getActiveTaxaContext();

    const iNatActive = $derived(filtersContext.includeINat);

    // Determine datasetCounts added across all taxa
    let datasetCounts = $derived(
        Object.values(taxaContext.taxa.items).reduce(
            (acc, taxon) => {
                if (!taxon.datasetCounts) return acc;
                for (const [dataset, count] of Object.entries(
                    taxon.datasetCounts
                )) {
                    acc[dataset] = (acc[dataset] ?? 0) + count;
                }
                return acc;
            },
            {} as Record<string, number>
        )
    );

    const higherTaxaActive = $derived(
        taxaContext.taxa.ids.some((id) => {
            const taxon = taxaContext.taxa.get(id);
            const taxonRank = taxon?.info.taxonRank;
            return taxonRank && !['species', 'subspecies'].includes(taxonRank);
        })
    );

    // Derive a unified list of datasets
    const datasetList = $derived.by(() => {
        if (!$datasets) return [];
        // If in observations domain and taxa selected,
        // OR if in taxa domain and parent taxa selected
        if (
            (domain === 'observations' && taxaContext.taxa.ids.length) ||
            (domain === 'taxa' && higherTaxaActive)
        ) {
            // Filter to relevant datasets
            return Object.entries(datasetCounts).map(([key, count]) => ({
                datasetKey: key,
                datasetTitle: $datasets?.[key]?.datasetTitle,
                count,
            }));
        } else {
            // Else, show all datasets
            return Object.entries($datasets).map(([key, info]) => ({
                datasetKey: key,
                datasetTitle: info.datasetTitle,
                count: null,
            }));
        }
    });

    // Track show/hide state of list
    let showAll = $state(false);
    // Number of datasets to show by default
    const SHOW_LIMIT = 5;

    // List of datasets visible (given show/hide state)
    const visibleDatasets = $derived(
        showAll ? datasetList : datasetList.slice(0, SHOW_LIMIT)
    );

    function handleDataDataset({ value, checked }: CheckboxPayload) {
        // Get list of currently selected datasets
        let currDatasets = filtersContext.datasets ?? [];

        // Update reactive state
        filtersContext.datasets = toggleArrayValue<string>(
            currDatasets,
            value,
            checked
        );
    }

    // Determine if observationsMetrics are loading for any taxa
    const observationsMetricsLoading = $derived(
        Object.values(taxaContext.taxa.items).some(
            (taxon) => taxon.observationMetricsLoading
        )
    );

    function handleINatToggle(checked: boolean) {
        filtersContext.includeINat = checked;
    }
</script>

{#if $datasets}
    <div
        class="datasets-section filters-section"
        class:active={!!filtersContext.datasets?.length ||
            !filtersContext.includeINat}
    >
        <div id="datasets-header" class="filters-section-header">
            <div class="datasets-header-and-icon">
                <span>{header}</span>
            </div>
            <div class="inat-toggle-wrapper">
                <div class="inat-toggle">
                    <Toggle
                        handler={handleINatToggle}
                        checked={iNatActive}
                        onColor="darkgreen"
                        offColor="darkred"
                    />
                </div>
                <span class="inat-label">Include iNat Data</span>
            </div>
        </div>
        <div class="filters-section-content datasets-content">
            {#if datasetList.length === 0}
                <div class="no-data-message">No Data for Given Filters</div>
            {:else}
                <form
                    id="datasets-filter"
                    class="datasets-list"
                    class:expanded={datasetList.length <= SHOW_LIMIT || showAll}
                >
                    {#each visibleDatasets as { datasetKey, datasetTitle, count } (datasetKey)}
                        {@const disabled =
                            datasetTitle ===
                                'iNaturalist Research-grade Observations' &&
                            !filtersContext.includeINat}
                        <div class={['dataset-item', { disabled }]}>
                            <CheckboxInput
                                name="dataset"
                                value={datasetKey}
                                handler={handleDataDataset}
                                checked={filtersContext?.datasets?.includes(
                                    datasetKey
                                ) ?? false}
                            >
                                <div class="dataset-label">
                                    <div class="institution-name-wrapper">
                                        <div
                                            class="institution-name"
                                            title={datasetTitle}
                                        >
                                            {datasetTitle}
                                        </div>
                                    </div>
                                    {#if showCounts && count !== null}
                                        <div
                                            class="institution-count"
                                            class:loading-blink={observationsMetricsLoading}
                                        >
                                            {#if observationsMetricsLoading}
                                                <div
                                                    class="count-loading-icon icon"
                                                >
                                                    <LoadingIcon />
                                                </div>
                                            {:else}
                                                ({count})
                                            {/if}
                                        </div>
                                    {/if}
                                </div>
                            </CheckboxInput>
                        </div>
                    {/each}
                </form>
                {#if datasetList.length > SHOW_LIMIT}
                    <div>
                        <button
                            onclick={() => (showAll = !showAll)}
                            class="button show-datasets-button"
                        >
                            {showAll
                                ? 'Show Less'
                                : `Show ${datasetList.length - SHOW_LIMIT} More`}
                        </button>
                    </div>
                {/if}
            {/if}
        </div>
    </div>
{/if}

<style>
    .count-loading-icon {
        height: 0.8rem;
    }
    .datasets-header-and-icon {
        display: flex;
        gap: 0.5rem;
    }
    .datasets-list {
        width: 100%;
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .datasets-list::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40px;
        background: linear-gradient(transparent, var(--container-highlight));
        pointer-events: none;
        display: block;
    }
    .datasets-list.expanded::after {
        display: none;
    }
    .datasets-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        align-items: center;
    }
    .show-datasets-button {
        border: solid 1px var(--border);
        width: fit-content;
        background-color: var(--container-fore);
    }
    .show-datasets-button:hover {
        background-color: var(--container-mid);
    }
    .show-datasets-button:active {
        background-color: var(--container-back);
    }
    .inat-toggle-wrapper {
        display: flex;
        gap: 0.5rem;
        justify-content: left;
        align-items: center;
    }
    .inat-toggle {
        height: 1.5rem;
        width: 1.5rem;
        stroke: var(--text-default);
    }
    .inat-label {
        text-align: left;
        font-size: 1rem;
    }
    #datasets-header {
        display: flex;
        justify-content: space-between;
        align-content: center;
    }
    .no-data-message {
        text-align: left;
    }
    .dataset-label {
        display: flex;
        justify-content: space-between;
        width: 100%;
        gap: 0.5rem;
        overflow: hidden;
    }
    .institution-name-wrapper {
        display: flex;
        justify-content: space-between;
        flex-grow: 1;
        min-width: 0;
    }
    .institution-name {
        align-self: left;
        min-width: 0;
        text-overflow: ellipsis;
        overflow: hidden;
        font-size: 0.8rem;
    }
    .institution-count {
        flex-shrink: 0;
        font-size: 0.8rem;
    }
    .datasets-section {
        display: flex;
        flex-direction: column;
        min-width: 250px;
        width: 100%;
    }
    .dataset-item.disabled {
        font-style: italic;
        opacity: 0.5;
        pointer-events: none;
    }
</style>
