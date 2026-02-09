<!-- 
    @component
    - Extra component for Ecoregions legend section
    - This section is a special case because of its nested structure
 -->

<script lang="ts">
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import {
        ecoregionsMap,
        type L3Ecoregion,
        type L4Ecoregion,
        type LegendFeatureValue,
    } from '../../constants/mapLegendKeys';
    import { getMapContext } from '../../contexts/mapContext';
    import type { LayerGroupID, MapLayerID } from '../../lib/map/mapLayers';
    import { handleLayerToggle } from '../../util/handleMapLayerToggle';
    import MapLegendDisplay from './MapLegendDisplay.svelte';
    import MapLegendFoldout from './MapLegendFoldout.svelte';

    const mapContext = getMapContext();

    function layerToggleHandler(payload: CheckboxPayload) {
        const layerID = payload.value as MapLayerID | LayerGroupID;
        const layerVisible = payload.checked as boolean;
        handleLayerToggle(mapContext, { layerID, layerVisible });
    }

    function l3LayerHoverHandler(e: MouseEvent | FocusEvent) {
        const target = e.target as HTMLElement;
        if (target) {
            mapContext.hoveredLegendInfo = [
                {
                    source: 'l3-ecoregions',
                    sourceLayer: 'tx_eco_l3-bsezyp',
                    properties: {
                        US_L3NAME: target.dataset.l3RegionName as L3Ecoregion,
                    },
                },
            ];
        }
    }

    // If there are any hovered features in context, get them here
    const l3Props = $derived.by(() => {
        const relevantFeatures = mapContext.hoveredFeatures?.filter(
            (f) => f.source === 'l3-ecoregions'
        );

        return relevantFeatures
            ?.map((f) => f.properties['US_L3NAME'])
            .filter((v): v is LegendFeatureValue => v != null);
    });

    function clearHover() {
        mapContext.hoveredFeatures = null;
    }
</script>

{#snippet ecoregionSection()}
    {@const l3Keys = Object.keys(ecoregionsMap) as L3Ecoregion[]}
    {#each l3Keys as l3RegionName}
        {@const l4ColorMap = Object.entries(ecoregionsMap[l3RegionName]) as [
            L4Ecoregion,
            string,
        ][]}
        <div class="ecoregion-legend-section">
            <div
                class={'l3-region-name'}
                class:active={l3Props?.includes(l3RegionName)}
                data-l3-region-name={l3RegionName}
                role="region"
                aria-label={l3RegionName}
                onmouseenter={l3LayerHoverHandler}
                onmouseleave={clearHover}
            >
                {l3RegionName}
            </div>
            <MapLegendDisplay
                targetProp="L4_KEY"
                colorKey={l4ColorMap}
                source="l4-ecoregions"
                sourceLayer="tx_eco_l4-1joalj"
            />
        </div>
    {/each}
{/snippet}

<MapLegendFoldout
    label="Ecoregions"
    layerID={'ecoregions-group'}
    handler={layerToggleHandler}
>
    <div id="ecoregion-legend-wrapper">
        {@render ecoregionSection()}
    </div>
</MapLegendFoldout>

<style>
    .l3-region-name:hover {
        font-weight: 600;
    }
    .ecoregion-legend-section {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .l3-region-name {
        text-align: left;
        margin-bottom: 0.25rem;
    }
    .l3-region-name.active {
        font-weight: bold;
    }
    #ecoregion-legend-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        overflow: auto;
        height: 100%;
        box-sizing: border-box;
    }
</style>
