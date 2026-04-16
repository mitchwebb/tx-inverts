<!-- 
    @component
    - Foldout section for displaying map layer information
    - Facilitates toggling of given layerID
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import {
        type StaticLayerGroupID,
        type StaticMapLayerID,
    } from '../../lib/map/mapLayers';
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import { getMapContext } from '../../contexts/mapContext';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import ChevronUp from '../../assets/ChevronUp.svelte';
    import ChevronDown from '../../assets/ChevronDown.svelte';
    import { slide } from 'svelte/transition';
    import { stopPropagation } from 'svelte/legacy';

    type MapLegendFoldoutProps = {
        label: string;
        layerID: StaticMapLayerID | StaticLayerGroupID;
        handler: (payload: CheckboxPayload) => void;
        children?: Snippet;
        defaultOpen?: boolean;
        foldout?: boolean;
    };

    let {
        label,
        layerID,
        handler,
        children,
        defaultOpen = false,
        foldout = true,
    }: MapLegendFoldoutProps = $props();

    let open = $derived(defaultOpen);

    const mapContext = getMapContext();

    const layerIDs = $derived(
        mapContext.layerGroups[layerID as StaticLayerGroupID] || [layerID]
    );

    const layerActive = $derived(
        layerIDs.every((id) => mapContext.activeLayers.includes(id))
    );

    function handleClick(payload: CheckboxPayload) {
        payload.e.stopPropagation();
        handler(payload);
    }

    function handleFoldout() {
        if (!foldout) return;
        open = !open;
    }
</script>

<div class={['map-key-foldout', { open }]}>
    <div
        role="button"
        tabindex="0"
        aria-expanded={open}
        aria-controls="foldout-content-{layerID}"
        class="map-key-foldout-header map-key-header map-key-section"
        class:has-foldout={foldout}
        onclick={handleFoldout}
        onkeydown={(e) =>
            (e.key === 'Enter' || e.key === ' ') && (open = !open)}
    >
        <span class="map-key-header-left">
            <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
            <span
                class="map-key-header-checkbox"
                onclick={(e) => e.stopPropagation()}
            >
                <CheckboxInput
                    name="layers"
                    value={layerID}
                    checked={layerActive}
                    handler={handleClick}
                />
            </span>
            <span> {label} </span>
        </span>
        {#if foldout}
            <span class="map-key-header-icons icon">
                {#if open}
                    <ChevronUp />
                {:else}
                    <ChevronDown />
                {/if}
            </span>
        {/if}
    </div>
    {#if foldout && open}
        <div
            id="foldout-content-{layerID}"
            class="map-key-foldout-content"
            transition:slide
        >
            {@render children?.()}
        </div>
    {/if}
</div>

<style>
    .map-key-header-checkbox {
        height: fit-content;
        box-sizing: border-box;
        pointer-events: none;
    }
    .map-key-header-left {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    @keyframes loading-blink {
        0% {
            opacity: 100%;
        }
        50% {
            opacity: 75%;
        }
        100% {
            opacity: 100%;
        }
    }
    :global(.map-key-header-icons > .ns-circle) {
        height: 2rem !important;
        width: 2rem !important;
    }
    .map-key-header-icons {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        flex-shrink: 0;
        gap: 0.75rem;
    }
    .map-key-foldout-header {
        outline: none;
        border: none;
        text-align: left;
        display: flex;
        justify-content: space-between;
        align-items: center;
        line-height: 1rem;
        color: var(--text-default);
        background-color: transparent;
        width: 100%;
        border-radius: 0;
        padding: 0.5rem;
        box-sizing: border-box;
        gap: 0.5rem;
        min-height: 2.5rem;
    }
    .map-key-foldout:not(:last-child) > .map-key-foldout-header,
    .map-key-foldout.open > .map-key-foldout-header {
        border-bottom: 1px solid var(--border);
    }
    .map-key-foldout-header.has-foldout:hover {
        cursor: pointer;
        background-color: var(--container-mid);
        user-select: none;
    }
    .map-key-foldout-header.has-foldout:active {
        background-color: var(--container-mid);
    }
    .map-key-foldout {
        background-color: var(--container-fore);
        transition: opacity 0.2s ease-in-out;
        box-sizing: border-box;
        max-height: 100%;
    }
    .map-key-foldout-content {
        display: block;
        background-color: var(--container-back);
        padding: 1rem;
        color: var(--text-default);
        border-bottom: 1px solid var(--border);
        overflow-y: auto;
        max-height: 200px;
    }
</style>
