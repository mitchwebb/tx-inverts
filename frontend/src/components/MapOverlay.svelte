<!-- 
    @component
    - Grid-style wrapper for map overlay
    - Includes map toolbar and sidebar
-->
<script lang="ts">
    import Sidebar from './Sidebar/Sidebar.svelte';
    import { getActiveTaxaContext } from '../contexts/activeTaxaContext';
    import MapToolbar from './MapToolbar/MapToolbar.svelte';

    const taxaContext = getActiveTaxaContext();
</script>

<div id="map-overlay-wrapper">
    <MapToolbar />
    <!-- Sidebar only visible if taxon selected -->
    {#if Object.keys(taxaContext.taxa).length}
        <div id="map-sidebar-positioner">
            <div id="map-sidebar-wrapper">
                <Sidebar />
            </div>
        </div>
    {/if}
    <!-- {#if mapHoverContext.lnglat}
        <div id="lnglat-display-wrapper">
            <div id="lnglat-display">{mapHoverContext.lnglat.join(', ')}</div>
        </div>
    {/if} -->
</div>

<style>
    #map-overlay-wrapper {
        grid-template-columns: 1fr auto;
        transition: background-color 0.5s;
        height: 100%;
        padding: 0.5rem 0.5rem 20px 0.5rem;
        pointer-events: none; /* Prevents the overlay from blocking mouse events */
        display: grid;
        grid-template-rows: 33px 1fr;
        /* gap: 2px; */
        position: relative;
        z-index: 2;
        box-sizing: border-box;
    }
    #map-sidebar-positioner {
        height: 100%;
        grid-row: 1/3;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }
    #map-sidebar-wrapper {
        /* height: fit-content; */
        flex-shrink: 1;
        max-height: 100%;
        border-radius: 3px;
        background-color: var(--container-back);
        padding: 0.5rem;
        box-sizing: border-box;
    }
</style>
