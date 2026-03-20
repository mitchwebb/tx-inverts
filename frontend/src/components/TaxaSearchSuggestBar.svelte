<script lang="ts">
    import type { RawSearchSuggestion, SearchSuggestion } from '../types/api';
    import LoadingIcon from '../assets/LoadingIcon.svelte';
    import { isItalicizedRank } from '../util/taxa';
    import InvasiveIcon from '../common/InvasiveIcon.svelte';
    import XIcon from '../assets/XIcon.svelte';

    import { portal } from '../common/Portal.svelte';
    import { onMount, tick } from 'svelte';

    type SearchSuggestProps = {
        placeholder?: string | null;
        handleSelect: (suggestion: SearchSuggestion) => void;
        handleClear?: (taxonID: number) => void;
        handleBlur?: () => void;
        autoFocus?: boolean;
    };

    let {
        placeholder = '',
        handleSelect,
        handleClear,
        handleBlur,
        autoFocus = false,
    }: SearchSuggestProps = $props();

    let suggestions: SearchSuggestion[] = $state([]);
    let inputText: string | null = $state('');
    let suggestionsVisible: boolean = $state(false);
    let isLoading: boolean = $state(false);

    // Used for keyboard navigation of search results
    let activeIndex = $state(-1);

    let currentSelection: SearchSuggestion | null = $state(null);

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

    let focused: boolean = $derived(autoFocus || false);

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
        currentSelection = suggestion;
        suggestionsVisible = false;
    }

    function clearSearch() {
        if (currentSelection?.taxonID && handleClear) {
            handleClear(currentSelection.taxonID);
        }
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

    function handleBlurInternal() {
        suggestionsVisible = false;
        focused = false;
        // Pass blur notification to parent for side effects
        if (handleBlur) {
            handleBlur();
        }
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
            const height = suggestionsElement?.offsetHeight ?? 0;
            top = inputRect.top + window.scrollY - height - 5;
        }

        portalStyle = {
            top: `${top}px`,
            left: `${left}px`,
            width: `${dropdownWidth}px`,
            maxHeight: `${maxHeight}px`,
        };
    }

    // Recalculate portal position on suggestions show and window resize
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
        if (!suggestionsVisible && currentSelection) {
            inputText = currentSelection.scientificName;
        }
    });

    onMount(() => {
        if (autoFocus) {
            inputElement.focus();
            focused = true;
        }
    });
</script>

<div class="search-wrapper" class:focused>
    <input
        class="taxon-search"
        type="text"
        bind:value={inputText}
        bind:this={inputElement}
        oninput={debounceSearchSuggest}
        {placeholder}
        onblur={handleBlurInternal}
        onkeydown={handleInputKeydown}
        onfocus={() => (focused = true)}
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
                                    class="scientific-name-wrapper"
                                >
                                    <span
                                        class={[
                                            'scientific-name',
                                            { italicized },
                                        ]}>{suggestion.scientificName}</span
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
        padding: 0;
        margin: 0 0.5rem;
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
        /* min-height: 1.75rem; */
        max-height: 2.5rem;
        position: relative;
        flex-grow: 1;
        align-items: center;
        box-sizing: border-box;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .search-wrapper.focused {
        border: 1px solid var(--fill-color);
    }
    input {
        outline: none;
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
    .loading-icon {
        color: var(--fill-color);
        margin: auto;
        padding: 0.5rem;
    }
    .taxon-search {
        min-height: 1.75rem;
        height: 100%;
        min-width: 100px;
        width: 100%;
        color: var(--text-default);
        background-color: transparent;
        border: unset;
        border-radius: 3px;
        padding: 0 2.5rem 0 0.75rem;
        box-sizing: border-box;
        text-overflow: ellipsis;
        overflow: hidden;
        /* margin: 0; */
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
        background-color: var(--container-back);
        overflow: visible;
        /* border-radius: 4px; */
        width: fit-content;
        max-width: 350px;
        overflow-y: scroll;
        border: 1px solid var(--container-shadow);
        box-shadow: 0px 3px 10px 1px var(--container-shadow);
        box-sizing: border-box;
        z-index: 8000;
    }
    .autocomplete-suggestions {
        padding: 0;
        margin: 0;
    }
</style>
