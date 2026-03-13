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
            [taxonID]: canonicalName,
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
            <div id="taxon-cards-wrapper">
                {#each Object.entries(filtersContext.filteredTaxa ?? {}) as [taxonID, canonicalName]}
                    <div class="filtered-taxon-card button">
                        <div class="filtered-taxon-name">
                            {canonicalName}
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
    #taxon-cards-wrapper {
        display: flex;
        flex-direction: column;
        /* border-radius: 3px; */
        gap: 0.25rem;
        width: fit-content;
    }
    .filtered-taxon-name {
        padding: 0.25rem 0.5rem;
    }
    .filters-section-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .remove-taxon-icon {
        height: 1.5rem;
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
        gap: 0.5rem;
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
