<script lang="ts">
    import type { Snippet } from 'svelte';
    import {
        FILTER_KEYS,
        getActiveFilterKeys,
        OCCURRENCE_FILTER_KEYS,
        SIDEBAR_FILTER_META,
        TAXA_FILTER_KEYS,
        type FiltersDomain,
    } from '../../constants/sidebarFilters';
    import {
        getFiltersContext,
        type FiltersState,
    } from '../../contexts/filtersContext';
    import { getModalContext } from '../../contexts/modalContext';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { capitalizeWords } from '../../util/textHelpers';
    import { countActiveFilters } from '../../lib/filters.svelte';

    type FiltersWrapperProps = {
        header: string;
        domain: FiltersDomain;
        children: Snippet;
        includeButtons?: boolean;
    };

    const {
        header,
        domain,
        children,
        includeButtons = true,
    }: FiltersWrapperProps = $props();

    const modalContext = getModalContext();
    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();

    function handleApplyFilters() {
        modalContext.visible = false;
    }

    function handleClearFilters() {
        for (const filterKey of FILTER_KEYS as (keyof FiltersState)[]) {
            const meta = SIDEBAR_FILTER_META[filterKey];
            // @ts-expect-error: type mismatch on default values
            filtersContext[filterKey] =
                meta.default as FiltersState[typeof filterKey];
        }
        taxaContext.taxa.clear();
    }

    const activeFilterCount: number = $derived(
        countActiveFilters(filtersContext, domain)
    );

    const formattedActiveFilters: string[] = $derived(
        getActiveFilterKeys(
            domain == 'taxon' ? TAXA_FILTER_KEYS : OCCURRENCE_FILTER_KEYS,
            filtersContext
        )
            .map((key) => {
                return SIDEBAR_FILTER_META[key].format(filtersContext[key]);
            })
            .filter((value) => value !== null)
    );
</script>

<div class="filters-content-wrapper">
    <div class="header-and-subheader">
        <h3 class="filters-header">{header}</h3>
        <div
            class="active-filters-text thin"
            class:active={formattedActiveFilters?.length}
        >
            {#if activeFilterCount === 0}
                <span>No Active Filters</span>
            {:else if activeFilterCount < 5}
                <span
                    >Active {capitalizeWords(domain)} Filters: {formattedActiveFilters.join(
                        ', '
                    )}</span
                >
            {:else}
                <span
                    >{activeFilterCount} Active {capitalizeWords(domain)} Filters</span
                >
            {/if}
        </div>
    </div>
    <div id="filters-content">
        {@render children?.()}
    </div>
    {#if includeButtons}
        <div class="apply-filters-section">
            <div class="filters-buttons-wrapper">
                <button
                    class="clear-filters-button button"
                    onclick={handleClearFilters}>Clear All</button
                >
                <button
                    class="apply-filters-button button"
                    onclick={handleApplyFilters}>Apply Filters</button
                >
            </div>
        </div>
    {/if}
</div>

<style>
    .header-and-subheader {
        margin: 0.5rem 0.5rem 0 0.5rem;
        gap: 0.5rem;
        vertical-align: baseline;
    }
    .active-filters-text {
        display: flex;
        width: 100%;
        font-size: 0.9rem;
        font-style: italic;
        text-align: left;
    }
    .active-filters-text.active {
        color: var(--accent-color);
    }
    .filters-header {
        margin: 0;
        display: flex;
        user-select: none;
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
    }
    #filters-content {
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
