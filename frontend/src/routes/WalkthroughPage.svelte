<script lang="ts">
    import type { Snippet } from 'svelte';
    import { getModalContext } from '../contexts/modalContext';
    import { getRouterContext } from '../contexts/routerContext';
    import { openModal } from '../lib/modal.svelte';
    import RangeExtentModal from '../common/Modals/RangeExtentModal.svelte';
    import TaxaSearch from '../components/TaxaSearch.svelte';
    import Sidebar from '../components/Sidebar/Sidebar.svelte';
    import MagnifyIcon from '../assets/MagnifyIcon.svelte';
    import { DUMMY_TAXON } from '../constants/taxa';

    const modalContext = getModalContext();
    const routerContext = getRouterContext();

    function showModal(snippet: Snippet) {
        openModal(modalContext, snippet);
    }

    function handlePageLink(e: Event) {
        // Prevent full reloading (normal navigation)
        e.preventDefault();

        const target = e.currentTarget as HTMLAnchorElement;
        const pathname = target.getAttribute('href');

        if (!pathname) return;

        // Navigate to page (ignoring same-page clicks)
        if (pathname !== window.location.pathname) {
            routerContext.navigate(pathname, true);
        }
    }
</script>

{#snippet rangeExtentModal()}
    <RangeExtentModal />
{/snippet}

<div id="about-page-wrapper">
    <h1 id="about-header">Texas Inverts Walkthrough</h1>
    <div class="about-page-body">
        <div class="about-page-section">
            <h3 class="about-page-subheader">General</h3>
            <p>
                The first thing you might notice is the
                <span class="taxa-search-example">
                    <TaxaSearch />
                </span>
                bar at the top of each page. Use this search bar to search for Texas
                invertebrates by scientific name! Selecting a species while on this
                walkthrough page will take you to the
                <a href="#map-page-section">map page</a> with your species selected.
            </p>
            <p>
                Selected species will show up in the sidebar, where you'll find
                analysis corresponding to each of your selected taxa, as well as
                various filters to alter the data being considered.
            </p>
            <p>The sidebar looks like this:</p>
            <div id="about-sidebar-positioner">
                <div id="about-sidebar">
                    <Sidebar activeTaxa={[DUMMY_TAXON]} demo={true} />
                </div>
            </div>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">
                <a id="map-page-section" class="page-anchor">Map Page</a>
            </h3>
            <p>
                The map page allows you to view observation data for your
                selected species. Each species selected in the sidebar will show
                up as a different color on the map, matched to their color in
                the sidebar. The individual points of data are surrounded by a
                larger, filled-in polygon of the same color: a visualization of
                that species'
                <button
                    onclick={() => showModal(rangeExtentModal)}
                    id="datasets-modal-button"
                    class="modal-button"
                >
                    range extent
                </button>.
            </p>
            <p>
                When zoomed out, observations points are grouped into squares as
                a heatmap. If you zoom in far enough, the groupings resolve to
                individual points—by clicking on these points, you'll find more
                information about each observation, as well as a link to their
                original GBIF record.
            </p>
            <p>
                You can also apply multiple layers to the map—counties, parks,
                and ecoregions—for additional insight.
            </p>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">
                <a id="backbone-page-section" class="page-anchor"
                    >Backbone Page</a
                >
            </h3>
            <p>
                The backbone page allows you to browse through the taxonomic
                structure used by Texas Inverts. This is GBIF's taxonomic
                backbone, pared down to species with observation data in Texas.
                You can also use this page to select species in the sidebar by
                hovering on a name and clicking the <span
                    class="icon magnify-dummy-icon"
                    ><MagnifyIcon />
                </span> icon that appears next to it.
            </p>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">
                <a id="rankings-page-section" class="page-anchor"
                    >Rankings Page</a
                >
            </h3>
            <p>This page hosts all of our ranked species (and subspecies)!</p>
            <p>
                You might notice that the sidebar filters are different on this
                page. That's because this page filters taxa as opposed to
                observation data.
            </p>
        </div>
    </div>
</div>

<style>
    .magnify-dummy-icon {
        color: var(--accent-color);
        display: inline-block;
        vertical-align: bottom;
        height: 1.2rem;
        width: 1.2rem;
    }
    .page-anchor {
        all: unset;
    }
    .taxa-search-example {
        display: inline-block;
        width: 11rem;
        user-select: none;
        pointer-events: none;
        line-height: 1rem;
        vertical-align: bottom;
    }
    #about-sidebar-positioner {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1rem 0;
    }
    #about-sidebar {
        width: 350px;
    }
    #about-taxa-diagram {
        height: 250px;
        max-width: 100%;
    }
    .ns-ranks-scale {
        padding: 1rem;
        display: flex;
        justify-content: center;
        width: 100%;
        box-sizing: border-box;
    }
    #data-parameter-list {
        display: flex;
        flex-direction: column;
        /* gap: 0.5rem; */
    }
    .modal-button {
        user-select: none;
        background-color: transparent;
        padding: 0;
        color: var(--accent-color);
        border: none;
    }
    #datasets-modal-button:hover {
        filter: brightness(0.8);
    }
    #about-page-wrapper {
        width: 100%;
        background-color: var(--container-back);
        padding: 1.5rem;
        box-sizing: border-box;
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .about-page-body {
        max-width: 800px;
        text-align: left;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .about-page-section {
        /* padding: 1rem; */
        /* border: 1px solid var(--border); */
        box-sizing: border-box;
        /* border-radius: 3px; */
    }
    .about-page-subheader {
        padding: 1rem 0;
        margin: 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        width: 100%;
    }
</style>
