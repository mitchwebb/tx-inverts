import { type MapState } from '../contexts/mapContext';
import {
    staticPerformanceSensitiveLayers,
    type StaticMapLayerID,
} from '../lib/map/mapLayers';
import type { LayerTogglePayload } from '../types/map';

// Safely handle mapContext.activeLayer list changes and pass to
// setLayerVisiblity function
export function toggleLayer(
    context: MapState,
    layerOrGroupID: string,
    visible: boolean,
    opacityOnly: boolean
) {
    // Expand possible group IDs into actual layer IDs
    const layerIDs: string[] = context.layerGroups[layerOrGroupID]?.slice() ?? [
        layerOrGroupID,
    ];

    // If trying to make visible
    if (visible) {
        // Add layer to updated list if not in activeLayers
        context.activeLayers = [
            ...context.activeLayers,
            ...layerIDs.filter((id) => !context.activeLayers.includes(id)),
        ];
        // If trying to hide layer, filter it from the current active list
    } else {
        context.activeLayers = context.activeLayers.filter(
            (id) => !layerIDs.includes(id)
        );
    }

    // Send layerID and params to visibility toggle logic
    context.setLayerVisibility(layerOrGroupID, visible, opacityOnly);
}

// Handler for input toggles to show/hide map layers (separate logic for easier testing)
export function handleLayerToggle(
    context: MapState,
    payload: LayerTogglePayload
) {
    if (payload.layerVisible === undefined) {
        throw new Error('Expected payload.checked to be defined.');
    }

    // Get layer id
    const id = payload.layerID;
    // Taxon layers are always performance sensitive
    const isTaxonLayer =
        /-(fill|fill-outline|circles|polygon|outline)-\d+$/.test(id) ||
        /-(layer-group)-\d+$/.test(id);
    // Determine if layer is marked as 'performanceSensitive'
    const opacityOnly =
        isTaxonLayer ||
        staticPerformanceSensitiveLayers.has(id as StaticMapLayerID);

    toggleLayer(context, id, payload.layerVisible, opacityOnly);
}
