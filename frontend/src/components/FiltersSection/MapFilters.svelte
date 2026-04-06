<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import FiltersWrapper from './FiltersWrapper.svelte';
    import INatFilterSection from './INatFilterSection.svelte';
    import './filtersSection.css';
</script>

<FiltersWrapper header={'Filter Occurrences'}>
    <div id='filters-top-section'>
        <INatFilterSection />
        <DateFilterSection header="Date Range" />
    </div>
    <DatasetFilterSection />
</FiltersWrapper>

<style>
    #filters-top-section {
        display: flex;
        gap: .5rem;
        width: 100%;
    }
</style>
