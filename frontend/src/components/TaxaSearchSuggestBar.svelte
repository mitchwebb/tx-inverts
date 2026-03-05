<script lang="ts">
    import type { RawSearchSuggestion, SearchSuggestion } from '../types/api';
    import LoadingIcon from '../assets/LoadingIcon.svelte';
    import { isItalicizedRank } from '../util/taxa';
    import InvasiveIcon from '../common/InvasiveIcon.svelte';
    import XIcon from '../assets/XIcon.svelte';

    import { portal } from '../common/Portal.svelte';
    import { tick } from 'svelte';

    type SearchSuggestProps = {
        placeholder?: string | null;
        currentSelection?: string | null;
        handleSelect: (suggestion: SearchSuggestion) => void;
        handleClear: () => void;
    };

    const {
        placeholder = '',
        currentSelection = null,
        handleSelect,
        handleClear,
    }: SearchSuggestProps = $props();

    let suggestions: SearchSuggestion[] = $state([]);
    let inputText: string | null = $state('');
    let suggestionsVisible: boolean = $state(false);
    let isLoading: boolean = $state(false);

    // Used for keyboard navigation of search results
    let activeIndex = $state(-1);

    // Always reset
    $effect(() => {
        if (!suggestionsVisible) {
            activeIndex = -1;
        }
    });

    let abortController = new AbortController(); // Track ongoing requests

    let debounceTimeout: ReturnType<typeof setTimeout>;

    let inputElement: HTMLInputElement;
    let suggestionsElement: HTMLElement | undefined = $state();

    // Suggestion alignment controller
    let alignRight = $state(false);

    // Debounce search suggest to prevent tons of requests
    function debounceSearchSuggest() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            handleSearchSuggest();
        }, 250); // Only submit 250ms after user stops typing
    }

    // Submit current search and return 10 results (max)
    async function handleSearchSuggest() {
        suggestions = [];
        suggestionsVisible = true;
        // Abort the previous request if there is one
        abortController.abort();
        // Create new AbortController
        abortController = new AbortController();
        const signal = abortController.signal;
        const url = '/server/taxa/search_suggest';
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
            suggestions = json.results.map((result: RawSearchSuggestion) => {
                return {
                    scientificName: result.scientific_name,
                    canonicalName: result.canonical_name,
                    taxonID: result.taxon_id,
                    taxonRank: result.taxon_rank,
                    usInvasive: result.us_invasive,
                };
            });
        } catch (error) {
            console.error(error);
        }
    }

    function selectTaxon(suggestion: SearchSuggestion) {
        handleSelect(suggestion);
        suggestionsVisible = false;
    }

    function clearSearch() {
        handleClear();
        inputText = '';
    }

    // Handler for keypress on taxon name
    function handleTaxonKeydown(
        e: KeyboardEvent,
        suggestion: SearchSuggestion
    ) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleSelect(suggestion);
        }
    }

    function handleBlur() {
        suggestionsVisible = false;
        // suggestions = [];
        // inputText = currentSelection;
    }

    function handleInputKeydown(e: KeyboardEvent) {
        if (!suggestionsVisible || !suggestions.length) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                activeIndex = (activeIndex + 1) % suggestions.length;
                break;

            case 'ArrowUp':
                e.preventDefault();
                activeIndex =
                    (activeIndex - 1 + suggestions.length) % suggestions.length;
                break;

            case 'Enter':
                if (activeIndex >= 0) {
                    e.preventDefault();
                    selectTaxon(suggestions[activeIndex]);
                }
                break;

            case 'Escape':
                suggestionsVisible = false;
                break;
        }
    }

    let portalStyle = $state({
        top: '0px',
        left: '0px',
        width: '0px',
        maxHeight: '100px',
    });

    // Give search results to portal, and set positioning using input element
    async function updatePortalPosition() {
        if (!inputElement || !suggestionsVisible) return;

        await tick();

        const inputRect = inputElement.getBoundingClientRect();
        const suggestionsRect = suggestionsElement?.getBoundingClientRect();
        let dropdownWidth = inputRect.width;
        if (!!suggestions.length) {
            dropdownWidth = Math.max(
                inputRect.width,
                suggestionsRect?.width || 0
            );
        }

        const viewportWidth = window.innerWidth;

        const scrollX = window.scrollX;

        let left = inputRect.left + scrollX;

        // Flip right if dropdown would overflow
        if (inputRect.left + dropdownWidth + 10 > viewportWidth) {
            left = inputRect.right + scrollX - dropdownWidth;
            alignRight = true;
        } else {
            alignRight = false;
        }

        // Margin between suggestions and viewport limits
        const margin = 10;
        // Calculate space available in viewport above/below input element
        const spaceBelow = window.innerHeight - (inputRect.bottom + margin);
        const spaceAbove = inputRect.top - margin;

        let top: number;
        let maxHeight: number;

        // Determine above/below behavior for suggestions, and set max height
        if (spaceBelow >= spaceAbove || spaceBelow >= 200) {
            // Open downward
            top = inputRect.bottom + window.scrollY;
            maxHeight = spaceBelow;
        } else {
            // Open upward
            maxHeight = spaceAbove;
            top = inputRect.top + window.scrollY - maxHeight - 5; // 5px gap
        }

        portalStyle = {
            top: `${top}px`,
            left: `${left}px`,
            width: `${dropdownWidth}px`,
            maxHeight: `${maxHeight}px`,
        };
    }

    // Recalculate on suggestions show and window resize
    $effect(() => {
        if (!suggestionsVisible) return;

        // Trigger effect on suggestions changes
        const _ = suggestions;
        const __ = isLoading;

        // Also reset activeIndex
        activeIndex = -1;

        // Wait for DOM update
        tick().then(() => updatePortalPosition());

        updatePortalPosition();

        const handleScroll = () => updatePortalPosition();
        const handleResize = () => updatePortalPosition();

        window.addEventListener('scroll', handleScroll, true); // true = capture phase for all scroll containers
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('scroll', handleScroll, true);
            window.removeEventListener('resize', handleResize);
        };
    });

    $effect(() => {
        if (!suggestionsVisible) {
            inputText = currentSelection;
        }
    });
