<!--
    @component
    - Foldout component to be used with Sidebar
-->
<script lang="ts">
    import { onMount, type Snippet } from 'svelte';
    import ChevronDown from '../../assets/ChevronDown.svelte';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import ChevronUp from '../../assets/ChevronUp.svelte';
    import { slide } from 'svelte/transition';
    import { getSidebarContext } from '../../contexts/sidebarContext';

    const sidebarContext = getSidebarContext();

    type SidebarFoldoutProps = {
        id: string; // Required for setting foldoutState
        label: string;
        closedDisplay?: Snippet;
        children?: Snippet;
        defaultOpen?: boolean;
        isLoading?: boolean;
        customClass?: string;
    };

    let {
        id,
        label,
        closedDisplay,
        children,
        defaultOpen = false,
        isLoading = false,
        customClass = '',
    }: SidebarFoldoutProps = $props();

    let open = $derived(sidebarContext.foldoutStates[id] === true);

    function handleKey(e: KeyboardEvent) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleFoldoutState();
        }
    }

    // Toggle foldout state in context
    function toggleFoldoutState() {
        sidebarContext.foldoutStates[id] = !open;
    }

    // On mount, set foldout state in context
    onMount(() => {
        if (!(id in sidebarContext.foldoutStates)) {
            sidebarContext.foldoutStates[id] = defaultOpen;
        }
    });
</script>

<div
    {id}
    class={['sidebar-foldout', { open }, customClass]}
    class:loading-blink={isLoading}
>
    <div
        role="button"
        tabindex="0"
        aria-expanded={open}
        class={['sidebar-foldout-header', { open }]}
        onclick={toggleFoldoutState}
        onkeydown={handleKey}
    >
        <div class="foldout-header-main sidebar-header">
            <span class="sidebar-header-text">
                {label}
            </span>
            <span class="sidebar-header-icons">
                {#if closedDisplay && !open}
                    {@render closedDisplay()}
                {/if}

                <span class="sidebar-icon icon">
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
    </div>
    {#if open}
        <div class="sidebar-foldout-content" transition:slide>
            {@render children?.()}
        </div>
    {/if}
</div>

<style>
    .foldout-header-main {
        text-align: left;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--text-default);
        background-color: transparent;
        width: 100%;
        box-sizing: border-box;
    }
    .foldout-header-banner {
        width: 100%;
    }
    .sidebar-header-text {
        font-size: 1.2rem;
    }
    :global(.sidebar-header-icons > .ns-circle) {
        height: 2rem !important;
        width: 2rem !important;
    }
    .sidebar-header-icons {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        flex-shrink: 0;
        gap: 0.5rem;
        height: 1.5rem;
    }
    :global(.sidebar-header-icons > svg) {
        flex-shrink: 0;
    }
    .sidebar-foldout-header {
        position: relative;
        display: flex;
        flex-direction: column;
        /* border-bottom: 1px solid transparent; */
    }
    .sidebar-foldout-header.open {
        border-bottom: 1px solid var(--border);
    }
    .sidebar-foldout-header:hover {
        cursor: pointer;
        background-color: var(--container-fore);
        user-select: none;
    }
    .sidebar-foldout-header:active {
        background-color: var(--container-mid);
    }
    .sidebar-foldout {
        width: 100%;
        background-color: var(--container-highlight);
        border: 1px solid var(--border);
        transition: opacity 0.2s ease-in-out;
        box-sizing: border-box;
    }
    .sidebar-foldout-content {
        display: block;
        background-color: var(--container-fore);
        padding: 0.75rem;
    }
</style>
