import type { FiltersState } from '../contexts/filtersContext';
import {
    normalizeAPIResponse,
    REGION_INFO_MAP,
    type RawRegionInfo,
    type RegionInfo,
} from '../types/api';

export async function getRegionInfo(
    regionID: FiltersState['regions']['ids'][0]
): Promise<RegionInfo | null> {
    const url = `server/regions/get_region_info?region_id=${regionID}`;
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        const json: RawRegionInfo | null = await response.json();
        return normalizeAPIResponse<RegionInfo>(json, REGION_INFO_MAP);
    } catch (error) {
        console.error(error);
        return null;
    }
}
