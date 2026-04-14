<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import FiltersWrapper from './FiltersWrapper.svelte';
    import GeoFilterSection from './GeoFilterSection.svelte';
    import RankFilterSection from './RankFilterSection.svelte';
    import TaxonFilterSection from './TaxonFilterSection.svelte';
    import './filtersSection.css';
</script>

<FiltersWrapper header={'Filter Rankings Table'}>
    <div class="vertical-filter-group">
        <TaxonFilterSection
            domain="taxa"
            header="Parent Taxa"
            excludeSpecies={true}
        />
        <GeoFilterSection />
    </div>
    <div class="vertical-filter-group">
        <div class="date-filter-section">
            <DateFilterSection domain="taxa" header="Dates Present" />
        </div>
        <RankFilterSection />
    </div>
    <DatasetFilterSection domain="taxa" showCounts={false} />
</FiltersWrapper>

<style>
    .vertical-filter-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        flex: 1 1;
    }
</style>
