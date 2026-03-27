<script lang="ts">
    import { getFiltersContext } from '../../contexts/filtersContext';
    import GeoSearch from '../GeoSearch.svelte';

    const filtersContext = getFiltersContext();
</script>

<div
    class="geographic-filter filters-section"
    class:active={!!filtersContext.nSRanks?.length}
>
    <div class="filters-section-header">Region</div>
    <div id="geo-filters" class="filters-section-content">
        <div class="geo-filters-item">
            <span> County </span>
            <GeoSearch placeholder="Search counties..."/>
        </div>
        <div class="geo-filters-item">
            <span> Parks </span>
            <GeoSearch placeholder="Search parks..."/>
        </div>
    </div>
</div>

<style>
    #geo-filters {
        display: flex;
        flex-direction: column;
        gap: .5rem;
    }
    .geo-filters-item {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: .5rem;
    }
</style>
