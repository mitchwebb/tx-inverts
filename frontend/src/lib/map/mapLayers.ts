import type { Layer } from 'mapbox-gl';
import {
    l3EcoregionsColorStops,
    l4EcoregionsColorStops,
    TexasParksColorStops,
} from '../../constants/mapLegendKeys';

export type LayerBundle = {
    id: string;
    source:
        | mapboxgl.VectorSourceSpecification
        | mapboxgl.GeoJSONSourceSpecification;
    layers: readonly Layer[];
    deferred?: boolean; // If true, layer initialization is left out of initial load
};

export const l4EcoregionsLayer = {
    id: 'l4-ecoregions',
    source: {
        type: 'vector',
        url: 'mapbox://mihtmo.a1utqz7l',
        promoteId: 'L4_KEY',
    },
    layers: [
        {
            id: 'l4-ecoregions',
            source: 'l4-ecoregions',
            type: 'fill',
            'source-layer': 'tx_eco_l4-1joalj',
            paint: {
                'fill-color': {
                    property: 'L4_KEY',
                    type: 'categorical',
                    stops: l4EcoregionsColorStops,
                },
                'fill-opacity': [
                    'case',
                    // ['boolean', ['feature-state', 'selected'], false],
                    // 0.7,
                    ['boolean', ['feature-state', 'hover'], false],
                    0.6,
                    0.2,
                ],
                'fill-outline-color': '#000000',
            },
        } as const,
    ] as const,
} as const satisfies LayerBundle;

export const l3EcoregionsLayer = {
    id: 'l3-ecoregions',
    source: {
        type: 'vector',
        url: 'mapbox://mihtmo.0f8lu7w6',
        promoteId: 'US_L3NAME',
    },
    layers: [
        {
            id: 'l3-ecoregions',
            source: 'l3-ecoregions',
            type: 'fill',
            'source-layer': 'tx_eco_l3-bsezyp',
            paint: {
                'fill-color': {
                    property: 'US_L3NAME',
                    type: 'categorical',
                    stops: l3EcoregionsColorStops,
                },
                'fill-opacity': [
                    'case',
                    // ['boolean', ['feature-state', 'selected'], false],
                    // 0.7,
                    ['boolean', ['feature-state', 'hover'], false],
                    0.8,
                    0.0,
                ],
                'fill-outline-color': '#000000',
            },
        } as const,
    ] as const,
} as const satisfies LayerBundle;

export const texasParksLayer = {
    id: 'parks',
    source: {
        type: 'vector',
        url: 'mapbox://mihtmo.a8sblcwq',
        promoteId: 'ManagerPropName',
    },
    layers: [
        {
            id: 'parks',
            source: 'parks',
            type: 'fill',
            'source-layer': 'texas_parks',
            paint: {
                'fill-color': {
                    property: 'LegendClass',
                    type: 'categorical',
                    stops: TexasParksColorStops,
                },
                'fill-opacity': [
                    'case',
                    // ['boolean', ['feature-state', 'selected'], false],
                    // 0.9,
                    ['boolean', ['feature-state', 'hover'], false],
                    0.7,
                    0.3,
                ],
                'fill-outline-color': '#000000',
            },
        } as const,
    ] as const,
} as const satisfies LayerBundle;

export const countiesLayer = {
    id: 'tx-counties',
    source: {
        type: 'vector',
        url: 'mapbox://mihtmo.4u7cu2jb',
        promoteId: 'COUNTY',
    },
    layers: [
        {
            id: 'counties-outline',
            source: 'tx-counties',
            type: 'line',
            'source-layer': 'tx_counties-25946r',
            paint: {
                'line-color': 'black',
                'line-width': [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    1,
                    0.5,
                ],
                'line-opacity': [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    1,
                    0.5,
                ],
            },
        } as const,
        {
            id: `counties-fill`,
            type: 'fill',
            source: 'tx-counties',
            'source-layer': 'tx_counties-25946r',
            paint: {
                'fill-color': 'black',
                'fill-opacity': [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    0.1,
                    0.0,
                ],
            },
        },
    ] as const,
} as const satisfies LayerBundle;

// TODO: This should be linked up with the API. Determine where to store value
export const observationsZoomCutoff: number = 10;

// Collect all static map layers in one place
export const staticMapLayers = [
    l3EcoregionsLayer,
    l4EcoregionsLayer,
    texasParksLayer,
    countiesLayer,
] satisfies LayerBundle[];

// Map layer source literal type
export type StaticMapLayerSource =
    (typeof staticMapLayers)[number]['layers'][number]['source'];

// Extract layers with source-layers for typing
type StaticLayerWithSourceLayer = Extract<
    (typeof staticMapLayers)[number]['layers'][number],
    { 'source-layer': string }
>;
// Map layer source-layer literal type
export type StaticMapSourceLayer = StaticLayerWithSourceLayer['source-layer'];

