<script lang="ts">
    import { datasets } from '../../contexts/Datasets';
    import './aboutModals.css';
</script>

{#if $datasets}
    <!-- Get list of keys sorted by dataset title -->
    {@const sortedKeys = Object.keys($datasets).sort((a, b) =>
        $datasets[a].datasetTitle.localeCompare($datasets[b].datasetTitle)
    )}
    <div id="datasets-modal" class="about-modal-wrapper">
        <h3 class="modal-header">Included Datasets</h3>
        <div id="datasets-modal-body">
            <p id="datasets-blurb">
                Our included datasets are selected from a list of datasets on
                GBIF containing invertebrate data within Texas. To help with
                data quality, we've filtered to institutions and universities,
                excluding most citizen science sources.
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

<style>
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
        /* list-style: none; */
    }
    .dataset-name {
        text-align: left;
    }
</style>
