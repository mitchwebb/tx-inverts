<!-- 
    @component
    - Grid-style wrapper for map overlay
    - Includes map toolbar and sidebar
-->
<script lang="ts">
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import MapToolbar from '../MapToolbar/MapToolbar.svelte';
    import DefaultPage from '../../common/DefaultPage.svelte';
</script>

<div id="map-overlay-wrapper">
    <DefaultPage overlay={true}>
        <MapToolbar />
    </DefaultPage>
    <!-- {#if mapHoverContext.lnglat}
        <div id="lnglat-display-wrapper">
            <div id="lnglat-display">{mapHoverContext.lnglat.join(', ')}</div>
        </div>
    {/if} -->
</div>

<style>
    #map-overlay-wrapper {
        pointer-events: none; /* Prevents the overlay from blocking mouse events */
        position: relative;
        z-index: 2;
        box-sizing: border-box;
        height: 100%;
    }
</style>
