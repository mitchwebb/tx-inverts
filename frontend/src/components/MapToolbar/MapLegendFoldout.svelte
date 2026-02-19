<!-- 
    @component
    - Foldout section for displaying map layer information
    - Facilitates toggling of given layerID
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import {
        layerGroups,
        type LayerGroupID,
        type MapLayerID,
    } from '../../lib/map/mapLayers';
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import { getMapContext } from '../../contexts/mapContext';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import ChevronUp from '../../assets/ChevronUp.svelte';
    import ChevronDown from '../../assets/ChevronDown.svelte';

    type MapLegendFoldoutProps = {
        label: string;
        layerID: MapLayerID | LayerGroupID;
        handler: (payload: CheckboxPayload) => void;
        children?: Snippet;
        defaultOpen?: boolean;
    };

    let {
        label,
        layerID,
        handler,
        children,
        defaultOpen = false,
    }: MapLegendFoldoutProps = $props();

    let open = $state(defaultOpen);

    const mapContext = getMapContext();

    const layerIDs = $derived(
        layerGroups[layerID as LayerGroupID] || [layerID]
    );

    const layerActive = $derived(
        layerIDs.every((id) => mapContext.activeLayers.includes(id))
    );
</script>

<div class={['map-key-foldout', { open }]}>
    <div
        role="button"
        tabindex="0"
        aria-expanded={open}
        aria-controls="foldout-content-{layerID}"
        class="map-key-foldout-header map-key-header map-key-section"
        onclick={() => (open = !open)}
        onkeydown={(e) =>
            (e.key === 'Enter' || e.key === ' ') && (open = !open)}
    >
        <span class="map-key-header-left">
            <CheckboxInput
                name="layers"
                value={layerID}
                checked={layerActive}
                {handler}
            />
            <span>{label}</span>
        </span>
        <span class="map-key-header-icons icon">
            {#if open}
                <ChevronUp />
            {:else}
                <ChevronDown />
            {/if}
        </span>
    </div>
    {#if open}
        <div
            id="foldout-content-{layerID}"
            class="map-key-foldout-content"
        >
            {@render children?.()}
        </div>
    {/if}
</div>

<style>
    .map-key-header-left {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        vertical-align: middle;
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
        /* padding: unset; */
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
    }
    .map-key-foldout:not(:last-child) > .map-key-foldout-header,
    .map-key-foldout.open > .map-key-foldout-header {
        border-bottom: 1px solid var(--border);
    }
    .map-key-foldout-header:hover {
        cursor: pointer;
        background-color: var(--container-mid);
        user-select: none;
    }
    .map-key-foldout-header:active {
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
