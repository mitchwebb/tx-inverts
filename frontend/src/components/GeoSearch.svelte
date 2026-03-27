<script lang="ts">
    import InvasiveIcon from "../common/InvasiveIcon.svelte";
    import SearchSuggestBar from "../common/SearchSuggestBar.svelte";
    import { getFiltersContext } from "../contexts/filtersContext";

    type GeoSearchProps = {
        placeholder?: string | null;
    }
    const { placeholder='Search for a region...' }: GeoSearchProps = $props();
    
    type CountySuggestion = Record<"county", string>;

    const filtersContext = getFiltersContext();

    let isLoading: boolean = $state(false);
    let suggestions: CountySuggestion[] = $state([]);

    let abortController = new AbortController();
    // Submit current search and return 10 results (max)
    async function handleSearchSuggest(inputText: string) {
        suggestions = [];
        // Abort the previous request if there is one
        if (abortController) abortController.abort();
        // Create new AbortController
        abortController = new AbortController();
        const signal = abortController.signal;
        const url = '/server/map/search_counties';
        try {
            // Set is loading
            isLoading = true;
            // Send search request
            const response = await fetch(url, {
                signal,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: inputText }),
            });
            // Error
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            // Ending loading
            isLoading = false;
            const json = await response.json();
            console.log(json)
            suggestions = json.results.map((result: CountySuggestion) => {
                return {
                    county: result.county
                };
            });
        } catch (error) {
            console.error(error);
        }
    }

    function handleGeoSelect(suggestion: CountySuggestion) {
        console.log(suggestion)
    }
</script>

{#snippet row(suggestion: CountySuggestion)}
    <div>
        {suggestion.county}
    </div>
{/snippet}


<SearchSuggestBar 
    {placeholder}
    handleSearchSuggest={handleSearchSuggest}
    handleSelect={handleGeoSelect} 
    suggestions={suggestions} 
    {row} 
    {isLoading} 
/>

<style>
</style>
