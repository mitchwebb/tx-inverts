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

<FiltersWrapper domain="observation" header={'Filter Occurrences'}>
    <div class="horizontal-filter-group">
        <TaxonFilterSection domain="observation" />
        <UncertaintyFilterSection />
        <DateFilterSection header="Date Range" />
    </div>
    <DatasetFilterSection domain="observation" />
</FiltersWrapper>

<style>
</style>
