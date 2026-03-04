<!--
    @component
    - Sidebar component for TexasInverts project
    - For displaying variable information and functionality depending on page
-->

<script lang="ts">
    import NSSection from './NSSection.svelte';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { getSidebarContext } from '../../contexts/sidebarContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import TaxaSearchSuggestBar from '../TaxaSearchSuggestBar.svelte';
    import { countActiveFilters } from '../../lib/filters.svelte';
    import type { SearchSuggestion } from '../../types/api';
    import FiltersButton from '../FiltersButton.svelte';
    import Filters from '../FiltersSection/Filters.svelte';
    import TaxonDisplay from './TaxonDisplay.svelte';
    import {
        getRouterContext,
        type RouterPath,
    } from '../../contexts/routerContext';
    import { getModalContext } from '../../contexts/modalContext';

    type SidebarProps = {
        showTaxonDisplay?: boolean;
        showNSDisplay?: boolean;
    };

    const { showTaxonDisplay = true, showNSDisplay = true }: SidebarProps =
        $props();

    // Load relevant contexts
    const taxonContext = getActiveTaxonContext();
    const sidebarContext = getSidebarContext();
    const filtersContext = getFiltersContext();
    const routerContext = getRouterContext();
    const modalContext = getModalContext();

    // Casting here is a quick fix, but doesn't guard for the future
    // Adding new routes in the future COULD cause issues
    const currPath = $derived(routerContext.url.pathname as RouterPath);

    let filtersCount = $derived<number>(
        countActiveFilters(filtersContext, null, currPath)
    );

    // Keep track of elements
    let filtersElement: HTMLElement | null = $state(null);
    let filtersButtonElement: HTMLElement;

    let filtersOpen = $state<boolean>(false);

    // Sidebar resizing logic
    function handleResize(e: MouseEvent) {
        if (!e.currentTarget) return;

        const origin = e.clientX;
        const originalWidth = sidebarContext.width;

        function resizeWindow(e: MouseEvent) {
            let change = origin - e.clientX;

            // Set new width, with max of 425px and min of 250px
            sidebarContext.width = Math.max(
                Math.min(originalWidth + change, 425),
                250
            );
        }

        function endResize() {
            window.removeEventListener('mouseup', endResize);
            window.removeEventListener('mousemove', resizeWindow);
        }
        window.addEventListener('mouseup', endResize);
        window.addEventListener('mousemove', resizeWindow);
    }

    function clearActiveTaxon() {
        taxonContext.taxonID = null;
    }

    function handleSearchSelect(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;

        taxonContext.taxonID = suggestion.taxonID;
    }

    // Handle click-to-close functionality for filters section
    function handleOutsidePointerDown(e: PointerEvent) {
        if (!filtersOpen) return;

        const target = e.target as Node;
        const portal = document.querySelector('#portal-root');

        // Don't react if click is on the filters element, button, or portal in general
        if (
            filtersElement?.contains(target) ||
            filtersButtonElement?.contains(target) ||
            portal?.contains(target)
        )
            return;

        filtersOpen = false;
    }

    function handleFiltersButton(e: MouseEvent) {
        e.stopPropagation();
        filtersOpen = !filtersOpen;
    }

    // Register click-to-close functionality for filters section
    $effect(() => {
        if (filtersOpen) {
            document.addEventListener(
                'pointerdown',
                handleOutsidePointerDown,
                true // capture
            );
        }

        return () => {
            document.removeEventListener(
                'pointerdown',
                handleOutsidePointerDown,
                true
            );
        };
    });
</script>

<div
    id="sidebar-wrapper"
    class="space-between"
    style:width={`${sidebarContext.width}px`}
>
    {#if filtersOpen}
        <div id="filters-section-wrapper" bind:this={filtersElement}>
            <Filters bind:filtersOpen />
        </div>
    {/if}
    <div id="sidebar">
        <button
            aria-label="resize containers"
            class="resize-bar"
            onmousedown={handleResize}
        ></button>
        <div id="sidebar-content-wrapper">
            <div id="search-and-filter-section">
                <div
                    id="filters-button-wrapper"
                    bind:this={filtersButtonElement}
                >
                    <FiltersButton
                        count={filtersCount}
                        open={filtersOpen}
                        handler={handleFiltersButton}
                    />
                </div>
                <TaxaSearchSuggestBar
                    placeholder={'Search by taxon...'}
                    currentSelection={taxonContext.taxonInfo.canonicalName}
                    handleClear={clearActiveTaxon}
                    handleSelect={handleSearchSelect}
                />
            </div>
            {#if taxonContext.taxonID}
                <div id="sidebar-content">
                    {#if showTaxonDisplay}
                        <TaxonDisplay />
                        {#if taxonContext.taxonID && showNSDisplay}
                            <NSSection />
                        {/if}
                    {/if}
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    #filters-button-wrapper {
        height: 100%;
    }
    :global(#search-and-filter-section > .search-wrapper) {
        background-color: var(--container-fore);
    }
    #filters-section-wrapper {
        position: absolute;
        top: 0;
        right: calc(100% - 0.5rem);
        z-index: 1;
        pointer-events: all;
        box-shadow: -4px 6px 12px rgba(0, 0, 0, 0.175);
        border-top-left-radius: 3px;
        border-bottom-left-radius: 3px;
    }
    #search-and-filter-section {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--container-back);
        gap: 0.5rem;
        z-index: 100;
        height: 2.5rem;
    }
    :global(.date-range-filter) {
        margin: auto;
    }
    .resize-bar {
        height: 100%;
        flex-shrink: 0;
        width: 1rem;
        padding: 0;
        cursor: ew-resize;
        transition: all 0.1s ease-in-out;
        border: none;
        position: absolute;
        left: -0.5rem;
        top: 0;
        z-index: 750;
        pointer-events: all;
        box-sizing: border-box;
        background-color: unset;
    }
    .resize-bar:active {
        cursor: grabbing;
    }
    .resize-bar:focus {
        outline: none;
    }
    :global(.iNat-toggle-wrapper svg) {
        stroke: var(--text-default);
    }
    :global(.inat-toggle-button svg) {
        fill: var(--text-default);
        stroke: var(--text-default);
    }
    :global(.space-between) {
        display: flex;
        justify-content: space-between;
    }
    :global(.sidebar-header) {
        line-height: 1.5rem;
        /* margin-bottom: 0.1rem; */
        padding: 0.75rem;
        display: flex;
        justify-content: space-between;
        font-size: 1.2rem;
    }
    #sidebar-wrapper {
        user-select: none;
        /* Prevent absorbing clicks on wrapper if contents are short */
        pointer-events: none;
        position: relative;
        top: 0;
        grid-column: 2;
        grid-row: 1 / 4;
        width: 100%;
        height: 100%;
        flex-shrink: 0;
        z-index: 2;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        color: var(--text-default);
        hyphens: manual;
    }
    #sidebar {
        position: relative;
        display: flex;
        pointer-events: auto;
        flex-direction: column;
        color: var(--text-default);
        background-color: var(--container-back);
        padding: 0.5rem;
        border-radius: 3px;
        display: flex;
        flex-direction: column;
        max-height: 100%;
        box-shadow: -4px 6px 12px rgba(0, 0, 0, 0.175);
        border: 1px solid var(--border);
        box-sizing: border-box;
    }
    #sidebar-content-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
        gap: 0.5rem;
    }
    #sidebar-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        overflow-y: auto;
    }
</style>
