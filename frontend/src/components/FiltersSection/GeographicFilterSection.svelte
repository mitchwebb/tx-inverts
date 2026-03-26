<script lang="ts">
    import { getFiltersContext } from '../../contexts/filtersContext';

    const filtersContext = getFiltersContext();
</script>

<div
    class="geographic-filter filters-section"
    class:active={!!filtersContext.nSRanks?.length}
></div>

<style>
</style>
