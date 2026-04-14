<!--
    @component
    - Toolbar for MapOverlay
-->
<script lang="ts">
    import LayersIcon from '../../assets/LayersIcon.svelte';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import ToolbarFoldoutButton from '../../common/ToolbarFoldoutButton.svelte';
    import { TexasParksColorStops } from '../../constants/mapLegendKeys';
    import { getMapContext } from '../../contexts/mapContext';
    import type {
        StaticLayerGroupID,
        StaticMapLayerID,
    } from '../../lib/map/mapLayers';
    import { handleLayerToggle } from '../../util/handleMapLayerToggle';
    import EcoregionLegend from './EcoregionLegend.svelte';
    import MapLegendDisplay from './MapLegendDisplay.svelte';
    import MapLegendFoldout from './MapLegendFoldout.svelte';

    const mapContext = getMapContext();

    function layerToggleHandler(payload: CheckboxPayload) {
        const layerID = payload.value as StaticMapLayerID | StaticLayerGroupID;
        const layerVisible = payload.checked as boolean;
        handleLayerToggle(mapContext, { layerID, layerVisible });
    }
</script>

<div id="map-toolbar-wrapper">
    <ToolbarFoldoutButton
        id="layers-menu"
        ariaLabel="Expand layers and legends menu"
        ButtonLabel={LayersIcon}
    >
        <MapLegendFoldout
            label="Counties"
            layerID="counties-group"
            handler={layerToggleHandler}
            foldout={false}
        ></MapLegendFoldout>
        <EcoregionLegend />
        <MapLegendFoldout
            label="Parks"
            layerID="parks"
            handler={layerToggleHandler}
        >
            <MapLegendDisplay
                targetProp="LegendClass"
                source="parks"
                sourceLayer="texas_parks"
                colorKey={TexasParksColorStops}
            />
        </MapLegendFoldout>
    </ToolbarFoldoutButton>
    {#if mapContext.loading}
        <div id="map-loading-icon" class="icon">
            <LoadingIcon />
        </div>
    {/if}
</div>

<style>
    :global(#map-toolbar-wrapper *) {
        pointer-events: all;
    }
    :global(#layers-menu) {
        height: 33px;
        width: 3.5rem;
        grid-row: 1/3;
        justify-content: left;
        pointer-events: none;
    }
    #map-toolbar-wrapper {
        height: 100%;
        width: 100%;
        grid-row: 1/3;
        grid-column: 1;
        user-select: none;
        pointer-events: none;
        z-index: 0;
        display: flex;
        gap: 1rem;
        height: max-content;
        align-items: center;
    }
    #map-toolbar-wrapper > * {
        z-index: 50;
        pointer-events: all;
    }
    #map-loading-icon {
        z-index: 50;
        color: var(--accent-color);
    }
</style>
