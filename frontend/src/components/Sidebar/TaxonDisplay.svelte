<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import LinkButton from '../../common/LinkButton.svelte';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { isItalicizedRank } from '../../util/taxa';
    import { capitalizeWords } from '../../util/textHelpers';

    const taxonContext = getActiveTaxonContext();
    const taxonInfo = $derived(taxonContext.taxonInfo);

    // Tie loading visuals to taxonContext.taxonLoading
    const isLoading = $derived(taxonContext.taxonLoading);

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
                {#if taxonContext.taxonID}
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
            <!-- {:else}
                <button class="x-icon icon" onclick={clearTaxon}>
                    <XIcon />
                </button> -->
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
                        Status: {capitalizeWords(taxonInfo.taxonomicStatus)}
                    </span>
                    <!-- This SHOULDN'T happen as synonyms should be redirected -->
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
    {/if}
</div>

<style>
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
        gap: 1rem;
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
