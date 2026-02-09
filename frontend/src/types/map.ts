import type { LayerGroupID, MapLayerID } from '../lib/map/mapLayers';

export type LayerTogglePayload = {
    layerID: MapLayerID | LayerGroupID;
    layerVisible: boolean;
};
