<script lang="ts">
    import Map from '../../components/Map/Map.svelte';
    import MapOverlay from '../../components/MapOverlay.svelte';
    import {
        setMapHoverContext,
        type MapHoverFormattedData,
    } from '../../contexts/mapHoverContext';

    const mapHoverState: MapHoverFormattedData = $state({
        lnglat: [null, null],
        hoveredProps: null,
    });
    setMapHoverContext(mapHoverState);
</script>

<div id="map-page">
    <Map />
    <MapOverlay />
</div>

<style>
    #map-page {
        min-height: 450px;
        height: 100%;
        width: 100%;
        position: relative;
        overflow: hidden;
    }
</style>
