<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import DateFilterSection from './DateFilterSection.svelte';
    import FiltersWrapper from './FiltersWrapper.svelte';
    import GeoFilterSection from './GeoFilterSection.svelte';
    import INatFilterSection from './INatFilterSection.svelte';
    import RankFilterSection from './RankFilterSection.svelte';
    import './filtersSection.css';
</script>

<FiltersWrapper header={'Filter Visible Taxa'}>
    <!-- <TaxonFilterSection /> -->
    <INatFilterSection/>
    <RankFilterSection />
    <GeoFilterSection/>
    <DateFilterSection header="Dates Found" />
</FiltersWrapper>

<style>
</style>
