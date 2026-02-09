<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import CheckboxInput, {
        type CheckboxPayload,
    } from '../../common/CheckboxInput.svelte';
    import type { Provider } from '../../constants/mapLegendKeys';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { dataProviders } from '../../contexts/DataProviders';
    import { getFiltersContext } from '../../contexts/filtersContext';

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxonContext();

    function handleDataProvider({ value, checked }: CheckboxPayload) {
        // Get list of currently selected providers
        let currProviders = filtersContext.dataProviders ?? [];

        if (checked) {
            // Add only if not already present
            if (!currProviders.includes(value as Provider)) {
                currProviders = [...currProviders, value as Provider];
            }
        } else {
            // Remove if present
            currProviders = currProviders.filter((p) => p !== value);
        }

        // Update reactive state
        filtersContext.dataProviders = currProviders;
    }
</script>

{#if $dataProviders}
    <div
        class="data-providers-section filters-section"
        class:active={!!filtersContext.dataProviders?.length}
        class:loading-blink={taxonContext.observationMetricsLoading}
    >
        {#if taxonContext.observationMetricsLoading}
            <div class="loading-icon icon">
                <LoadingIcon />
            </div>
        {/if}
        <div class="filters-section-header">Datasets</div>
        <div class="filters-section-content">
            {#if taxonContext.providerCounts}
                <form id="datasets-filter">
                    {#each Object.entries(taxonContext.providerCounts) as [institutionCode, count] (institutionCode)}
                        {@const institutionName =
                            $dataProviders?.[institutionCode]?.[
                                'institutionName'
                            ]}
                        {@const disabled =
                            institutionName === 'iNaturalist.org' &&
                            !filtersContext.includeINat}
                        <div class={['provider-item', { disabled }]}>
                            <CheckboxInput
                                name="provider"
                                value={institutionCode}
                                handler={handleDataProvider}
                                checked={filtersContext?.dataProviders?.includes(
                                    institutionCode as Provider
                                ) ?? false}
                            >
                                <div class="provider-label">
                                    <div
                                        class="institution-name"
                                        title={institutionName ||
                                            institutionCode}
                                    >
                                        {institutionName || institutionCode}
                                    </div>
                                    <div class="institution-count">
                                        ({count})
                                    </div>
                                </div>
                            </CheckboxInput>
                        </div>
                    {/each}
                </form>
            {:else}
                <div class="no-data-message">No Data</div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .no-data-message {
        text-align: left;
    }
    .loading-icon {
        position: absolute;
        right: 1rem;
    }
    .provider-label {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        overflow: hidden;
    }
    .institution-name {
        align-self: left;
        white-space: nowrap;
        min-width: 0;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .data-providers-section {
        display: flex;
        flex-direction: column;
    }
    .provider-item.disabled {
        font-style: italic;
        opacity: 0.5;
        pointer-events: none;
    }
</style>
