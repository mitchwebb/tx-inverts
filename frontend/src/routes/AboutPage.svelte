<script lang="ts">
    import type { Snippet } from 'svelte';
    import DatasetsModal from '../common/Modals/DatasetsModal.svelte';
    import OccurrencesModal from '../common/Modals/OccurrencesModal.svelte';
    import NSScale from '../common/NSScale.svelte';
    import TaxonPyramid from '../common/TaxonPyramid.svelte';
    import { getModalContext } from '../contexts/modalContext';
    import { getRouterContext } from '../contexts/routerContext';
    import { openModal } from '../lib/modal.svelte';
    import RangeExtentModal from '../common/Modals/RangeExtentModal.svelte';

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

{#snippet datasetsModal()}
    <DatasetsModal />
{/snippet}

{#snippet occurrencesModal()}
    <OccurrencesModal />
{/snippet}

{#snippet rangeExtentModal()}
    <RangeExtentModal />
{/snippet}

<div id="about-page-wrapper">
    <div id="welcome-banner-wrapper">
        <img
            id="welcome-banner"
            alt="Welcome to Texas Inverts"
            src="/static/welcome_banner.png"
        />
    </div>
    <div class="about-page-body">
        <div class="about-page-summary">
            <p>
                Texas is home to more than 30,000 invertebrate species—an
                extraordinary level of biodiversity that remains, in many
                respects, poorly understood. This site was designed as part of
                Texas Parks and Wildlife's ongoing goal to better understand,
                prioritize, and protect these species.
            </p>
            <p>
                Texas Inverts was created through a partnership between the
                University of Texas at Austin and Texas Parks and Wildlife
                (TPWD). This is a space to interact with Texas' publicly
                available invertebrate species data, designed to help inform
                TPWD's <i> Species of Greatest Conservation Need (SGCN) </i>
                list. The SGCN list, developed as part of Texas'
                <i> State Wildlife Action Plan (SWAP) </i>, serves to guide
                research, restoration, management, and recovery efforts for
                wildlife and plants across Texas.
            </p>
        </div>
        <div>
            <h3 class="about-page-subheader">Rankings</h3>
            <div class="ns-ranks-scale">
                <NSScale level="s" />
            </div>
            <p>
                The main goal of this tool is to provide preliminary
                conservation rankings for our invertebrate species in Texas.
                These rankings, like those on the
                <a href="https://www.iucnredlist.org/" target="_blank">
                    IUCN Red List
                </a>
                or those produced by
                <a href="https://www.natureserve.org/" target="_blank">
                    NatureServe
                </a>, are not typically made en masse—and for good reason. The
                data and expertise needed to justifiably produce these rankings
                aren't available for many species, with invertebrates being
                especially underrepresented. With 30,000+ species in Texas
                alone, many species are difficult to find, difficult to
                identify, or altogether ignored.
            </p>
            <p>
                With this in mind, the rankings on this site are fundamentally
                approximate and imperfect. They are not meant to be taken as
                final rankings but are instead made to be used as a starting
                point when considering the ranking process for any given
                species. For Texas Parks and Wildlife, this means being able to
                make a more informed start when determining which species to
                examine more closely.
            </p>
            <p>
                For this tool, there are two metrics that are used to calculate
                these preliminary rankings:
            </p>
            <ul>
                <li>
                    <button
                        onclick={() => showModal(occurrencesModal)}
                        id="datasets-modal-button"
                        class="modal-button"
                    >
                        Occurrences
                    </button>
                </li>
                <li>
                    <button
                        onclick={() => showModal(rangeExtentModal)}
                        id="datasets-modal-button"
                        class="modal-button"
                    >
                        Range Extent
                    </button>
                </li>
            </ul>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">Our Data</h3>
            <p>
                Texas Inverts was built upon public observation data collected
                by universities and institutions in the US, as well as data from
                the citizen science app, iNaturalist. We source this data from
                <a href="https://www.gbif.org" target="_blank">GBIF</a> (the Global
                Biodiversity Information Facility) in DarwinCore format.
            </p>
            <p>Our observation dataset begins with these requirements:</p>
            <ul id="data-parameter-list">
                <li>Invertebrate Species</li>
                <ul>
                    <li>Non-Chordate Animalia</li>
                </ul>
                <ul>
                    <li>Chordate Invertebrates</li>
                    <ul>
                        <li>Thaliacea</li>
                        <li>Ascidiacea</li>
                        <li>Appendicularia</li>
                        <li>Leptocardii</li>
                    </ul>
                </ul>
                <li>Occurrence Status: Present</li>
                <li>
                    Found Within
                    <button
                        onclick={() => showModal(datasetsModal)}
                        id="datasets-modal-button"
                        class="modal-button"
                    >
                        Approved Datasets
                    </button>
                </li>
                <li>Located Within Texas Bounding Box</li>
            </ul>
            <p>
                After this preliminary filter, records without valid collection
                dates are examined, unambiguous dates are assigned when
                available, and those that remain are filtered out. The records
                are then filtered to a Texas boundary shapefile (sourced from
                TxDOT) and entered into our database.
            </p>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">Our Taxonomic Backbone</h3>
            <div id="about-taxa-diagram">
                <TaxonPyramid />
            </div>
            <p>
                Our taxonomic backbone, the foundation for how we classify and
                structure the relationships between species on this site, is
                sourced from the
                <a
                    href="https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
                    target="_blank"
                >
                    GBIF Taxonomic Backbone
                </a>
                before being filtered down to those species with occurrence records
                within Texas. See the
                <a
                    class="page-link"
                    href={'/backbone'}
                    onclick={handlePageLink}
                    onkeydown={handlePageLink}
                >
                    Backbone Page
                </a>
                to browse the structure.
            </p>
            <p>
                There is no universally accepted taxonomic tree, and taxonomic
                relationships are constantly in flux as we learn new information
                and discover new species. In the interest of keeping our
                occurrence data consistent with our taxonomy, this project bases
                both on GBIF's conventions.
            </p>
        </div>
    </div>
</div>

<style>
    #welcome-banner-wrapper {
        border-radius: 3px;
        background-color: #056565;
        margin: 1rem 0;
        width: 100%;
        max-width: 1000px;
        box-sizing: border-box;
    }
    #welcome-banner {
        padding: 1rem 0;
        object-fit: cover;
        max-width: 100%;
        box-sizing: border-box;
        max-height: 100%;
        min-height: 200px;
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
