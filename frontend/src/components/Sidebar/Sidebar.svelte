<!--
    @component
    - Sidebar component for TexasInverts project
    - For displaying variable information and functionality depending on page
-->

<script lang="ts">
    import NSSection from './NSSection.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
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
    import AddTaxonButton from './AddTaxonButton.svelte';
    // import DownloadOccurrenceForm from '../DownloadOccurrenceForm.svelte';
    // import DownloadIcon from '../../assets/DownloadIcon.svelte';

    type SidebarProps = {
        showTaxonDisplay?: boolean;
        showNSDisplay?: boolean;
    };

    const { showTaxonDisplay = true, showNSDisplay = true }: SidebarProps =
        $props();

    // Load relevant contexts
    const taxaContext = getActiveTaxaContext();
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

    function removeTaxon(taxonID: number) {
        taxaContext.remove(taxonID);
    }
    function handleSearchSelect(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;

        taxaContext.add(suggestion.taxonID);
    }

    // Handle click-to-close functionality for filters section
    function handleOutsidePointerDown(e: PointerEvent) {
        if (!filtersOpen) return;

        const target = e.target as Node;
        const portal = document.querySelector('#portal-root');

        // Container from AirDatepicker, used in date filter
        const datepickerContainer = document.querySelector(
            '.air-datepicker-global-container'
        );

        // Don't react if click is on the filters element, button, or portal in general
        if (
            filtersElement?.contains(target) ||
            filtersButtonElement?.contains(target) ||
            portal?.contains(target) ||
            datepickerContainer?.contains(target)
        )
            return;

        filtersOpen = false;
    }

    function handleFiltersButton() {
        modalContext.content = Filters;
        modalContext.visible = true;
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

    // function handleOccDownloadButton() {
    //     modalContext.visible = true;
    //     modalContext.content = DownloadOccurrenceForm;
    // }
</script>

<div
    id="sidebar-wrapper"
    class="space-between"
    style:width={`${sidebarContext.width}px`}
>
    {#if filtersOpen}
        <div id="filters-section-wrapper" bind:this={filtersElement}>
            <Filters />
        </div>
    {/if}
    <div id="filters-coverup"></div>
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
                    handleClear={removeTaxon}
                    handleSelect={handleSearchSelect}
                />
                <!-- <button
                    class="download-button button"
                    onclick={handleOccDownloadButton}
                >
                    <DownloadIcon />
                </button> -->
            </div>
            {#if Object.keys(taxaContext.taxa).length}
                <div id="sidebar-content" class="sidebar-section">
                    {#each Object.keys(taxaContext.taxa).map(Number) as taxonID}
                        <div id={`${taxonID}-sidebar-section`}>
                            <TaxonDisplay {taxonID} />
                            {#if taxonID && showNSDisplay}
                                <div class="sidebar-body-wrapper">
                                    <div
                                        class="sidebar-body-overlay"
                                        style:background-color={taxaContext
                                            .taxa[taxonID].color}
                                    ></div>
                                    <NSSection {taxonID} />
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
            {#if !!taxaContext.taxonIDs.length}
                <div class="sidebar-endcap">
                    <AddTaxonButton />
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    /* .download-button {
        box-sizing: border-box;
        height: 100%;
        width: 3rem;
        padding: 0;
        display: flex;
        justify-content: center;
        border: 1px solid var(--border);
        box-sizing: border-box;
    } */
    .sidebar-endcap {
        display: flex;
        gap: 0.5rem;
        height: 2.5rem;
    }
    .sidebar-body-wrapper {
        position: relative;
    }
    .sidebar-body-overlay {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 100%;
        opacity: 0.05;
        pointer-events: none;
    }
    :global(.sidebar-section) {
        border-radius: 3px;
    }
    #filters-coverup {
        position: absolute;
        height: 100%;
        left: -0.5rem;
        top: 0;
        width: 0.5rem;
        z-index: 5;
        background-color: var(--container-back);
        border-radius: 3px;
    }
    #filters-button-wrapper {
        height: 100%;
    }
    :global(#search-and-filter-section > .search-wrapper) {
        background-color: var(--container-fore);
    }
    #filters-section-wrapper {
        position: absolute;
        top: -0.5rem;
        right: calc(100%);
        z-index: 1;
        pointer-events: all;
        border-top-left-radius: 3px;
        border-bottom-left-radius: 3px;
        /* box-shadow: -4px 3px 4px 0px var(--container-shadow); */
    }
    #search-and-filter-section {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--container-back);
        gap: 0.5rem;
        z-index: 100;
        height: 2.5rem;
        flex-shrink: 0;
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
        left: -1rem;
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
        /* max-height: 100%; */
        flex-shrink: 0;
        z-index: 2;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        color: var(--text-default);
        hyphens: manual;
        border-radius: 3px;
        box-sizing: border-box;
    }
    #sidebar {
        position: relative;
        display: flex;
        pointer-events: auto;
        flex-direction: column;
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        height: 100%;
        box-sizing: border-box;
        border-radius: 3px;
        gap: 0.5rem;
    }
    #sidebar-content-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
        gap: 0.5rem;
        box-sizing: border-box;
    }
    #sidebar-content {
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        overflow-y: auto;
        flex-shrink: 1;
        min-height: 0;
        gap: 0.5rem;
    }
</style>
