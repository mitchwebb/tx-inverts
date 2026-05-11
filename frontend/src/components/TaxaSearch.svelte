<script lang="ts">
    import InvasiveIcon from '../common/InvasiveIcon.svelte';
    import SearchSuggestBar from '../common/SearchSuggestBar.svelte';
    import {
        getActiveTaxaContext,
        initialTaxonState,
    } from '../contexts/activeTaxaContext';
    import type {
        RawTaxonSearchSuggestion,
        TaxonSearchSuggestion,
    } from '../types/api';
    import { isItalicizedRank } from '../util/taxa';

    type TaxaSearchProps = {
        placeholder?: string | null;
        handleBlur?: () => void;
        autoFocus?: boolean;
        replace?: boolean;
        excludeSpecies?: boolean;
        onSelect?: () => void;
    };

    const {
        placeholder = 'Search for taxa...',
        handleBlur,
        autoFocus = false,
        replace = false,
        excludeSpecies = false,
        onSelect,
    }: TaxaSearchProps = $props();

    const taxaContext = getActiveTaxaContext();

    let isLoading: boolean = $state(false);
    let suggestions: TaxonSearchSuggestion[] = $state([]);

    let abortController = new AbortController();

    // Submit current search and return 10 results (max)
    async function handleSearchSuggest(inputText: string) {
        suggestions = [];
        // Abort the previous request if there is one
        if (abortController) abortController.abort();
        // Create new AbortController
        abortController = new AbortController();
        const signal = abortController.signal;
        const url = '/server/taxa/taxon_search_suggest';
        try {
            // Set is loading
            isLoading = true;
            // Send search request
            const response = await fetch(url, {
                signal,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: inputText,
                    exclude_species: excludeSpecies,
                }),
            });
            // Error
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            // Ending loading
            isLoading = false;
            const json = await response.json();
            suggestions = json.results.map(
                (result: RawTaxonSearchSuggestion) => {
                    return {
                        scientificName: result.scientific_name,
                        canonicalName: result.canonical_name,
                        taxonID: result.taxon_id,
                        taxonRank: result.taxon_rank,
                        usInvasive: result.us_invasive,
                    };
                }
            );
        } catch (error) {
            console.error(error);
        }
    }

    function handleTaxonSelect(suggestion: TaxonSearchSuggestion) {
        if (!suggestion.taxonID) return;

        if (replace) taxaContext.taxa.clear();

        taxaContext.taxa.add({
            ...initialTaxonState,
            taxonID: suggestion.taxonID,
        });

        if (onSelect) {
            onSelect();
        }
    }
</script>

{#snippet row(suggestion: TaxonSearchSuggestion)}
    {@const italicized = isItalicizedRank(suggestion.taxonRank)}
    <div
        class="taxon-suggestion-wrapper"
        class:invasive={suggestion.usInvasive}
    >
        <div title={suggestion.scientificName} class="scientific-name-wrapper">
            <span class={['scientific-name', { italicized }]}
                >{suggestion.scientificName}</span
            >
            {#if suggestion.usInvasive}
                <div class="invasive-icon icon">
                    <InvasiveIcon />
                </div>
            {/if}
        </div>
        <div class="taxon-rank">
            {suggestion.taxonRank}
        </div>
    </div>
{/snippet}

<SearchSuggestBar
    {placeholder}
    {autoFocus}
    {handleBlur}
    {handleSearchSuggest}
    handleSelect={handleTaxonSelect}
    {suggestions}
    {row}
    {isLoading}
/>

<style>
    .taxon-suggestion-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        gap: 0.25rem;
    }
    .invasive-icon {
        display: inline-block;
        margin-left: 0.5rem;
        height: 1.5rem;
        width: 1.5rem;
    }
    .invasive > * {
        color: var(--accent-color);
    }
    .scientific-name {
        min-width: 0;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .scientific-name-wrapper {
        display: flex;
        align-items: center;
        white-space: nowrap;
        flex-shrink: 1;
        overflow: hidden;
        /* display: block; */
    }
    .taxon-rank {
        opacity: 0.5;
        font-size: 0.75rem;
    }
</style>
