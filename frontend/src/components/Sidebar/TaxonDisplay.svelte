<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import XIcon from '../../assets/XIcon.svelte';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import LinkButton from '../../common/LinkButton.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { isItalicizedRank } from '../../util/taxa';
    import { capitalizeWords } from '../../util/textHelpers';

    type TaxonDisplayProps = {
        taxonID: number;
    };

    const { taxonID }: TaxonDisplayProps = $props();

    const taxaContext = getActiveTaxaContext();
    const taxon = $derived(taxaContext.taxa.get(taxonID)!);

    // Tie loading visuals to taxaContext.taxonLoading
    const isLoading = $derived(taxon.taxonLoading);

    const taxonNotAccepted = $derived(
        taxon.info.taxonomicStatus !== 'accepted'
    );

    function handleTaxonClose() {
        taxaContext.taxa.remove(taxonID);
    }
</script>

<div id="sidebar-main-header" class="sidebar-header header">
    <div
        class="taxon-display-overlay"
        style:background-color={taxon.color}
    ></div>
    <div
        id="main-header-top"
        class:invasive={taxon.info.usInvasive}
        class:loading-blink={isLoading}
    >
        {#if taxon.taxonError}
            <div id="taxon-error">Requested Taxon Not Found</div>
        {/if}
        <div id="main-header-name">
            {#if taxon.info.usInvasive}
                <div class="invasive-icon">
                    <InvasiveIcon />
                </div>
            {/if}
            {#if taxon.info.canonicalName}
                <span
                    class={'scientific-name'}
                    class:italicized={isItalicizedRank(taxon.info.taxonRank)}
                >
                    {taxon.info.canonicalName}
                </span>
            {/if}
            {#if taxon.info.scientificNameAuthorship}
                <span class="scientific-authorship thin">
                    {taxon.info.scientificNameAuthorship}
                </span>
            {/if}
            {#if taxon.info.canonicalName}
                <div class="gbif-link-button">
                    <LinkButton
                        href={`https://www.gbif.org/species/${taxon.taxonID}`}
                        target="_blank"
                    />
                </div>
            {/if}
            {#if isLoading}
                <div class="loading-icon icon">
                    <LoadingIcon />
                </div>
            {/if}
        </div>
        <button class="icon close-taxon-button" onclick={handleTaxonClose}>
            <XIcon />
        </button>
    </div>
    {#if taxon.info.commonNames && taxon.info.commonNames?.length > 0}
        <div id="common-names" class="thin">
            {(capitalizeWords(taxon.info.commonNames) as string[]).join(', ')}
        </div>
    {/if}
    <div id="aux-taxon-text">
        {#if taxon.info.taxonomicStatus && taxonNotAccepted}
            <div id="taxonomic-status-text" class={'thin dubious-taxon'}>
                <span>
                    Taxon Status: {capitalizeWords(taxon.info.taxonomicStatus)}
                </span>
                {#if taxon.info.taxonomicStatus.includes('synonym')}
                    <div>
                        Accepted Taxon ID: {taxon.info.acceptedTaxonID}
                    </div>
                {/if}
            </div>
        {/if}
        {#if taxon.info.taxonRank}
            <span id="taxon-rank" class="thin">
                {taxon.info.taxonRank}
            </span>
        {/if}
    </div>
</div>

<style>
    .taxon-display-overlay {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        opacity: 0.2;
        pointer-events: none;
    }
    .close-taxon-button {
        padding: 0;
        align-self: baseline;
        justify-self: end;
        background-color: transparent;
    }
    #main-header-name {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
        line-height: 1.3rem;
        font-size: 1.4rem;
    }
    #sidebar-main-header {
        background-size: cover;
        background-position: center;
        display: flex;
        flex-direction: column;
        text-align: left;
        gap: 0.5rem;
        position: relative;
        /* font-size: 1.4rem; */
        overflow-wrap: anywhere;
        word-break: normal;
        hyphens: manual;
        -webkit-hyphens: auto;
        -moz-hyphens: auto;
        background-color: var(--container-highlight);
        border: 1px solid var(--border);
        border-bottom: none;
    }
    #taxon-error {
        color: var(--accent-color);
    }
    .gbif-link-button {
        height: 0.9rem;
        display: inline-block;
        color: var(--fill-color);
        align-self: flex-start;
    }
    .invasive-icon {
        height: 1.2rem;
        width: 1.2rem;
        color: var(--accent-color);
    }
    .invasive > * {
        color: var(--accent-color);
    }
    .dubious-taxon {
        color: var(--accent-color);
    }
    #main-header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        position: relative;
    }
    #aux-taxon-text {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
    }
    .loading-icon {
        cursor: pointer;
        background-color: transparent;
        padding: 0;
        color: var(--text-default);
        border: none;
        flex-shrink: 0;
    }
    .scientific-name {
        font-weight: 400;
        /* flex-shrink: 0; */
        word-break: normal;
    }
    .scientific-authorship {
        flex-shrink: 1;
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
