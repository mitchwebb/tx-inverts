<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import {
        FILTER_KEYS,
        SIDEBAR_FILTER_META,
    } from '../../constants/sidebarFilters';
    import {
        getFiltersContext,
        type FiltersStateType,
    } from '../../contexts/filtersContext';
    import { getRouterContext } from '../../contexts/routerContext';
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import INatFilterSection from './INatFilterSection.svelte';
    import RankFilterSection from './RankFilterSection.svelte';
    import TaxonFilterSection from './TaxonFilterSection.svelte';
    import './filtersSection.css';

    const filtersContext = getFiltersContext();
    const routerContext = getRouterContext();

    // Determine if we're on the map page (in order to include/exclude page-specific sections)
    const pageID = $derived(routerContext.url.pathname);

    // Bindable allows this component to close itself in a parent
    let { filtersOpen = $bindable() } = $props();

    function handleApplyFilters() {
        filtersOpen = false;
    }

    // This is fairly safe within SIDEBAR_FILTER_META, but ts doesn't like the union
    // Still, I don't like manually ignoring the error.
    function handleClearFilters() {
        for (const filterKey of FILTER_KEYS as (keyof FiltersStateType)[]) {
            const meta = SIDEBAR_FILTER_META[filterKey];
            // @ts-expect-error: type mismatch on default values
            filtersContext[filterKey] =
                meta.default as FiltersStateType[typeof filterKey];
        }
    }
</script>

<div class="filters-content-wrapper">
    <div id="filters-content">
        <INatFilterSection />
        {#if pageID === '/map'}
            <DatasetFilterSection />
            <DateFilterSection />
        {/if}
        {#if pageID === '/rankings'}
            <TaxonFilterSection />
            <RankFilterSection />
        {/if}
    </div>
    <div class="apply-filters-section">
        <div class="filters-buttons-wrapper">
            <button
                class="clear-filters-button button"
                onclick={handleClearFilters}>Clear Filters</button
            >
            <button
                class="apply-filters-button button"
                onclick={handleApplyFilters}>Apply Filters</button
            >
        </div>
    </div>
</div>
<div id="border-coverup"></div>

<style>
    #border-coverup {
        height: 1px;
        width: 0.5rem;
        position: absolute;
        right: 0;
        top: calc(100% - 1px);
        z-index: 10000;
        background-color: var(--container-back);
    }
    .filters-content-wrapper {
        overflow-y: auto;
        width: 100%;
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        padding: 0.5rem;
        gap: 0.5rem;
        background-color: var(--container-back);
        border-top: 1px solid var(--border);
        border-left: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        position: relative;
        border-top-left-radius: 3px;
        border-bottom-left-radius: 3px;
        /* max-width: 500px; */
        min-width: 300px;
        max-height: 475px;
    }
    #filters-content {
        display: flex;
        flex-direction: column;
        overflow-y: auto;
        box-sizing: border-box;
        gap: 0.5rem;
        width: 100%;
    }
    .filters-buttons-wrapper {
        display: flex;
        gap: 0.5rem;
        justify-content: right;
        white-space: nowrap;
    }
    .clear-filters-button {
        border: 1px solid var(--border);
        background-color: rgb(139, 0, 0);
    }
    .clear-filters-button:hover {
        background-color: rgb(129, 0, 0);
    }
    .clear-filters-button:active {
        background-color: rgb(119, 0, 0);
    }
    .apply-filters-button {
        border: 1px solid var(--border);
    }
    .apply-filters-button:not(:hover) {
        background-color: var(--container-highlight);
    }
</style>
