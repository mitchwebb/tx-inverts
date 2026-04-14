import type { FiltersState } from '../contexts/filtersContext';
import {
    normalizeAPIResponse,
    REGION_INFO_MAP,
    type RawRegionInfo,
    type RegionInfo,
} from '../types/api';

export async function getRegionInfo(
    regionID: FiltersState['region']['ids'][0]
): Promise<RegionInfo | null> {
    const url = 'server/regions/get_region_info';
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                region_id: regionID,
            }),
        });
        const json: RawRegionInfo | null = await response.json();
        return normalizeAPIResponse<RegionInfo>(json, REGION_INFO_MAP);
    } catch (error) {
        console.error(error);
        return null;
    }
}
