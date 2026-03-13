<!-- 
    @component
    - Grid-style wrapper for map overlay
    - Includes map toolbar and sidebar
-->
<script lang="ts">
    import Sidebar from './Sidebar/Sidebar.svelte';
    import { getActiveTaxonContext } from '../contexts/activeTaxonContext';
    import MapToolbar from './MapToolbar/MapToolbar.svelte';

    const taxonContext = getActiveTaxonContext();
</script>

<div id="map-overlay-wrapper">
    <MapToolbar />
    <!-- Sidebar only visible if taxon selected -->
    {#if taxonContext.taxonID}
        <div id="map-sidebar-wrapper">
            <Sidebar />
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
    #map-sidebar-wrapper {
        /* max-height: fit-content; */
        height: fit-content;
        border-radius: 3px;
        background-color: var(--container-back);
        padding: 0.5rem;
        box-sizing: border-box;
        box-shadow: 0px 2px 4px 0px var(--container-shadow);
        grid-row: 1/3;
    }
</style>
