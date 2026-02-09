<script lang="ts">
    import { getFiltersContext } from '../../contexts/filtersContext';
    import type { SearchSuggestion } from '../../types/api';
    import TaxaSearchSuggestBar from '../TaxaSearchSuggestBar.svelte';

    const filtersContext = getFiltersContext();

    function handleSearchClear() {
        filtersContext.filteredTaxonID = null;
    }

    function handleSearchSelect(suggestion: SearchSuggestion) {
        if (!suggestion.taxonID) return;

        filtersContext.filteredTaxonID = suggestion.taxonID;
    }
</script>

<div
    class="taxon-filter filters-section"
    class:active={!!filtersContext.filteredTaxonID}
>
    <div class="filters-section-header">Taxon</div>
    <div class="filters-section-content">
        <TaxaSearchSuggestBar
            placeholder="Filter by taxon..."
            handleClear={handleSearchClear}
            handleSelect={handleSearchSelect}
            currentSelection={filtersContext.filteredCanonicalName}
        />
    </div>
</div>

<style>
</style>
