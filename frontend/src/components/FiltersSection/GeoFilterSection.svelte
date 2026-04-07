<script lang="ts">
    import type { Tracing } from 'trace_events';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import GeoSearch from '../GeoSearch.svelte';
    import XIcon from '../../assets/XIcon.svelte';
    import SearchbarCard from '../../common/SearchbarCard.svelte';

    const filtersContext = getFiltersContext();

    type CountySuggestion = {
        'id': string,
        'county': string
    }

    // TODO: Make raw type
    type RawParkSuggestion = {
        'id': string,
        'prop_name': string,
        'alt_prop_name': string,
        'prop_class': string,
        'owner': string
    }

    type ParkSuggestion = {
        'id': string,
        'propName': string,
        'altPropName': string,
        'propClass': string,
        'owner': string
    }

    function parseCounties(json: CountySuggestion[]) {
        return json.map((result: CountySuggestion) => {
            return {
                id: result.id,
                county: result.county
            };
        });
    }

    function handleCountySelect(suggestion: CountySuggestion) {
        if (!suggestion.id) return;
        filtersContext.region.add({
            id: suggestion.id,
            name: suggestion.county,
            regionType: 'county'
        })
    }

    function parseParks(json: RawParkSuggestion[]): ParkSuggestion[] {
        return json.map((result: RawParkSuggestion) => {
            return {
                id: result.id,
                propName: result.prop_name,
                altPropName: result.alt_prop_name, 
                propClass: result.prop_class,
                owner: result.owner,
            }
        })
    }

    function handleParksSelect(suggestion: ParkSuggestion) {
        if (!suggestion.id) return;
        filtersContext.region.add({
            id: suggestion.id,
            name: suggestion.propName,
            regionType: 'park'
        })
    }

    function handleRemoveRegion(id: string | null) {
        if (!id) return;
        filtersContext.region.remove(id);
    }
</script>

{#snippet countyRow(suggestion: CountySuggestion)}
    <div>
        {suggestion.county}
    </div>
{/snippet}

{#snippet parkRow(suggestion: ParkSuggestion)}
    <div class='park-suggestion-row'>
        <span class='prop-name'>{suggestion.propName}</span>
        <div class='alt-prop-text'>
            {#if suggestion.altPropName && suggestion.altPropName.trim()}
                <span class='alt-prop-name thin'>{suggestion.altPropName}</span>
            {/if}
            <span class='park-owner thin'>{suggestion.owner}</span>
        </div>
    </div>
{/snippet}

<div
    class="geographic-filter filters-section"
>
    <div class="filters-section-header">Regions Found</div>
    <div id="geo-filters" class="filters-section-content">
        <div class="geo-filters-item filters-section" class:active={filtersContext.region.items.some((r) => r.regionType === "county")}>
            <span> County </span>
            <GeoSearch 
                placeholder="Search counties..." 
                pathSuffix="counties"
                parseJSON={parseCounties} 
                suggestionRow={countyRow} 
                handleSelect={handleCountySelect}/>
            <div class='county-cards'>
                {#each filtersContext.region.items.filter((r) => r.regionType === 'county') as county}
                    <SearchbarCard label={county.name} value={county.id} handleRemoveCard={handleRemoveRegion}/>
                {/each}
            </div>
        </div>
        <div class="geo-filters-item filters-section" class:active={filtersContext.region.items.some((r) => r.regionType === "park")}>
            <span> Park </span>
            <GeoSearch 
                placeholder="Search parks..."
                pathSuffix="parks"
                parseJSON={parseParks}
                suggestionRow={parkRow}
                handleSelect={handleParksSelect}
                />
            <div class="parks-cards">
                {#each filtersContext.region.items.filter((r) => r.regionType === 'park') as park}
                    <SearchbarCard label={park.name} value={park.id} handleRemoveCard={handleRemoveRegion}/>
                {/each}
            </div>
        </div>
    </div>
</div>

<style>
    .county-cards, .parks-cards {
        display: flex;
        flex-direction: column;
        gap: .25rem;
        width: 100%;
        max-width: 250px;
    }
    .prop-name {
        grid-row: 1;
        grid-column: 1/3;
        font-size: .9rem;
        flex-shrink: 1;
        min-width: 0;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
    }
    .alt-prop-name {
        flex-shrink: 1;
        min-width: 0;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
    }
    .park-suggestion-row {
        display: grid;
        grid-template-columns: auto auto;
        grid-template-rows: auto auto;
        width: 100%;
        justify-content: space-between;
    }
    .alt-prop-text {
        display: flex;
        grid-row: 2;
        grid-column: 1/3;
        justify-content: space-between;
        font-style: italic;
        font-size: .8rem;
        width: 100%;
        gap: .5rem;
    }
    #geo-filters {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .geo-filters-item {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: .5rem;
        width: 100%;
    }
</style>
