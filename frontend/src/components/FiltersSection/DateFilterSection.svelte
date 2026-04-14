<script lang="ts">
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DatePicker, {
        type AirDatepickerPayload,
    } from '../../common/DatePicker.svelte';
    import { isMobile } from '../../contexts/device';
    import type { FilterDomain } from '../../constants/sidebarFilters';

    type DateFilterProps = {
        domain?: FilterDomain; // Determines min/max behavior
        header?: string;
    };

    const { domain = 'observations', header = 'Date Range' }: DateFilterProps =
        $props();

    const filtersContext = getFiltersContext();
    const taxonContext = getActiveTaxaContext();

    function handleStartDate({ date, datepicker }: AirDatepickerPayload) {
        const singleDate = Array.isArray(date) ? date[0] : date;
        datepicker.hide();
        // Do not update context if date is identical
        if (singleDate?.getTime() === filtersContext.dateStart?.getTime())
            return;
        filtersContext.dateStart = singleDate || null;
    }

    function handleEndDate({ date, datepicker }: AirDatepickerPayload) {
        const singleDate = Array.isArray(date) ? date[0] : date;
        datepicker.hide();
        // Do not update context if date is identical
        if (singleDate?.getTime() === filtersContext.dateEnd?.getTime()) return;
        filtersContext.dateEnd = singleDate || null;
    }

    // Get all min or max dates from activeTaxa, return Date[]
    function getTaxonDates(type: 'dateMin' | 'dateMax') {
        return Object.values(taxonContext.taxa.items)
            .map((t) => t[type])
            .filter((d): d is Date => d !== null);
    }

    // Derive minDate using all activeTaxa minDates
    const minDate = $derived.by(() => {
        if (domain === 'taxa') return undefined;
        return getTaxonDates('dateMin').sort((a, b) => (a > b ? 1 : -1))[0];
    });

    // Derive maxDate using all activeTaxa maxDates
    const maxDate = $derived.by(() => {
        if (domain === 'taxa') return undefined;
        return getTaxonDates('dateMax').sort((a, b) => (a < b ? 1 : -1))[0];
    });

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
                value={filtersContext.dateStart}
                placeholder={minDate
                    ? `${minDate.toLocaleDateString()} (Min Date)`
                    : 'Min Date'}
                isMobile={$isMobile}
                position="bottom right"
                buttons="clear"
            />
            <span>to</span>
            <DatePicker
                onSelect={handleEndDate}
                id="date-end-filter"
                startDate={maxDate}
                {maxDate}
                value={filtersContext.dateEnd}
                placeholder={maxDate
                    ? `${maxDate.toLocaleDateString()} (Max Date)`
                    : 'Max Date'}
                isMobile={$isMobile}
                position="bottom right"
                buttons="clear"
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
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    :global(#date-start-filter),
    :global(#date-end-filter) {
        max-width: 200px;
        flex: 1 1 75px;
    }
    :global(.date-filters-wrapper input) {
        height: 2.5rem;
        box-sizing: border-box;
    }
</style>
