<script lang="ts">
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DatePicker, {
        type AirDatepickerPayload,
    } from '../../common/DatePicker.svelte';
    import { isMobile } from '../../contexts/device';
    import type { FiltersDomain } from '../../constants/sidebarFilters';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import DatesChart from '../../common/DatesChart.svelte';
    import { type ScriptableContext } from 'chart.js/auto';

    type DateFilterProps = {
        domain?: FiltersDomain; // Determines min/max behavior
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

    // Determine if observationsMetrics are loading for any taxa
    const dateRangesLoading = $derived(
        Object.values(taxonContext.taxa.items).some(
            (taxon) => taxon.dateRangeLoading
        )
    );

    // Collect all active dateCounts and compile lineChart definitions
    const allDateDatasets = $derived(
        taxonContext.taxa.items
            .filter((taxon) => {
                if (taxon.taxonLoading) return false;
                else return true;
            })
            .map((taxon) => {
                return {
                    // pointRadius: 0,
                    tension: 0.5,
                    borderColor: taxon.color,
                    backgroundColor: taxon.color,
                    data: taxon.dateCounts ?? [],
                    label: taxon.info.canonicalName || 'Missing Name',
                    pointRadius: (ctx: ScriptableContext<'line'>) => {
                        const value = ctx.parsed?.y;
                        return value === 0 ? 0 : 3; // 0 = no visible marker, 3 = default-ish size
                    },
                };
            })
    );
</script>

<div
    class="date-filters-section filters-section"
    class:active={filtersContext.dateStart || filtersContext.dateEnd}
    class:loading-blink={dateRangesLoading}
>
    <div class="filters-section-header">
        <span>{header}</span>
        {#if dateRangesLoading}
            <div class="loading-icon icon">
                <LoadingIcon />
            </div>
        {/if}
    </div>
    <div id="date-filters-section-content" class="filters-section-content">
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
                dateFormat="yyyy-MM-dd"
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
                dateFormat="yyyy-MM-dd"
            />
        </div>
        {#if taxonContext.taxa.ids.length && domain == 'observations'}
            <DatesChart
                title="Filtered Observations Per Month"
                data={allDateDatasets}
                legendPosition={'bottom'}
                chartID="date-counts-chart"
                min={filtersContext.dateStart?.toISOString() ||
                    minDate?.toISOString()}
                max={filtersContext.dateEnd?.toISOString() ||
                    maxDate?.toISOString()}
            />
        {/if}
    </div>
</div>

<style>
    #date-filters-section-content {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .date-filters-section {
        flex-basis: 25%;
    }
    .filters-section-header {
        width: 100%;
        display: flex;
        gap: 0.5rem;
    }
    .date-filters-wrapper {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        position: relative;
        font-size: 0.8rem;
        height: 100%;
    }
    :global(#date-start-filter),
    :global(#date-end-filter) {
        min-width: 125px;
        max-width: 200px;
        flex: 1 1 75px;
    }
    :global(.date-filters-wrapper input) {
        height: 2.5rem;
        box-sizing: border-box;
    }
</style>