</script>

<div class="search-wrapper">
    <input
        class="taxon-search"
        type="text"
        bind:value={inputText}
        bind:this={inputElement}
        oninput={debounceSearchSuggest}
        {placeholder}
        onblur={handleBlur}
        onkeydown={handleInputKeydown}
    />
    {#if suggestionsVisible && inputText?.length !== 0}
        <div
            use:portal={'#portal-root'}
            bind:this={suggestionsElement}
            class="suggestions-wrapper"
            style:top={portalStyle.top}
            style:left={portalStyle.left}
            style:min-width={portalStyle.width}
            style:max-height={portalStyle.maxHeight}
        >
            {#if suggestions}
                <ul class="autocomplete-suggestions">
                    {#if isLoading}
                        <div class="loading-icon icon">
                            <LoadingIcon />
                        </div>
                    {:else if suggestions.length == 0}
                        <li
                            id="no-suggestions-item"
                            class="autocomplete-suggestion"
                        >
                            No suggestions
                        </li>
                    {:else}
                        {#each suggestions as suggestion, i}
                            {@const italicized = isItalicizedRank(
                                suggestion.taxonRank
                            )}
                            <li
                                onmousedown={() => selectTaxon(suggestion)}
                                class={[
                                    'autocomplete-suggestion',
                                    { invasive: suggestion.usInvasive },
                                    { active: i === activeIndex },
                                ]}
                                tabindex="0"
                                role="option"
                                aria-selected={i === activeIndex}
                                onkeydown={(e) =>
                                    handleTaxonKeydown(e, suggestion)}
                            >
                                <div
                                    title={suggestion.scientificName}
                                    class={['scientific-name', { italicized }]}
                                >
                                    {suggestion.scientificName}
                                    {#if suggestion.usInvasive}
                                        <div class="invasive-icon icon">
                                            <InvasiveIcon />
                                        </div>
                                    {/if}
                                </div>
                                <div class="taxon-rank">
                                    {suggestion.taxonRank}
                                </div>
                            </li>
                        {/each}
                    {/if}
                </ul>
            {/if}
        </div>
    {/if}
    {#if currentSelection}
        <button class="search-close-button icon" onclick={clearSearch}>
            <XIcon />
        </button>
    {/if}
</div>

<style>
    .autocomplete-suggestion.active {
        background-color: var(--container-highlight);
    }
    #no-suggestions-item {
        pointer-events: none;
    }
    .search-close-button {
        position: absolute;
        right: 0;
        top: 0;
        height: 100%;
        margin: 0;
        padding: 0 0.25rem 0 0;
        background-color: unset;
        color: unset;
        border: unset;
    }
    .search-wrapper {
        min-width: 100px;
        border-radius: 4px;
        border: 1px solid var(--border);
        color: var(--text-default);
        background-color: var(--container-back);
        margin: 0;
        height: 100%;
        min-height: 1.75rem;
        max-height: 2.5rem;
        position: relative;
        flex-grow: 1;
        max-width: 350px;
        align-items: center;
        box-sizing: border-box;
    }
    .invasive-icon {
        display: inline-block;
        margin-left: 0.5rem;
        height: 1.5rem;
        width: 1.5rem;
    }
    .invasive > * {
        color: goldenrod;
    }
    .scientific-name {
        display: flex;
        align-items: center;
        min-width: 0;
        white-space: nowrap;
        text-overflow: ellipsis;
        flex-shrink: 1;
        overflow: hidden;
        /* display: block; */
    }
    .loading-icon {
        color: var(--fill-color);
        margin: auto;
        padding: 0.5rem;
    }
    .taxon-search {
        height: 100%;
        width: 100%;
        color: var(--text-default);
        background-color: transparent;
        border: unset;
        border-radius: 3px;
        padding: 0 2.5rem 0 0.75rem;
        box-sizing: border-box;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .taxon-search:focus {
        outline: 1px solid var(--fill-color);
    }
    .taxon-rank {
        opacity: 0.5;
        font-size: 0.75rem;
    }
    .autocomplete-suggestion {
        list-style-type: none;
        text-align: left;
        margin: 0;
        padding: 0.25rem 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        height: 2.5rem;
        min-width: 0;
        box-sizing: border-box;
    }
    .autocomplete-suggestion:not(:first-child) {
        border-top: 1px solid var(--border);
    }
    .autocomplete-suggestion:hover {
        background-color: var(--container-fore);
        cursor: pointer;
    }
    .suggestions-wrapper {
        color: var(--text-default);
        position: absolute;
        white-space: nowrap;
        margin-top: 5px;
        background-color: var(--container-mid);
        overflow: visible;
        /* border-radius: 4px; */
        width: fit-content;
        max-width: 500px;
        overflow-y: scroll;
        border: 1px solid var(--container-shadow);
        box-shadow: 0px 2px 12px 2px var(--container-shadow);
        box-sizing: border-box;
        z-index: 9999;
    }
    .autocomplete-suggestions {
        padding: 0;
        margin: 0;
    }
</style>
