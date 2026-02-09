import { getContext, setContext } from 'svelte';
import {
    layerGroups,
    type LayerGroupID,
    type MapLayerID,
    type MapLayerSource,
    type MapSourceLayer,
} from '../lib/map/mapLayers';

export const mapStateKey = 'map';

export type HoveredFeatureInfo = {
    source: MapLayerSource;
    sourceLayer: MapSourceLayer;
    id: number | string | MapLayerID;
    properties: Record<string, unknown>;
};

export type HoveredLegendInfo = {
    source: MapLayerSource;
    sourceLayer: MapSourceLayer;
    properties: Record<string, unknown>;
};

// TODO: Anything in here with key values should be taken from somewhere more global
export type MapStateType = {
    map: mapboxgl.Map | null;
    center: mapboxgl.LngLat | null;
    zoom: number | null;
    activeLayers: MapLayerID[];
    isLayerGroupActive: (groupID: LayerGroupID) => boolean;
    setLayerVisibility: (
        layerID: MapLayerID | LayerGroupID,
        visible: boolean,
        opacityOnly: boolean
    ) => void;
    rangeExtentGeom: GeoJSON.Polygon | null;
    areaOfOccupancyGeom: GeoJSON.MultiPolygon | null;
    hoveredFeatures: HoveredFeatureInfo[] | null;
    hoveredLegendInfo: HoveredLegendInfo[] | null;
    loading: boolean;
};

export const initialMapState: MapStateType = {
    activeLayers: [
        'observations-circles',
        'observations-fill',
        'observations-fill-outline',
        'range-extent-outline',
        'range-extent-polygon',
    ],
    isLayerGroupActive: (groupID: LayerGroupID) => {
        const layerIDs = layerGroups[groupID];
        if (!layerIDs) return false;
        return layerIDs.every((id) =>
            // activeLayers exists at this point
            initialMapState.activeLayers.includes(id)
        );
    },
    setLayerVisibility: (
        _layerID: MapLayerID | LayerGroupID,
        _visible: boolean,
        _opacityOnly: boolean
    ) => {},
    loading: false,
    rangeExtentGeom: null,
    areaOfOccupancyGeom: null,
    map: null,
    center: null,
    zoom: null,
    hoveredFeatures: null,
    hoveredLegendInfo: null,
};

export function setMapContext(mapState: MapStateType) {
    setContext(mapStateKey, mapState);
}

export function getMapContext(): MapStateType {
    return getContext(mapStateKey) as MapStateType;
}
