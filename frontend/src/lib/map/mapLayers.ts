import type { Layer } from 'mapbox-gl';
import {
    l3EcoregionsColorStops,
    l4EcoregionsColorStops,
    providersColorStops,
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
                    0.7,
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
                    0.7,
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

export const rangeExtentLayer = {
    id: 'range-extent',
    source: {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: [],
        },
    },
    layers: [
        {
            id: 'range-extent-polygon',
            type: 'fill',
            source: 'range-extent',
            paint: {
                'fill-color': '#8888ff',
                'fill-opacity': 0.2,
                'fill-outline-color': '#000000',
            },
        } as const,
        {
            id: 'range-extent-outline',
            type: 'line',
            source: 'range-extent',
            paint: {
                'line-color': '#8888ff',
                'line-width': 1,
            },
        } as const,
    ] as const,
} as const satisfies LayerBundle;

// TODO: This needs to link up with the API. Determine where to store number
export const observationsZoomCutoff: number = 10;

export const observationsLayerSource: {
    id: string;
    source: mapboxgl.VectorSourceSpecification;
} = {
    id: 'observations-tiles',
    source: {
        type: 'vector',
        tiles: [], // Tiles need to be added dynamically when source is created
        minzoom: 0,
        maxzoom: 14,
        promoteId: 'gbif_id',
    },
} as const;

export const observationsLayer = {
    ...observationsLayerSource,
    layers: [
        // Low zoom: Heatmap bins
        {
            id: 'observations-fill',
            type: 'fill',
            source: 'observations-tiles',
            'source-layer': 'observations-heatmap',
            minzoom: 0,
            maxzoom: observationsZoomCutoff,
            paint: {
                'fill-color': 'darkorange',
                'fill-opacity': [
                    'interpolate',
                    ['linear'],
                    ['ln', ['+', ['get', 'observation_count'], 1]],
                    Math.log(1),
                    0.3,
                    Math.log(2),
                    0.4,
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
            id: 'observations-fill-outline',
            type: 'line',
            source: 'observations-tiles',
            'source-layer': 'observations-heatmap',
            minzoom: 0,
            maxzoom: observationsZoomCutoff,
            paint: {
                'line-color': 'white',
                'line-width': 1,
            },
        } as const,

        // High zoom: circle points
        {
            id: 'observations-circles',
            type: 'circle',
            source: 'observations-tiles',
            'source-layer': 'observations-circles',
            minzoom: observationsZoomCutoff,
            paint: {
                'circle-color': [
                    'match',
                    ['get', 'institution_code'],
                    ...providersColorStops.flat(),
                    'white',
                ],
                'circle-opacity': [
                    'case',
                    ['boolean', ['feature-state', 'selected'], false],
                    1.0,
                    ['boolean', ['feature-state', 'selected'], false],
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
                'circle-stroke-color': 'black',
                'circle-stroke-width': 1,
                'line-opacity': 1,
            },
        } as const,
    ] as const,
    deferred: true,
} as const satisfies LayerBundle;

export const allMapLayers = [
    l3EcoregionsLayer,
    l4EcoregionsLayer,
    texasParksLayer,
    rangeExtentLayer,
    observationsLayer,
] satisfies LayerBundle[];

// Map layer source literal type
export type MapLayerSource =
    (typeof allMapLayers)[number]['layers'][number]['source'];

// Extract layers with source-layers for typing
type LayerWithSourceLayer = Extract<
    (typeof allMapLayers)[number]['layers'][number],
    { 'source-layer': string }
>;
// Map layer source-layer literal type
export type MapSourceLayer = LayerWithSourceLayer['source-layer'];

// Map layer id literal type
export type MapLayerID = (typeof allMapLayers)[number]['layers'][number]['id'];

export const allMapLayerIDs: MapLayerID[] = allMapLayers.flatMap((layerDef) =>
    layerDef.layers.map((layer) => layer.id)
);

export const layerGroups = {
    'observations-layer-group': [
        'observations-fill',
        'observations-fill-outline',
        'observations-circles',
    ],
    'range-extent-layer-group': [
        'range-extent-polygon',
        'range-extent-outline',
    ],
    'ecoregions-group': ['l3-ecoregions', 'l4-ecoregions'],
} as const;

// List of layers
export const performanceSensitiveLayers = new Set<LayerGroupID | MapLayerID>([
    'observations-layer-group',
    'observations-fill',
    'observations-fill-outline',
    'observations-circles',
]);

export type LayerGroupID = keyof typeof layerGroups;

export type LayerWithPromotedID = Extract<
    (typeof allMapLayers)[number]['source'],
    { promoteId: string }
>;

export type PromotedID = LayerWithPromotedID['promoteId'];

// List of all promoteIds property values
export const promotedMapProperties = allMapLayers
    .map((layer) => {
        // Narrow to vector sources
        if (layer.source.type === 'vector') {
            return layer.source.promoteId;
        }
        return undefined;
    })
    .filter((id): id is string => id !== undefined);

// Selector definitions for promoted props (used for setting hover/select state)
export const promotedPropSelectors = allMapLayers.reduce(
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
