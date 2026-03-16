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
        type FiltersState,
    } from '../../contexts/filtersContext';
    import { getModalContext } from '../../contexts/modalContext';
    import { getRouterContext } from '../../contexts/routerContext';
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import INatFilterSection from './INatFilterSection.svelte';
    import RankFilterSection from './RankFilterSection.svelte';
    import TaxonFilterSection from './TaxonFilterSection.svelte';
    import './filtersSection.css';

    const filtersContext = getFiltersContext();
    const routerContext = getRouterContext();
    const modalContext = getModalContext();

    // Determine if we're on the map page (in order to include/exclude page-specific sections)
    const pageID = $derived(routerContext.url.pathname);

    // Bindable allows this component to close itself in a parent
    // let { filtersOpen = $bindable() } = $props();

    function handleApplyFilters() {
        // filtersOpen = false;
        modalContext.visible = false;
        // modalContext.content = null;
    }

    // This is fairly safe within SIDEBAR_FILTER_META, but ts doesn't like the union
    // Still, I don't like manually ignoring the error.
    function handleClearFilters() {
        for (const filterKey of FILTER_KEYS as (keyof FiltersState)[]) {
            const meta = SIDEBAR_FILTER_META[filterKey];
            // @ts-expect-error: type mismatch on default values
            filtersContext[filterKey] =
                meta.default as FiltersState[typeof filterKey];
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

<style>
    .filters-content-wrapper {
        width: 100%;
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        /* padding: 0.5rem; */
        gap: 0.5rem;
        background-color: var(--container-back);
        width: 500px;
        max-width: 100%;
        max-height: 475px;
        box-sizing: border-box;
    }
    #filters-content {
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        gap: 0.5rem;
        width: 100%;
        overflow: auto;
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
