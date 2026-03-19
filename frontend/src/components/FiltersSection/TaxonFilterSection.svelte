<script lang="ts">
    import XIcon from '../../assets/XIcon.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import type { SearchSuggestion } from '../../types/api';
    import { isItalicizedRank } from '../../util/taxa';
    import TaxaSearchSuggestBar from '../TaxaSearchSuggestBar.svelte';

    const taxaContext = getActiveTaxaContext();

    function handleRemoveTaxon(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;
        const taxonID = target.dataset.taxonId;

        if (!taxonID) return;

        taxaContext.remove(Number(taxonID));
    }

    function handleSearchClear() {
        // This doesn't need to function in this case
    }

    function handleSearchSelect(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;

        // Get info from current selection
        const taxonID = suggestion.taxonID;

        taxaContext.add(Number(taxonID), true);
    }
</script>

<div
    class="taxon-filter filters-section"
    class:active={!!taxaContext.taxonIDs.length}
>
    <div class="filters-section-header">Taxa</div>
    <div class="filters-section-content">
        <TaxaSearchSuggestBar
            placeholder="Filter by taxon..."
            handleClear={handleSearchClear}
            handleSelect={handleSearchSelect}
        />
        {#if !!taxaContext.taxonIDs.length}
            <div id="taxon-cards-wrapper">
                {#each taxaContext.taxonIDs as taxonID}
                    {@const taxonInfo = taxaContext.taxa[taxonID].info}
                    {@const isItalicized = isItalicizedRank(
                        taxonInfo.taxonRank
                    )}
                    <div class="filtered-taxon-card button">
                        <div class="filtered-taxon-name">
                            <span class:italicized={isItalicized}
                                >{taxonInfo.canonicalName}</span
                            >
                            <div class="filtered-taxon-authorship thin">
                                {taxaContext.taxa[taxonID].info
                                    .scientificNameAuthorship}
                            </div>
                        </div>

                        <button
                            class="remove-taxon-button icon"
                            data-taxon-id={taxonID}
                            onclick={handleRemoveTaxon}
                        >
                            <div class="remove-taxon-icon">
                                <XIcon />
                            </div>
                        </button>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .italicized {
        font-style: italic;
    }
    #taxon-cards-wrapper {
        display: flex;
        flex-direction: column;
        /* border-radius: 3px; */
        gap: 0.25rem;
        width: fit-content;
    }
    .filtered-taxon-name {
        display: flex;
        gap: 0.5rem;
        padding: 0.25rem 0.5rem;
    }
    .filters-section-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .remove-taxon-icon {
        height: 1.5rem;
        pointer-events: none;
    }
    .remove-taxon-button {
        cursor: pointer;
        padding: 0;
        background-color: var(--container-back);
        border-radius: 3px;
        height: 100%;
        width: 1.75rem;
        display: flex;
        justify-content: center;
        align-items: center;
        /* margin-right: 0.25rem; */
    }
    .filtered-taxon-card {
        display: flex;
        /* gap: 0.5rem; */
        background-color: var(--container-mid);
        cursor: unset;
        justify-content: space-between;
        border: 1px solid var(--border);
        font-size: 1rem;
        align-items: center;
        height: 30px;
        border-radius: 3px;
    }
</style>
