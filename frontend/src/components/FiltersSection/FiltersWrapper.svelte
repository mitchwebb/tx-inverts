<script lang="ts">
    import type { Snippet } from 'svelte';
    import {
        FILTER_KEYS,
        SIDEBAR_FILTER_META,
    } from '../../constants/sidebarFilters';
    import {
        getFiltersContext,
        type FiltersState,
    } from '../../contexts/filtersContext';
    import { getModalContext } from '../../contexts/modalContext';

    type FiltersWrapperProps = {
        header: string;
        children: Snippet;
    };

    const { header, children }: FiltersWrapperProps = $props();

    const modalContext = getModalContext();
    const filtersContext = getFiltersContext();

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
    <div class="filters-header header">{header}</div>
    <div id="filters-content">
        {@render children?.()}
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
    .filters-header {
        margin: 0.5rem;
        display: flex;
        justify-content: center;
    }
    .filters-content-wrapper {
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        gap: 0.5rem;
        background-color: var(--container-back);
        min-width: 200px;
        width: fit-content;
        max-width: 800px;
        max-height: 80dvh;
    }
    #filters-content {
        overflow-y: auto;
        flex: 1;
        min-height: 0;
        display: flex;
        gap: 0.5rem;
        height: 100%;
        flex-wrap: wrap;
        align-items: stretch;
    }
    .filters-buttons-wrapper {
        display: flex;
        gap: 0.5rem;
        justify-content: right;
        white-space: nowrap;
        flex-shrink: 0;
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