// Map layer id literal type
export type StaticMapLayerID =
    (typeof staticMapLayers)[number]['layers'][number]['id'];

export const staticMapLayerIDs: StaticMapLayerID[] = staticMapLayers.flatMap(
    (layerDef) => layerDef.layers.map((layer) => layer.id)
);

export const staticLayerGroups = {
    'ecoregions-group': ['l3-ecoregions', 'l4-ecoregions'],
    'counties-group': ['counties-outline', 'counties-fill'],
} as const;

export type StaticLayerGroupID = keyof typeof staticLayerGroups;

export type LayerWithPromotedID = Extract<
    (typeof staticMapLayers)[number]['source'],
    { promoteId: string }
>;

export type PromotedID = LayerWithPromotedID['promoteId'];

// List of all promoteIds property values
export const promotedMapProperties = staticMapLayers
    .map((layer): string | undefined => {
        // Narrow to vector sources
        if (layer.source.type === 'vector') {
            return layer.source.promoteId;
        }
        return undefined;
    })
    .filter((id): id is string => id !== undefined);

// Selector definitions for promoted props (used for setting hover/select state)
export const promotedPropSelectors = staticMapLayers.reduce(
    (acc, layer) => {
        // Narrow to vector sources
        if (layer.source.type !== 'vector') return acc;
        const promotedID = layer.source.promoteId;
        if (!promotedID) return acc;

        for (let sublayer of layer.layers) {
            // Ensure both properties exist
            if ('source-layer' in sublayer && 'source' in sublayer) {
                acc[promotedID as string] = {
                    source: sublayer.source as string,
                    sourceLayer: sublayer['source-layer'] as string,
                };
                break;
            }
        }
        return acc;
    },
    {} as Record<string, { source: string; sourceLayer: string }>
);

export const staticPerformanceSensitiveLayers = new Set<
    StaticLayerGroupID | StaticMapLayerID
>([]);

export function createObservationsBundle(taxonID: string, color: string) {
    const sourceID = `observations-tiles-${taxonID}`;
    return {
        id: sourceID,
        source: {
            type: 'vector',
            tiles: [],
            minzoom: 0,
            maxzoom: 14,
            promoteId: 'gbif_id',
        } as mapboxgl.VectorSourceSpecification,
        layers: [
            {
                id: `observations-fill-${taxonID}`,
                type: 'fill',
                source: sourceID,
                'source-layer': 'observations-heatmap',
                minzoom: 0,
                maxzoom: observationsZoomCutoff,
                paint: {
                    'fill-color': color,
                    'fill-opacity': [
                        'interpolate',
                        ['linear'],
                        ['ln', ['+', ['get', 'observation_count'], 1]],
                        Math.log(1),
                        0.1,
                        Math.log(2),
                        0.3,
                        Math.log(5),
                        0.5,
                        Math.log(10),
                        0.6,
                        Math.log(20),
                        0.7,
                        Math.log(50),
                        0.8,
                        Math.log(100),
                        0.9,
                        Math.log(200),
                        1.0,
                    ],
                },
            },
            {
                id: `observations-fill-outline-${taxonID}`,
                type: 'line',
                source: sourceID,
                'source-layer': 'observations-heatmap',
                minzoom: 0,
                maxzoom: observationsZoomCutoff,
                paint: {
                    'line-color': 'white',
                    'line-width': 1,
                },
            },
            {
                id: `observations-circles-${taxonID}`,
                type: 'circle',
                source: sourceID,
                'source-layer': 'observations-circles',
                minzoom: observationsZoomCutoff,
                paint: {
                    'circle-color': color,
                    'circle-opacity': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false],
                        1.0,
                        ['boolean', ['feature-state', 'hover'], false],
                        0.9,
                        0.8,
                    ],
                    'circle-radius': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false],
                        10,
                        ['boolean', ['feature-state', 'hover'], false],
                        12,
                        8,
                    ],
                    'circle-stroke-width': 2,
                },
            },
        ],
        deferred: true,
    } satisfies LayerBundle;
}

export function createRangeExtentBundle(taxonID: string, color: string) {
    const sourceID = `range-extent-${taxonID}`;
    return {
        id: sourceID,
        source: {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: [],
            },
        } as mapboxgl.GeoJSONSourceSpecification,
        layers: [
            {
                id: `range-extent-polygon-${taxonID}`,
                type: 'fill',
                source: sourceID,
                paint: {
                    'fill-color': color,
                    'fill-opacity': 0.2,
                    'fill-outline-color': '#000000',
                },
            },
            {
                id: `range-extent-outline-${taxonID}`,
                type: 'line',
                source: sourceID,
                paint: {
                    'line-color': color,
                    'line-width': 1,
                },
            },
        ],
    } satisfies LayerBundle;
}
