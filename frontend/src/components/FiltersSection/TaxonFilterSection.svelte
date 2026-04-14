<script lang="ts">
    import SearchbarCard from '../../common/SearchbarCard.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import { isItalicizedRank } from '../../util/taxa';
    import TaxaSearch from '../TaxaSearch.svelte';

    type TaxonFilterProps = {
        domain: 'taxa' | 'observations';
        header?: string;
        excludeSpecies?: boolean; // Determines whether or not to exclude species and below
    };

    const {
        domain,
        header = 'Selected Taxa',
        excludeSpecies = false,
    }: TaxonFilterProps = $props();

    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();

    function handleRemoveTaxon(taxonID: string | null) {
        if (!taxonID) return;
        taxaContext.taxa.remove(Number(taxonID));
    }
</script>

<div
    class="taxon-filter filters-section"
    class:active={domain === 'taxa'
        ? filtersContext.filterTaxonIDs.length
        : false}
>
    <div class="filters-section-header">{header}</div>
    <div class="filters-section-content">
        <div class="taxa-search-wrapper">
            <TaxaSearch {excludeSpecies} />
        </div>

        {#if !!taxaContext.taxa.ids.length}
            <div id="taxon-cards-wrapper">
                {#each taxaContext.taxa.items as taxon}
                    {@const taxonInfo = taxon.info}
                    {@const taxonRank = taxonInfo.taxonRank}
                    {@const isItalicized = isItalicizedRank(
                        taxonInfo.taxonRank
                    )}
                    <!-- If excluding species, leave out species and subspecies cards -->
                    {#if !excludeSpecies || (taxonRank && !['species', 'subspecies'].includes(taxonRank))}
                        {#snippet label()}
                            <div class="filtered-taxon-name">
                                <span class:italicized={isItalicized}
                                    >{taxonInfo.canonicalName}</span
                                >
                                <div class="filtered-taxon-authorship thin">
                                    {taxon.info.scientificNameAuthorship}
                                </div>
                            </div>
                        {/snippet}
                        <SearchbarCard
                            {label}
                            value={taxon.taxonID}
                            handleRemoveCard={handleRemoveTaxon}
                        />
                    {/if}
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .taxa-search-wrapper {
        height: 2.5rem;
    }
    .italicized {
        font-style: italic;
    }
    #taxon-cards-wrapper {
        display: flex;
        flex-direction: column;
        /* border-radius: 3px; */
        gap: 0.25rem;
        width: fit-content;
        width: 100%;
        box-sizing: border-box;
    }
    .filtered-taxon-name {
        display: flex;
        gap: 0.5rem;
        padding: 0.25rem;
    }
    .filters-section-content {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        max-width: 350px;
    }
    .taxon-filter {
        width: 100%;
        min-width: 250px;
    }
</style>
