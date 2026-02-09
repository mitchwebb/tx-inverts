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
    import type { LayerGroupID, MapLayerID } from '../../lib/mapLayers';
    import { handleLayerToggle } from '../../util/handleMapLayerToggle';
    import EcoregionLegend from './EcoregionLegend.svelte';
    import MapLegendDisplay from './MapLegendDisplay.svelte';
    import MapLegendFoldout from './MapLegendFoldout.svelte';

    const mapContext = getMapContext();

    function layerToggleHandler(payload: CheckboxPayload) {
        const layerID = payload.value as MapLayerID | LayerGroupID;
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
        z-index: 1000;
        pointer-events: all;
    }
    #map-loading-icon {
        z-index: 1000;
        color: goldenrod;
    }
</style>
