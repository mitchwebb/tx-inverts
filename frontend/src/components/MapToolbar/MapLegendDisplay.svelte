<!-- 
    @component
    - Color-coded display for map legend for a given feature property
    - Uses mapContext to highlight active features
 -->

<script lang="ts">
    import type {
        Color,
        LegendFeatureProperty,
        LegendFeatureValue,
    } from '../../constants/mapLegendKeys';
    import { getMapContext } from '../../contexts/mapContext';
    import type {
        StaticMapLayerSource,
        StaticMapSourceLayer,
    } from '../../lib/map/mapLayers';

    type MapLegendProps = {
        targetProp: LegendFeatureProperty;
        source: StaticMapLayerSource;
        sourceLayer: StaticMapSourceLayer;
        colorKey: [string, Color][];
    };

    let { colorKey, targetProp, source, sourceLayer }: MapLegendProps =
        $props();

    const mapContext = getMapContext();

    // If there are any hovered features in context, get them here
    const relevantProperties = $derived.by(() => {
        const relevantFeatures = mapContext.hoveredFeatures?.filter(
            (f) => f.source === source
        );

        return relevantFeatures
            ?.map((f) => f.properties[targetProp])
            .filter((v): v is LegendFeatureValue => v != null);
    });

    function handleHover(e: MouseEvent) {
        const target = e.target as HTMLElement;
        if (target) {
            const value = target.dataset.featureProperty;
            mapContext.hoveredLegendInfo = [
                {
                    source,
                    sourceLayer,
                    properties: {
                        [targetProp]: value,
                    },
                },
            ];
        }
    }

    function clearHover() {
        mapContext.hoveredFeatures = null;
    }
</script>

<div class="map-legend-section">
    {#snippet legendItem(value: LegendFeatureValue, color: string)}
        <div
            class="legend-item"
            class:active={relevantProperties?.includes(value)}
            data-feature-property={value}
            role="region"
            onmouseenter={handleHover}
            onmouseleave={clearHover}
        >
            <span class="legend-color" style="background-color: {color}"></span>
            <span class="legend-label">{value}</span>
        </div>
    {/snippet}
    {#each colorKey as field}
        {@render legendItem(field[0] as LegendFeatureValue, field[1])}
    {/each}
</div>

<style>
    .legend-item.active {
        font-weight: 600;
    }
    .legend-item:hover {
        font-weight: 600;
    }
    .legend-color {
        width: 20px;
        height: 20px;
        display: inline-block;
        margin-right: 10px;
        border-radius: 3px;
        flex-shrink: 0;
    }
    .legend-item {
        display: flex;
        align-items: center;
        justify-content: left;
        font-size: 0.75rem;
    }
    .legend-label {
        text-align: left;
        text-wrap: nowrap;
    }
    .map-legend-section {
        display: flex;
        flex-direction: column;
        gap: 2px;
        overflow-y: auto;
        overflow-x: hidden;
        flex: 1;
        height: 100%;
        box-sizing: border-box;
    }
</style>
