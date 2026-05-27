<!-- Middle component for extracting geographic search logic (for multiple API routes) -->
<script lang="ts" generics="T">
    import type { Snippet } from "svelte";
    import SearchSuggestBar from "../common/SearchSuggestBar.svelte";

    type GeoSearchProps = {
        placeholder?: string | null;
        pathSuffix: 'parks' | 'counties';
        parseJSON: (json: any) => T[];
        suggestionRow: Snippet<[T, number]>;
        handleSelect: (suggestion: T) => void;
    }
    const { 
        placeholder='Search for a region...',
        pathSuffix,
        parseJSON,
        suggestionRow,
        handleSelect
    }: GeoSearchProps = $props();

    let isLoading: boolean = $state(false);
    let suggestions: T[] = $state([]);

    let abortController = new AbortController();
    // Submit current search and return 10 results (max)
    async function handleSearchSuggest(inputText: string) {
        suggestions = [];
        // Abort the previous request if there is one
        if (abortController) abortController.abort();
        // Create new AbortController
        abortController = new AbortController();
        const signal = abortController.signal;
        const url = `/server/map/search_${pathSuffix}?search_term=${inputText}`;
        try {
            // Set is loading
            isLoading = true;
            // Send search request
            const response = await fetch(url, {
                signal,
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            // Error
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            // Ending loading
            isLoading = false;
            const json = await response.json();
            const parsedJSON = parseJSON(json.results);
            suggestions = parsedJSON;
        } catch (error) {
            console.error(error);
        }
    }

    function handleGeoSelect(suggestion: T) {
        handleSelect(suggestion);
    }
</script>

<div class='geo-searchbar'>
    <SearchSuggestBar 
        {placeholder}
        handleSearchSuggest={handleSearchSuggest}
        handleSelect={handleGeoSelect} 
        suggestions={suggestions} 
        row={suggestionRow} 
        {isLoading} 
    />
</div>


<style>
    .geo-searchbar {
        height: 2.5rem;
        width: 100%;
    }
</style>
