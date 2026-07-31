<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import FiltersWrapper from './FiltersWrapper.svelte';
    import TaxonFilterSection from './TaxonFilterSection.svelte';
    import UncertaintyFilterSection from './UncertaintyFilterSection.svelte';
    import './filtersSection.css';
</script>

<FiltersWrapper header={'Filter Occurrences'}>
    <div class="horizontal-filter-group">
        <TaxonFilterSection domain="observations" />
        <UncertaintyFilterSection />
        <DateFilterSection header="Date Range" />
    </div>
    <DatasetFilterSection domain="observations" />
</FiltersWrapper>

<style>
</style>
