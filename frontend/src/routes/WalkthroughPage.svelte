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
            <p>
                At the top you'll see a filters button along with another taxon
                search bar. By clicking the filters button, you'll be presented
                with optional filters, which are dependent on your current page
                and currently selected taxa—in this case, you'll see filters for
                observation data. On the Rankings page, you will see filters for
                taxa instead. The search bar operates in the same way as the
                header search bar.
            </p>
            <p>
                Below this toolbar is the display for a sample taxon. The top
                section displays the scientific name, a few common names (if
                available), taxonomic rank, and a link to the GBIF page for this
                taxon. Below that, in the Conservation Values foldout, you'll
                see the proposed conservation rank for this species, followed by
                the values used to make this preliminary rank. These values are
                derived from the currently available public data.
            </p>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">
                <a id="map-page-section" class="page-anchor" href="/map"
                    >Map Page</a
                >
            </h3>
            <p>
                The map page allows you to view observation data for your
                selected species. Each species selected in the sidebar will show
                up as a different color on the map, matched to its color in the
                sidebar. The individual points of data are surrounded by a
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
            <img
                id="map-screenshot"
                alt="A sample of observation points grouped on a map"
                src="../static/map-screenshot.png"
            />
            <p>
                When zoomed out, observation points are grouped into squares as
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
                <a
                    id="backbone-page-section"
                    class="page-anchor"
                    href="/backbone">Backbone Page</a
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
            <div id="backbone-screenshot-wrapper">
                <img
                    id="backbone-screenshot"
                    alt="A sample of a taxonomic tree on the backbone page"
                    src="../static/backbone-screenshot.png"
                />
            </div>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">
                <a
                    id="rankings-page-section"
                    class="page-anchor"
                    href="/rankings">Rankings Page</a
                >
            </h3>
            <img
                id="rankings-screenshot"
                alt="A sample of the rankings page with a list of Camponotus species and their rankings"
                src="../static/rankings-screenshot.png"
            />
            <p>This page hosts all of our species (and subspecies) rankings!</p>
            <p>
                You'll find that the sidebar filters are different on this page.
                As mentioned above, the filters on this page filter taxa as
                opposed to observation data. Along with these filters, you can
                filter the list of taxa shown on this page by searching for a
                parent taxon of genus or higher taxonomic rank.
            </p>
            <p>
                As an important note, the suggested rankings found on this site
                are fundamentally approximate and imperfect. They are not meant
                to be taken as final rankings but are instead made to be used as
                a starting point when considering the ranking process for any
                given species. For Texas Parks and Wildlife, this means being
                able to make a more informed start when determining which
                species to examine more closely. Check out the <a
                    href="/about/txinverts"
                >
                    about page
                </a> for more info on the data used to make these preliminary rankings.
            </p>
            <p>
                The rankings shown in the leftmost column of this table are
                rankings made with no additional filters to our data. These
                rankings update when toggling iNaturalist data on or off, but do
                not otherwise take any filtering into account. By clicking on a
                column header, you can sort the list by the selected column. You
                can also use this page to select species in the sidebar by
                hovering on a name and clicking the <span
                    class="icon magnify-dummy-icon"
                    ><MagnifyIcon />
                </span> icon that appears next to it.
            </p>
        </div>
    </div>
</div>

<style>
    #rankings-screenshot {
        float: left;
        object-fit: cover;
        height: 300px;
        margin-right: 1rem;
    }
    #backbone-screenshot-wrapper {
        display: flex;
        justify-content: center;
    }
    img {
        border-radius: 3px;
        border: 1px solid var(--border);
    }
    #backbone-screenshot {
        margin: 0;
        width: 500px;
        height: 134px;
        object-fit: cover;
    }
    #map-screenshot {
        width: 306px;
        height: 134px;
        float: right;
        margin-left: 1rem;
    }
    .magnify-dummy-icon {
        color: var(--accent-color);
        display: inline-block;
        vertical-align: bottom;
        height: 1.2rem;
        width: 1.2rem;
    }
    .page-anchor {
        all: unset;
        cursor: pointer;
    }
    .page-anchor:hover {
        color: var(--accent-color);
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
        box-sizing: border-box;
    }
    .about-page-subheader {
        padding: 1rem 0;
        margin: 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        width: 100%;
    }
</style>
