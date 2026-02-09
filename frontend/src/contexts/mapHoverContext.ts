import { getContext, setContext } from 'svelte';

export const mapHoverStateKey = 'mapHover';

export type MapHoverFormattedData = {
    lnglat: [string | number, string | number] | [null, null];
};

export function setMapHoverContext(mapState: MapHoverFormattedData): void {
    setContext(mapHoverStateKey, mapState);
}

export function getMapHoverContext(): MapHoverFormattedData {
    return getContext(mapHoverStateKey);
}
