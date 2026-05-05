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
    import { countActiveFilters } from '../../lib/filters.svelte';
    import FiltersButton from '../FiltersButton.svelte';
    import TaxonDisplay from './TaxonDisplay.svelte';
    import {
        getRouterContext,
        type RouterPath,
    } from '../../contexts/routerContext';
    import { getModalContext } from '../../contexts/modalContext';
    import AddTaxonButton from './AddTaxonButton.svelte';
    import TaxaSearch from '../TaxaSearch.svelte';
    import ObservationsFilters from '../FiltersSection/ObservationsFilters.svelte';
    import TaxaFilters from '../FiltersSection/TaxaFilters.svelte';
    import { openModal } from '../../lib/modal.svelte';
    import DownloadOccurrenceForm from '../DownloadOccurrenceForm.svelte';
    import DownloadIcon from '../../assets/DownloadIcon.svelte';

    type SidebarProps = {
        showNSDisplay?: boolean;
    };

    const { showNSDisplay = true }: SidebarProps = $props();

    // Load relevant contexts
    const taxaContext = getActiveTaxaContext();
    const sidebarContext = getSidebarContext();
    const filtersContext = getFiltersContext();
    const routerContext = getRouterContext();
    const modalContext = getModalContext();

    // Casting here is a quick fix, but doesn't guard for the future
    // Adding new routes in the future COULD cause issues
    const currPath = $derived(routerContext.url.pathname as RouterPath);

    // Determine which filters menu to open from sidebar
    const filtersDomain = $derived.by(() => {
        if (['/map', '/backbone'].includes(currPath)) {
            return 'observations';
        } else {
            return 'taxa';
        }
    });

    let filtersCount = $derived<number>(
        countActiveFilters(filtersContext, filtersDomain)
    );

    // Keep track of elements
    let filtersElement: HTMLElement | null = $state(null);

    let filtersOpen = $state<boolean>(false);

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
            portal?.contains(target) ||
            datepickerContainer?.contains(target)
        )
            return;

        filtersOpen = false;
    }

    function handleFiltersButton() {
        openModal(modalContext, filters);
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
    //     modalContext.content = occurrenceDownloadForm;
    // }
</script>

<!-- {#snippet occurrenceDownloadForm()}
    <DownloadOccurrenceForm />
{/snippet} -->

{#snippet filters()}
    {#if filtersDomain === 'observations'}
        <ObservationsFilters />
    {:else if filtersDomain === 'taxa'}
        <TaxaFilters />
    {/if}
{/snippet}

<div id="sidebar-wrapper" class="space-between">
    <div id="sidebar">
        <div id="sidebar-content-wrapper" class:open={sidebarContext.open}>
            <div id="search-and-filter-section">
                <div id="filters-button-wrapper">
                    <FiltersButton
                        count={filtersCount}
                        open={filtersOpen}
                        handler={handleFiltersButton}
                    />
                </div>
                <div class="sidebar-search-wrapper">
                    <TaxaSearch
                        replace={true}
                        placeholder={'Search by taxon...'}
                    />
                </div>
                <!-- <button
                    class="download-button button"
                    onclick={handleOccDownloadButton}
                >
                    <DownloadIcon />
                </button> -->
            </div>
            {#if taxaContext.taxa.items.length && sidebarContext.open}
                <div id="sidebar-content" class="sidebar-section">
                    {#each taxaContext.taxa.ids as taxonID}
                        <div id={`${taxonID}-sidebar-section`}>
                            {#if taxaContext.taxa.get(taxonID)}
                                <TaxonDisplay {taxonID} />
                            {/if}
                            {#if taxonID && showNSDisplay}
                                <div class="sidebar-body-wrapper">
                                    <div
                                        class="sidebar-body-overlay"
                                        style:background-color={taxaContext.taxa.get(
                                            taxonID
                                        )?.color}
                                    ></div>
                                    <NSSection {taxonID} />
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
            {#if taxaContext.taxa.ids.length}
                <div class="sidebar-endcap">
                    <AddTaxonButton />
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    .sidebar-search-wrapper {
        height: 100%;
        width: 100%;
    }
    #sidebar-foldout-icon {
        padding: 0;
        margin: 0;
    }
    #sidebar-foldout-button {
        height: 100%;
        border: 1px solid var(--border);
    }

    #sidebar-content-wrapper {
        height: 100%;
        /* gap: 0.5rem; */
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }
    #sidebar-content {
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
        overflow-y: auto;
        flex-shrink: 1;
        min-height: 0;
        gap: 0.5rem;
        grid-row: 2;
        margin-top: 0.5rem;
    }
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
        grid-row: 3;
        margin-top: 0.5rem;
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
        opacity: 0.1;
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
        width: 100px;
        flex-shrink: 0;
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
    }
    #search-and-filter-section {
        grid-row: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        /* background-color: var(--container-back); */
        gap: 0.5rem;
        z-index: 100;
        height: 2.5rem;
        flex-shrink: 0;
    }
    :global(.date-range-filter) {
        margin: auto;
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
        padding: 0.5rem;
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
        border-radius: 3px;
        box-sizing: border-box;
        height: 100%;
    }
    #sidebar {
        position: relative;
        pointer-events: auto;
        flex-direction: column;
        color: var(--text-default);
        flex-direction: column;
        height: 100%;
        box-sizing: border-box;
        border-radius: 3px;
        gap: 0.5rem;
    }
</style>
