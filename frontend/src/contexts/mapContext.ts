import { getContext, setContext } from 'svelte';
import {
    staticLayerGroups,
    type StaticLayerGroupID,
} from '../lib/map/mapLayers';

export const mapStateKey = 'map';

export type HoveredFeatureInfo = {
    source: string;
    sourceLayer: string;
    id: number | string;
    properties: Record<string, unknown>;
};

export type HoveredLegendInfo = {
    source: string;
    sourceLayer: string;
    properties: Record<string, unknown>;
};

export type TaxonLayerState = {
    color: string;
    layerIDs: string[];
    loaded: boolean;
    rangeExtentGeom: GeoJSON.Polygon | null;
    areaOfOccupancyGeom: GeoJSON.MultiPolygon | null;
};

// TODO: Anything in here with key values should be taken from somewhere more global
export type MapState = {
    map: mapboxgl.Map | null;
    center: mapboxgl.LngLat | null;
    zoom: number | null;
    activeLayers: string[];
    layerGroups: Record<string, string[]>;
    isLayerGroupActive: (groupID: string) => boolean;
    setLayerVisibility: (
        layerID: string,
        visible: boolean,
        opacityOnly: boolean
    ) => void;
    hoveredFeatures: HoveredFeatureInfo[] | null;
    hoveredLegendInfo: HoveredLegendInfo[] | null;
    loading: boolean;
    taxonLayers: Record<number, TaxonLayerState>;
};

export const initialMapState: MapState = {
    activeLayers: [],
    // Initialize with static layer groups, dynamic will be added later
    layerGroups: Object.fromEntries(
        Object.entries(staticLayerGroups).map(([k, v]) => [k, [...v]])
    ),
    isLayerGroupActive: (_groupID: string) => false,
    setLayerVisibility: (
        _layerID: string,
        _visible: boolean,
        _opacityOnly: boolean
    ) => {},
    loading: false,
    map: null,
    center: null,
    zoom: null,
    hoveredFeatures: null,
    hoveredLegendInfo: null,
    taxonLayers: {},
};

export function setMapContext(mapState: MapState) {
    setContext(mapStateKey, mapState);
}

export function getMapContext(): MapState {
    return getContext(mapStateKey) as MapState;
}
