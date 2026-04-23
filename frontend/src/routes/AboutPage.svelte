<script lang="ts">
    import InfoButton from '../common/InfoButton.svelte';
    import { datasets } from '../contexts/Datasets';
    import { getModalContext } from '../contexts/modalContext';
    import { openModal } from '../lib/modal.svelte';

    const modalContext = getModalContext();

    function showDatasetsModal() {
        openModal(modalContext, datasetsModal);
    }
</script>

{#snippet datasetsModal()}
    {#if $datasets}
        <!-- Get list of keys sorted by dataset title -->
        {@const sortedKeys = Object.keys($datasets).sort((a, b) =>
            $datasets[a].datasetTitle.localeCompare($datasets[b].datasetTitle)
        )}
        <div id="datasets-modal">
            <h3>Included Datasets</h3>
            <div id="datasets-modal-body">
                <p id="datasets-blurb">
                    Our included datasets are selected from a list of datasets
                    on GBIF containing invertebrate data within Texas. To help
                    with data quality, we've filtered to institutions and
                    universities, excluding most citizen science sources.
                </p>
                <ul class="dataset-list">
                    {#each sortedKeys as datasetKey}
                        <li class="dataset-name">
                            <a
                                href={`https://www.gbif.org/dataset/${datasetKey}`}
                                target="_blank"
                            >
                                {$datasets[datasetKey]['datasetTitle']}
                            </a>
                        </li>
                    {/each}
                </ul>
            </div>
        </div>
    {/if}
{/snippet}

<div id="about-page-wrapper">
    <h1 id="about-header">Welcome to Texas Inverts!</h1>
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
        <div class="about-page-section">
            <h3 class="about-page-subheader">Observation Data</h3>
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
                <li>Non-Chordate Animalia</li>
                <li>Chordate Invertebrates</li>
                <ul>
                    <li>Thaliacea</li>
                    <li>Ascidiacea</li>
                    <li>Appendicularia</li>
                    <li>Leptocardii</li>
                </ul>
                <li>Occurrence Status: Present</li>
                <li>
                    <button
                        onclick={showDatasetsModal}
                        id="datasets-modal-button"
                    >
                        Within Approved Datasets
                    </button>
                </li>
                <li>Within a Simple Texas Bounding Box</li>
            </ul>
            <p>
                From here, our data is processed a bit further. Records without
                valid collection dates are examined, unambiguous dates are
                assigned when available, and those that remain are filtered out.
                The records are then filtered to a Texas boundary shapefile
                (from TxDOT), and entered into our database.
            </p>
        </div>
        <div class="about-page-section">
            <h3 class="about-page-subheader">Taxonomic Backbone:</h3>
            <p>
                Our taxonomic backbone is sourced from the
                <a
                    href="https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
                    target="_blank"
                >
                    GBIF Taxonomic Backbone
                </a>, before being filtered down to those species with
                occurrence records within Texas. See the
                <a href="/backbone">Backbone page</a> to browse the structure.
            </p>
        </div>
    </div>
</div>

<style>
    #data-parameter-list {
        display: flex;
        flex-direction: column;
        /* gap: 0.5rem; */
    }

    #datasets-modal-button {
        user-select: none;
        background-color: transparent;
        padding: 0;
        color: var(--accent-color);
        border: none;
    }
    #datasets-modal-button:hover {
        filter: brightness(0.8);
    }
    #datasets-modal {
        display: flex;
        flex-direction: column;
        max-width: 750px;
        padding: 1rem;
    }
    #datasets-blurb {
        text-align: left;
    }
    #datasets-modal-body {
        padding: 0 1rem;
    }
    .dataset-list {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        /* padding-left: 1rem; */
        list-style: none;
    }
    .dataset-name {
        text-align: left;
    }
    #about-page-wrapper {
        width: 100%;
        min-height: 100%;
        background-color: var(--container-back);
        padding: 3rem;
        box-sizing: border-box;
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        align-items: center;
        /* gap: 0.5rem; */
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
        border-bottom: 1px solid var(--border);
        width: 100%;
    }
</style>
