<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import Toggle from '../../common/Toggle.svelte';
    import type { Provider } from '../../constants/mapLegendKeys';
    import type { FilterDomain } from '../../constants/sidebarFilters';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { dataProviders } from '../../contexts/DataProviders';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import { toggleArrayValue } from '../../util/toggleArrayValue';

    type DatasetFilterProps = {
        header?: string;
        domain?: FilterDomain;
        showCounts?: boolean;
    };

    const {
        header = 'Datasets',
        showCounts = true,
        domain = 'observations',
    }: DatasetFilterProps = $props();

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxaContext();

    const iNatActive = $derived(filtersContext.includeINat);

    // Derive a unified list of providers
    const providerList = $derived.by(() => {
        if (!$dataProviders) return [];
        // If in observations domain and taxa selected,
        // OR if in taxa domain and parent taxa selected
        if (
            (domain === 'observations' && taxonContext.taxa.ids.length) ||
            (domain === 'taxa' && filtersContext.filterTaxonIDs.length)
        ) {
            // Filter to relevant providers
            return Object.entries(providerCounts).map(([code, count]) => ({
                institutionCode: code,
                institutionName: $dataProviders?.[code]?.institutionName,
                count,
            }));
        } else {
            // Else, show all providers
            return Object.entries($dataProviders).map(([code, info]) => ({
                institutionCode: code,
                institutionName: info.institutionName,
                count: null,
            }));
        }
    });

    // Track show/hide state of list
    let showAll = $state(false);
    // Number of providers to show by default
    const SHOW_LIMIT = 5;

    // List of providers visible (given show/hide state)
    const visibleProviders = $derived(
        showAll ? providerList : providerList.slice(0, SHOW_LIMIT)
    );

    function handleDataProvider({ value, checked }: CheckboxPayload) {
        // Get list of currently selected providers
        let currProviders = filtersContext.dataProviders ?? [];

        // Update reactive state
        filtersContext.dataProviders = toggleArrayValue<Provider>(
            currProviders,
            value as Provider,
            checked
        );
    }

    // Determine if observationsMetrics are loading for any taxa
    const observationsMetricsLoading = $derived(
        Object.values(taxonContext.taxa.items).some(
            (taxon) => taxon.observationMetricsLoading
        )
    );

    // Determine providerCounts added across all taxa
    let providerCounts = $derived(
        Object.values(taxonContext.taxa.items).reduce(
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

    function handleINatToggle(checked: boolean) {
        filtersContext.includeINat = checked;
    }
</script>

{#if $dataProviders}
    <div
        class="data-providers-section filters-section"
        class:active={!!filtersContext.dataProviders?.length ||
            !filtersContext.includeINat}
        class:loading-blink={observationsMetricsLoading}
    >
        <div id="data-providers-header" class="filters-section-header">
            {#if observationsMetricsLoading}
                <div class="loading-icon icon">
                    <LoadingIcon />
                </div>
            {:else}
                <span>{header}</span>
            {/if}
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
        <div class="filters-section-content providers-content">
            {#if providerList.length === 0}
                <div class="no-data-message">No Data for Given Filters</div>
            {:else}
                <form
                    id="datasets-filter"
                    class="providers-list"
                    class:expanded={providerList.length <= SHOW_LIMIT ||
                        showAll}
                >
                    {#each visibleProviders as { institutionCode, institutionName, count } (institutionCode)}
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
                                    {#if showCounts && count !== null}
                                        <div class="institution-count">
                                            ({count})
                                        </div>
                                    {/if}
                                </div>
                            </CheckboxInput>
                        </div>
                    {/each}
                    <!-- {#if providerList.length > SHOW_LIMIT && !showAll}
                        <div class='blank-provider-item'>
                            <div class="provider-label">
                                <div class="institution-name-wrapper">
                                    <div class="institution-name">...</div>
                                    <div class="institution-code"></div>
                                </div>
                            </div>
                        </div>
                    {/if} -->
                </form>
                {#if providerList.length > SHOW_LIMIT}
                    <div>
                        <button
                            onclick={() => (showAll = !showAll)}
                            class="button show-providers-button"
                        >
                            {showAll
                                ? 'Show Less'
                                : `Show ${providerList.length - SHOW_LIMIT} More`}
                        </button>
                    </div>
                {/if}
            {/if}
        </div>
    </div>
{/if}

<style>
    .providers-list {
        width: 100%;
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .providers-list::after {
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
    .providers-list.expanded::after {
        display: none;
    }
    .providers-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        align-items: center;
    }
    .show-providers-button {
        border: solid 1px var(--border);
        width: fit-content;
        background-color: var(--container-fore);
    }
    .show-providers-button:hover {
        background-color: var(--container-mid);
    }
    .show-providers-button:active {
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
        /* white-space: nowrap; */
        font-size: 1rem;
    }
    #data-providers-header {
        display: flex;
        justify-content: space-between;
    }
    .no-data-message {
        text-align: left;
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
        /* white-space: nowrap; */
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
        min-width: 250px;
        width: 100%;
    }
    .provider-item.disabled {
        font-style: italic;
        opacity: 0.5;
        pointer-events: none;
    }
</style>
