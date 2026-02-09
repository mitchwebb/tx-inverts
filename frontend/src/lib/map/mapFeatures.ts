import type { FeatureSelector, GeoJSONFeature, Map } from 'mapbox-gl';
import type {
    HoveredFeatureInfo,
    HoveredLegendInfo,
} from '../../contexts/mapContext';

export function clearTargetFeatures(
    map: mapboxgl.Map,
    targetArray: HoveredFeatureInfo[] | GeoJSONFeature[] | FeatureSelector[],
    condition: 'hover' | 'selected'
) {
    if (targetArray.length) {
        for (const feature of targetArray) {
            if (
                feature?.source &&
                map.getSource(feature.source) &&
                feature?.id != null
            ) {
                map.setFeatureState(
                    {
                        source: feature.source,
                        sourceLayer: feature.sourceLayer,
                        id: feature.id,
                    },
                    { [condition]: false }
                );
            }
        }
        // Clear targetArray
        targetArray.length = 0;
    }
}

export function highlightMatchingFeatures(
    map: Map,
    hoveredFeatures: FeatureSelector[],
    source: string,
    sourceLayer: string,
    property: string,
    value: unknown
) {
    // Query all features in the source + sourceLayer
    const allFeatures = map.querySourceFeatures(source, { sourceLayer });
    console.log(source, sourceLayer, property, value);

    for (const feature of allFeatures) {
        // Skip features without an ID
        if (!feature.id) continue;

        // Only highlight features that match the given property value
        if (feature.properties?.[property] === value) {
            const featureDef = {
                source,
                sourceLayer,
                id: feature.id,
            };

            hoveredFeatures.push(featureDef);
            map.setFeatureState(featureDef, { hover: true });
        }
    }
}

export function handleLegendHover(
    map: Map,
    hoveredFeatures: FeatureSelector[],
    hoveredLegendInfo: HoveredLegendInfo[] | null
) {
    if (!hoveredLegendInfo) return;

    for (const hovered of hoveredLegendInfo) {
        const { source, sourceLayer, properties } = hovered;

        for (const [property, value] of Object.entries(properties)) {
            if (value == null) continue;

            highlightMatchingFeatures(
                map,
                hoveredFeatures,
                source,
                sourceLayer,
                property,
                value
            );
        }
    }
}
