<!--
    @component
    - General foldout component
-->
<script lang="ts">
    import { onMount, type Snippet } from 'svelte';
    import { slide } from 'svelte/transition';
    import LoadingIcon from '../assets/LoadingIcon.svelte';
    import ChevronUp from '../assets/ChevronUp.svelte';
    import ChevronDown from '../assets/ChevronDown.svelte';
    import { getSidebarContext } from '../contexts/sidebarContext';

    type FoldoutProps = {
        label: string;
        id?: string;
        openCallback?: (id: string | undefined, open: boolean) => void;
        closedDisplay?: Snippet;
        children?: Snippet;
        defaultOpen?: boolean;
        isLoading?: boolean;
        customClass?: string;
        bannerText?: string;
    };

    let {
        label,
        id,
        openCallback,
        closedDisplay,
        children,
        defaultOpen = false,
        isLoading = false,
        customClass = '',
        bannerText,
    }: FoldoutProps = $props();

    let open = $derived(defaultOpen);

    function handleKey(e: KeyboardEvent) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleFoldoutState();
        }
    }

    // Toggle foldout state in context
    function toggleFoldoutState() {
        open = !open;
        if (openCallback) openCallback(id, open);
    }
</script>

<div
    {id}
    class={['foldout', { open }, customClass]}
    class:loading-blink={isLoading}
>
    <div
        role="button"
        tabindex="0"
        aria-expanded={open}
        class={['foldout-header', { open }]}
        onclick={toggleFoldoutState}
        onkeydown={handleKey}
    >
        <span class="foldout-header-text">
            {label}
        </span>
        <span class="foldout-header-icons">
            {#if closedDisplay && !open}
                {@render closedDisplay()}
            {/if}

            <span class="foldout-icon icon">
                {#if isLoading}
                    <LoadingIcon />
                {:else if open}
                    <ChevronUp />
                {:else}
                    <ChevronDown />
                {/if}
            </span>
        </span>
    </div>
    {#if open}
        <div class="foldout-content-wrapper" transition:slide>
            {#if bannerText}
                <div class="banner-text">{bannerText}</div>
            {/if}
            <div class="foldout-content">
                {@render children?.()}
            </div>
        </div>
    {/if}
</div>

<style>
    .banner-text {
        background-color: var(--accent-color);
        color: black;
        font-size: 0.75rem;
        width: 100%;
        display: flex;
        justify-content: center;
        height: 1rem;
    }
    .foldout-header-text {
        font-size: 1.2rem;
    }
    :global(.foldout-header-icons > .ns-circle) {
        height: 2rem !important;
        width: 2rem !important;
    }
    .foldout-header-icons {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        flex-shrink: 0;
        gap: 0.5rem;
        height: 1.5rem;
    }
    :global(.foldout-header-icons > svg) {
        flex-shrink: 0;
    }
    .foldout-header {
        text-align: left;
        display: flex;
        flex-wrap: nowrap;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        color: var(--text-default);
        background-color: transparent;
        width: 100%;
        box-sizing: border-box;
        padding: 0.5rem;
    }
    .foldout-header.open {
        border-bottom: 1px solid var(--border);
    }
    .foldout-header:hover {
        cursor: pointer;
        background-color: var(--container-fore);
        user-select: none;
    }
    .foldout-header:active {
        background-color: var(--container-mid);
    }
    .foldout {
        width: 100%;
        background-color: var(--container-highlight);
        border: 1px solid var(--border);
        transition: opacity 0.2s ease-in-out;
        box-sizing: border-box;
    }
    .foldout-content {
        display: block;
        /* background-color: var(--container-fore); */
        padding: 0.75rem;
        position: relative;
    }
</style>
