<script lang="ts">
    // import DownloadIcon from '../../assets/DownloadIcon.svelte';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import LinkButton from '../../common/LinkButton.svelte';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { getModalContext } from '../../contexts/modalContext';
    import { isItalicizedRank } from '../../util/taxa';
    import { capitalizeWords } from '../../util/textHelpers';
    // import DownloadOccurrenceForm from '../DownloadOccurrenceForm.svelte';

    const taxonContext = getActiveTaxonContext();
    const taxonInfo = $derived(taxonContext.taxonInfo);

    const modalContext = getModalContext();

    // Tie loading visuals to taxonContext.taxonLoading
    const isLoading = $derived(taxonContext.taxonLoading);

    // function handleOccDownloadButton() {
    //     modalContext.visible = true;
    //     modalContext.content = DownloadOccurrenceForm;
    // }

    const taxonNotAccepted = $derived(taxonInfo.taxonomicStatus !== 'accepted');
</script>

<div id="sidebar-main-header" class="sidebar-section sidebar-header">
    {#if taxonContext.taxonError}
        <div id="taxon-error">Requested Taxon Not Found</div>
    {:else}
        <div
            id="main-header-top"
            class:invasive={taxonInfo.usInvasive}
            class:loading-blink={isLoading}
        >
            <span id="main-header-name">
                {#if taxonInfo.usInvasive}
                    <span class="invasive-icon icon">
                        <InvasiveIcon />
                    </span>
                {/if}
                <span
                    class={'scientific-name'}
                    class:italicized={isItalicizedRank(taxonInfo.taxonRank)}
                >
                    {taxonInfo.canonicalName}
                </span>
                <span class="authorship subheader thin">
                    {taxonInfo.scientificNameAuthorship}
                </span>
                {#if taxonInfo.canonicalName}
                    <span class="gbif-link-button">
                        <LinkButton
                            href={`https://www.gbif.org/species/${taxonContext.taxonID}`}
                            target="_blank"
                        />
                    </span>
                {/if}
            </span>
            {#if isLoading}
                <div class="loading-icon icon">
                    <LoadingIcon />
                </div>
            {/if}
        </div>
        {#if taxonInfo.commonNames && taxonInfo.commonNames?.length > 0}
            <div id="common-names" class="thin">
                {(capitalizeWords(taxonInfo.commonNames) as string[]).join(
                    ', '
                )}
            </div>
        {/if}
        <div id="aux-taxon-text">
            {#if taxonInfo.taxonomicStatus && taxonNotAccepted}
                <div id="taxonomic-status-text" class={'thin dubious-taxon'}>
                    <span>
                        Taxon Status: {capitalizeWords(
                            taxonInfo.taxonomicStatus
                        )}
                    </span>
                    {#if taxonInfo.taxonomicStatus.includes('synonym')}
                        <div>
                            Accepted Taxon ID: {taxonInfo.acceptedTaxonID}
                        </div>
                    {/if}
                </div>
            {/if}
            {#if taxonInfo.taxonRank}
                <span id="taxon-rank" class="thin">
                    {taxonInfo.taxonRank}
                </span>
            {/if}
        </div>
        <!-- <div id="observations-download-section">
            {#if taxonContext.nSValues.observationCount}
                <div class="observation-count thin">
                    Records: {taxonContext.nSValues.observationCount?.toLocaleString()}
                </div>
                <button
                    class="download-button"
                    onclick={handleOccDownloadButton}
                >
                    <DownloadIcon />
                </button>
            {/if}
        </div> -->
    {/if}
</div>

<style>
    #observations-download-section {
        display: flex;
        gap: 0.5rem;
        width: 100%;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
    }
    .observation-count {
        font-size: 1rem;
    }
    .download-button {
        box-sizing: border-box;
        height: 1.5rem;
        width: 1.5rem;
        padding: 0;
    }
    #sidebar-main-header {
        display: flex;
        flex-direction: column;
        text-align: left;
        gap: 0.5rem;
        position: relative;
        font-size: 1.5rem;
        overflow-wrap: anywhere;
        word-break: normal;
        hyphens: manual;
        -webkit-hyphens: auto;
        -moz-hyphens: auto;
        background-color: var(--container-highlight);
        border: 1px solid var(--border);
    }
    #taxon-error {
        color: goldenrod;
    }
    .gbif-link-button {
        height: 0.9rem;
        display: inline-block;
        color: var(--fill-color);
    }
    .invasive-icon {
        display: inline-block;
        vertical-align: -0.125em;
        color: goldenrod;
    }
    .invasive > * {
        color: goldenrod;
    }
    .dubious-taxon {
        color: goldenrod;
    }
    #main-header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    #aux-taxon-text {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
    }
    .x-icon,
    .loading-icon {
        cursor: pointer;
        background-color: transparent;
        padding: 0;
        color: var(--text-default);
        border: none;
        flex-shrink: 0;
    }
    .x-icon {
        align-self: first baseline;
    }
    .x-icon:hover {
        color: var(--border);
    }
    .scientific-name {
        font-weight: 400;
    }
    #taxon-rank {
        opacity: 0.7;
        line-height: 1;
        font-size: 1rem;
        white-space: nowrap;
    }
    #taxonomic-status-text {
        font-size: 1rem;
        line-height: 1;
    }
    #common-names {
        line-height: 1;
        font-size: 1rem;
    }
</style>
