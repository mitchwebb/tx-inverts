<script lang="ts">
    import RangeInput from '../../common/RangeInput.svelte';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { getFiltersContext } from '../../contexts/filtersContext';

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxonContext();

    function handleDate(start: string | null, end: string | null) {
        filtersContext.dateStart = start;
        filtersContext.dateEnd = end;
    }
</script>

<div
    class="date-filters-section filters-section"
    class:active={filtersContext.dateStart || filtersContext.dateEnd}
>
    <div class="filters-section-header">
        <span>Dates</span>
    </div>
    <div class="filters-section-content">
        <RangeInput
            startValue={filtersContext.dateStart}
            endValue={filtersContext.dateEnd}
            type="date"
            handler={handleDate}
            customClass="date-range-filter"
            max={taxonContext.dateMax}
            min={taxonContext.dateMin}
        />
    </div>
</div>

<style>
    .date-filters-section {
        min-width: 275px;
    }
</style>
