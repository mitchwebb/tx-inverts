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

    const { header = 'Date Range' }: DateFilterProps = $props();

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxaContext();

    function handleStartDate({ date }: AirDatepickerPayload) {
        const singleDate = Array.isArray(date) ? date[0] : date;
        filtersContext.dateStart = singleDate || null;
    }

    function handleEndDate({ date }: AirDatepickerPayload) {
        const singleDate = Array.isArray(date) ? date[0] : date;
        filtersContext.dateEnd = singleDate || null;
    }

    // Get all min or max dates from activeTaxa, return Date[]
    function getTaxonDates(type: 'dateMin' | 'dateMax') {
        return Object.values(taxonContext.taxa.items)
            .map((t) => t[type])
            .filter((d): d is Date => d !== null);
    }

    // Derive minDate using all activeTaxa minDates
    const minDate = $derived(
        getTaxonDates('dateMin').sort((a, b) => (a > b ? 1 : -1))[0]
    );

    // Derive maxDate using all activeTaxa maxDates
    const maxDate = $derived(
        getTaxonDates('dateMax').sort((a, b) => (a < b ? 1 : -1))[0]
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
            <span>to</span>
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
        gap: .5rem;
        flex-wrap: wrap;
    }
    :global(#date-start-filter), :global(#date-end-filter) {
        max-width: 200px;
        flex: 1 1 75px;
    }
</style>
