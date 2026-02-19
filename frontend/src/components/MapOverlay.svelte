<!-- 
    @component
    - Grid-style wrapper for map overlay
    - Includes map toolbar and sidebar
-->
<script lang="ts">
    import Sidebar from './Sidebar/Sidebar.svelte';
    import { getActiveTaxonContext } from '../contexts/activeTaxonContext';
    import { getSidebarContext } from '../contexts/sidebarContext';
    import MapToolbar from './MapToolbar/MapToolbar.svelte';

    // const mapHoverContext = getMapHoverContext();
    const sidebarContext = getSidebarContext();
    const taxonContext = getActiveTaxonContext();
</script>

<div
    id="map-overlay-wrapper"
    style:grid-template-columns={`1fr ${sidebarContext.width}px`}
>
    <MapToolbar />
    <!-- Sidebar only visible if taxon selected -->
    {#if taxonContext.taxonID}
        <Sidebar />
    {/if}
    <!-- {#if mapHoverContext.lnglat}
        <div id="lnglat-display-wrapper">
            <div id="lnglat-display">{mapHoverContext.lnglat.join(', ')}</div>
        </div>
    {/if} -->
</div>

<style>
    #map-overlay-wrapper {
        transition: background-color 0.5s;
        height: 100%;
        padding: 10px 10px 20px 10px;
        pointer-events: none; /* Prevents the overlay from blocking mouse events */
        display: grid;
        grid-template-rows: 33px 1fr;
        gap: 2px;
        position: relative;
        z-index: 2;
        box-sizing: border-box;
    }
</style>
