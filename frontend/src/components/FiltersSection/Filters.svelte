<!--
    @component
    - Variable component to house relevant filters
    - Uses URL pathname to determine which filters to show
-->
<script lang="ts">
    import type { FiltersDomain } from '../../constants/sidebarFilters';
    import DatasetFilterSection from './DatasetFilterSection.svelte';
    import DateFilterSection from './DateFilterSection.svelte';
    import FiltersWrapper from './FiltersWrapper.svelte';
    import GeoFilterSection from './GeoFilterSection.svelte';
    import RankFilterSection from './RankFilterSection.svelte';
    import TaxonFilterSection from './TaxonFilterSection.svelte';
    import UncertaintyFilterSection from './UncertaintyFilterSection.svelte';
    import './filtersSection.css';

    type TaxaFiltersProps = {
        domain: FiltersDomain;
        header?: string;
        includeButtons?: boolean;
    };

    const {
        domain,
        header = 'Filters',
        includeButtons = true,
    }: TaxaFiltersProps = $props();
</script>

<FiltersWrapper {header} {includeButtons}>
    <div class="vertical-filter-group">
        <TaxonFilterSection
            {domain}
            header="Selected Taxa"
            excludeSpecies={domain == 'taxa'}
        />
        <UncertaintyFilterSection />
        {#if domain == 'taxa'}
            <RankFilterSection />
        {/if}
    </div>
    <div class="vertical-filter-group">
        <div class="date-filter-section">
            <DateFilterSection {domain} header="Dates Present" />
        </div>
        <GeoFilterSection />
    </div>
    <div class="horizontal-filter-group">
        <DatasetFilterSection {domain} showCounts={domain == 'observations'} />
    </div>
</FiltersWrapper>

<style>
</style>
