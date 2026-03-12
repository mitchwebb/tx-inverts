<script lang="ts">
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DatePicker, {
        type AirDatepickerPayload,
    } from '../../common/DatePicker.svelte';

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxonContext();

    function handleStartDate({ formattedDate }: AirDatepickerPayload) {
        filtersContext.dateStart = (formattedDate as string) || null;
    }

    function handleEndDate({ formattedDate }: AirDatepickerPayload) {
        filtersContext.dateEnd = (formattedDate as string) || null;
    }

    const minDate = $derived(
        taxonContext.dateMin ? new Date(taxonContext.dateMin) : undefined
    );
    const maxDate = $derived(
        taxonContext.dateMax ? new Date(taxonContext.dateMax) : undefined
    );

    // TODO: Once we add mobile support, AirDatepicker has an isMobile arg
</script>

<div
    class="date-filters-section filters-section"
    class:active={filtersContext.dateStart || filtersContext.dateEnd}
>
    <div class="filters-section-header">
        <span>Dates</span>
    </div>
    <div class="filters-section-content">
        <div class="date-filters-wrapper">
            <DatePicker
                onSelect={handleStartDate}
                id="date-start-filter"
                startDate={minDate}
                {minDate}
                buttons={'clear'}
                value={filtersContext.dateStart}
                placeholder={`${minDate?.toLocaleDateString()} (Min Date)`}
            />
            <span> to </span>
            <DatePicker
                onSelect={handleEndDate}
                id="date-end-filter"
                startDate={maxDate}
                {maxDate}
                buttons={'clear'}
                value={filtersContext.dateEnd}
                placeholder={`${maxDate?.toLocaleDateString()} (Max Date)`}
            />
        </div>
    </div>
</div>

<style>
    .filters-section-header {
        width: 100%;
    }
    .date-filters-wrapper {
        display: flex;
        gap: 1rem;
    }
</style>
