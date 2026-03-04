<script lang="ts">
    import XIcon from '../../assets/XIcon.svelte';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import type { SearchSuggestion } from '../../types/api';
    import TaxaSearchSuggestBar from '../TaxaSearchSuggestBar.svelte';

    const filtersContext = getFiltersContext();

    function handleRemoveTaxon(e: MouseEvent) {
        const target = e.target as HTMLElement;
        const parent = target.parentNode as HTMLElement;
        const taxonID = parent.dataset.taxonId;

        const currentTaxa = filtersContext.filteredTaxa;

        if (!taxonID || !currentTaxa) return;

        const taxonIDNum = Number(taxonID);

        let { [taxonIDNum]: _, ...newTaxa } = currentTaxa;

        if (Object.keys(newTaxa).length === 0) {
            filtersContext.filteredTaxa = null;
        } else {
            filtersContext.filteredTaxa = newTaxa;
        }
    }

    function handleSearchClear() {
        // This doesn't need to function in this case
    }

    function handleSearchSelect(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;

        // Get info from current selection
        const taxonID = suggestion.taxonID;
        const canonicalName = suggestion.canonicalName;

        const currentTaxa = filtersContext.filteredTaxa;

        filtersContext.filteredTaxa = {
            ...currentTaxa,
            [taxonID]: canonicalName
        };
    }
</script>

<div
    class="taxon-filter filters-section"
    class:active={!!filtersContext.filteredTaxa}
>
    <div class="filters-section-header">Taxa</div>
    <div class="filters-section-content">
        <TaxaSearchSuggestBar
            placeholder="Filter by taxon..."
            handleClear={handleSearchClear}
            handleSelect={handleSearchSelect}
        />
        {#if filtersContext.filteredTaxa}
            <div id='taxon-cards-wrapper'>
            {#each Object.entries(filtersContext.filteredTaxa ?? {}) as [taxonID, canonicalName]}
                <div class='filtered-taxon-card button'>
                    <div class='filtered-taxon-name'>
                        {canonicalName}
                    </div>
                    <button 
                        class='remove-taxon-icon icon'
                        data-taxon-id={taxonID} 
                        onclick={handleRemoveTaxon}>
                        <XIcon/>
                    </button>
                </div>
            {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    #taxon-cards-wrapper {
        display: flex;
        flex-direction: column;
        border: 1px solid var(--border);
    }
    .filtered-taxon-name {
        padding: .25rem .5rem;
    }
    .filters-section-content {
        display: flex;
        flex-direction: column;
        gap: .5rem;
    }
    .remove-taxon-icon {
        cursor: pointer;
        padding: 0;
        background-color: var(--container-fore);
        height: 100%;
        border-radius: 0;
    }
    .filtered-taxon-card {
        display: flex;
        gap: .5rem;
        background-color: var(--container-mid);
        /* border: 1px solid var(--border); */
        cursor: unset;
        justify-content: space-between;
        font-size: 1rem;
        align-items: center;
        height: 30px;
    }

    /* .filtered-taxon-card() */
    .filtered-taxon-card:not(:last-child) {
        border-bottom: 1px solid var(--border);
    }
    
</style>
