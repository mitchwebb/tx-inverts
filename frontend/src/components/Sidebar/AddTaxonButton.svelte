<script lang="ts">
    import PlusIcon from '../../assets/PlusIcon.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import type { SearchSuggestion } from '../../types/api';
    import TaxaSearchSuggestBar from '../TaxaSearchSuggestBar.svelte';

    const taxaContext = getActiveTaxaContext();

    // This param determines whether to show the add button or the search bar
    let active: boolean = $state(false);

    // When selecting a new taxon, append to list of taxa in context
    function handleAddTaxon(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;
        taxaContext.add(suggestion.taxonID, true);
        active = false;
    }

    function handleSearchBlur() {
        active = false;
    }
</script>

<div id="add-taxon-button-wrapper">
    {#if active}
        <TaxaSearchSuggestBar
            placeholder="Search for Taxon to Add..."
            handleSelect={handleAddTaxon}
            autoFocus={true}
            handleBlur={handleSearchBlur}
        />
    {:else}
        <button id="add-taxon-button" onclick={() => (active = !active)}>
            <span>Add Taxon</span>
            <span id="add-taxon-icon" class="icon">
                <PlusIcon />
            </span>
        </button>
    {/if}
</div>

<style>
    #add-taxon-button-wrapper {
        display: flex;
        width: 100%;
        height: 2.5rem;
        box-sizing: border-box;
    }
    #add-taxon-button {
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--border);
        width: 100%;
        height: 100%;
        padding: 0;
        gap: 0.5rem;
    }
</style>
