<script lang="ts">
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DatePicker, {
        type AirDatepickerPayload,
    } from '../../common/DatePicker.svelte';
    import { isMobile } from '../../contexts/device';

    type DateFilterProps = {
        header?: string;
    };

    const { header = 'Dates' }: DateFilterProps = $props();

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxaContext();

    function handleStartDate({ formattedDate }: AirDatepickerPayload) {
        filtersContext.dateStart = (formattedDate as string) || null;
    }

    function handleEndDate({ formattedDate }: AirDatepickerPayload) {
        filtersContext.dateEnd = (formattedDate as string) || null;
    }

    function getTaxonDates(type: 'dateMin' | 'dateMax') {
        return Object.values(taxonContext.taxa)
            .map((t) => t[type])
            .filter((d): d is string => d !== null)
            .map((d) => new Date(d).getTime());
    }

    const minDate = $derived(
        getTaxonDates('dateMin').length
            ? new Date(Math.min(...getTaxonDates('dateMin')))
            : undefined
    );

    const maxDate = $derived(
        getTaxonDates('dateMax').length
            ? new Date(Math.max(...getTaxonDates('dateMax')))
            : undefined
    );

    // TODO: Once we add mobile support, AirDatepicker has an isMobile arg
</script>

<div
    class="date-filters-section filters-section"
    class:active={filtersContext.dateStart || filtersContext.dateEnd}
>
    <div class="filters-section-header">
        <span>{header}</span>
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
                placeholder={minDate
                    ? `${minDate.toLocaleDateString()} (Min Date)`
                    : 'Min Date'}
                isMobile={$isMobile}
            />
            <span> to </span>
            <DatePicker
                onSelect={handleEndDate}
                id="date-end-filter"
                startDate={maxDate}
                {maxDate}
                buttons={'clear'}
                value={filtersContext.dateEnd}
                placeholder={maxDate
                    ? `${maxDate.toLocaleDateString()} (Max Date)`
                    : 'Max Date'}
                isMobile={$isMobile}
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
        align-items: center;
        gap: 1rem;
    }
</style>
