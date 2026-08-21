<script lang="ts">
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import SearchbarCard from '../../common/SearchbarCard.svelte';
    import type { FiltersDomain } from '../../constants/sidebarFilters';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { isItalicizedRank } from '../../util/taxa';
    import TaxaSearch from '../TaxaSearch.svelte';

    type TaxonFilterProps = {
        domain: FiltersDomain;
        header?: string;
        excludeSpecies?: boolean; // Determines whether or not to exclude species and below
    };

    const {
        domain,
        header = 'Selected Taxa',
        excludeSpecies = false,
    }: TaxonFilterProps = $props();

    const taxaContext = getActiveTaxaContext();

    function handleRemoveTaxon(taxonID: string | null) {
        if (!taxonID) return;
        taxaContext.taxa.remove(Number(taxonID));
    }

    const higherTaxaActive = $derived(
        taxaContext.taxa.ids.some((id) => {
            const taxon = taxaContext.taxa.get(id);
            const taxonRank = taxon?.info.taxonRank;
            return taxonRank && !['species', 'subspecies'].includes(taxonRank);
        })
    );
</script>

<div
    class="taxon-filter filters-section"
    class:active={domain === 'taxa' ? higherTaxaActive : false}
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
                            <div class="taxon-card-label">
                                {#if taxon.taxonLoading}
                                    <div class="taxon-loading">
                                        <LoadingIcon />
                                    </div>
                                {/if}
                                <div class="filtered-taxon-name">
                                    <span class:italicized={isItalicized}
                                        >{taxonInfo.canonicalName}</span
                                    >
                                    <div class="filtered-taxon-authorship thin">
                                        {taxon.info.scientificNameAuthorship}
                                    </div>
                                </div>
                            </div>
                        {/snippet}
                        <SearchbarCard
                            {label}
                            tintColor={taxon.color}
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
    .taxon-card-label {
        display: flex;
        width: 100%;
        height: 100%;
    }
    .taxon-loading {
        height: 1rem;
        display: flex;
        align-items: center;
    }
    .taxa-search-wrapper {
        height: 2.5rem;
    }
    .italicized {
        font-style: italic;
    }
    #taxon-cards-wrapper {
        display: flex;
        flex-direction: column;
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
        height: fit-content;
    }
    .taxon-filter {
        width: 100%;
        min-width: 250px;
        flex-basis: 75%;
    }
</style>
