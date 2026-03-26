<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import CheckboxInput, {
        type CheckboxPayload,
    } from '../../common/CheckboxInput.svelte';
    import type { Provider } from '../../constants/mapLegendKeys';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { dataProviders } from '../../contexts/DataProviders';
    import { getFiltersContext } from '../../contexts/filtersContext';

    type DatasetFilterProps = {
        header?: string;
        showCounts?: boolean;
    };

    const { header = 'Datasets', showCounts = true }: DatasetFilterProps =
        $props();

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxaContext();

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

    // Determine if observationsMetrics are loading for any taxa
    const observationsMetricsLoading = $derived(
        Object.values(taxonContext.taxa).some(
            (taxon) => taxon.observationMetricsLoading
        )
    );

    // Determine providerCounts added across all taxa
    let providerCounts = $derived(
        Object.values(taxonContext.taxa).reduce(
            (acc, taxon) => {
                if (!taxon.providerCounts) return acc;
                for (const [provider, count] of Object.entries(
                    taxon.providerCounts
                )) {
                    acc[provider] = (acc[provider] ?? 0) + count;
                }
                return acc;
            },
            {} as Record<string, number>
        )
    );
</script>

{#if $dataProviders}
    <div
        class="data-providers-section filters-section"
        class:active={!!filtersContext.dataProviders?.length}
        class:loading-blink={observationsMetricsLoading}
    >
        {#if observationsMetricsLoading}
            <div class="loading-icon icon">
                <LoadingIcon />
            </div>
        {/if}
        <div class="filters-section-header">{header}</div>
        <div class="filters-section-content">
            {#if !!providerCounts.length}
                <form id="datasets-filter">
                    {#each Object.entries(providerCounts) as [institutionCode, count] (institutionCode)}
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
                                    <div class="institution-name-wrapper">
                                        <div
                                            class="institution-name"
                                            title={institutionName ||
                                                institutionCode}
                                        >
                                            {institutionName || institutionCode}
                                        </div>
                                        <div class="institution-code">
                                            {institutionCode}
                                        </div>
                                    </div>
                                    {#if showCounts}
                                        <div class="institution-count">
                                            ({count})
                                        </div>
                                    {/if}
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
        width: 100%;
        gap: 0.5rem;
        overflow: hidden;
    }
    .institution-name-wrapper {
        display: flex;
        justify-content: space-between;
        /* width: 100%; */
        flex-grow: 1;
        min-width: 0;
    }
    .institution-name {
        align-self: left;
        white-space: nowrap;
        min-width: 0;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .institution-count {
        flex-shrink: 0;
    }
    .institution-code {
        /* font-style: italic; */
        font-weight: 200;
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
