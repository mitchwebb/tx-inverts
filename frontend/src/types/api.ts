// Types pertaining to API responses
import type { TaxonomicRank, TaxonomicStatus } from './taxa';

export type RawTaxonSearchSuggestion = {
    scientific_name: string;
    scientific_name_authorship: string | null;
    canonical_name: string;
    taxon_id: string;
    taxon_rank: TaxonomicRank;
    us_invasive: boolean;
    taxonomic_status: TaxonomicStatus;
};

export type TaxonSearchSuggestion = {
    scientificName: string | null;
    scientificNameAuthorship: string | null;
    canonicalName: string | null;
    taxonID: string;
    taxonRank: TaxonomicRank | null;
    uSInvasive: boolean | null;
    taxonomicStatus: TaxonomicStatus | null;
};

export type NSRank = 'x' | 'h' | '1' | '2' | '3' | '4' | '5' | 'u' | null;

export type NSLevel = 's' | 'g' | 'n';

export type RawNSValues = {
    number_of_occurrences: number | null;
    area_of_occupancy_4km2_bins: number | null;
    area_of_occupancy_1km2_bins: number | null;
    range_extent_km2: number | null;
    observation_count: number | null;
} | null;

export type NSValues = {
    numberOfOccurrences: number | null;
    areaOfOccupancy4Km2Bins: number | null;
    areaOfOccupancy1Km2Bins: number | null;
    rangeExtentKm2: number | null;
    observationCount: number | null;
};

export const NS_VALUES_MAP = {
    number_of_occurrences: 'numberOfOccurrences',
    area_of_occupancy_4km2_bins: 'areaOfOccupancy4Km2Bins',
    area_of_occupancy_1km2_bins: 'areaOfOccupancy1Km2Bins',
    range_extent_km2: 'rangeExtentKm2',
    observation_count: 'observationCount',
} as const;

export type TaxonInfo = {
    taxonID: string;
    parentNameUsageID: string;
    acceptedNameUsageID: string | null;
    canonicalName: string | null;
    scientificName: string | null;
    scientificNameAuthorship: string | null;
    vernacularNames: string[] | null;
    taxonRank: TaxonomicRank | null;
    kingdom: string | null;
    phylum: string | null;
    class: string | null;
    order: string | null;
    family: string | null;
    genericName: string | null;
    infragenericEpithet: string | null;
    specificEpithet: string | null;
    infraspecificEpithet: string | null;
    uSInvasive: boolean | null;
    taxonomicStatus: TaxonomicStatus | null;
    nSRankState: NSRank | null; // NS Rank from Database
    nSRankStateNoINat: NSRank | null; // NS Rank from Database without iNat
};

export type TaxonNodeType = TaxonInfo & {
    effectiveParentID?: string | null; // Used to point to the effective parent in a visual hierarchy
};

export type RawRegionInfo = {
    id: string;
    name: string;
    region_type: 'park' | 'county' | 'ecoregion';
};

export type RegionInfo = {
    id: string; // uuid
    name: string;
    regionType: 'park' | 'county' | 'ecoregion';
};

export const REGION_INFO_MAP = {
    id: 'id',
    name: 'name',
    region_type: 'regionType',
} as const;

// Function to map RAW API values to frontend values, replacing any missing values with null
export function normalizeAPIResponse<T extends Record<string, any>>(
    data: Record<string, any> | null | undefined,
    map: Record<string, keyof T>
): T {
    const out: any = {};

    for (const [from, to] of Object.entries(map)) {
        out[to] = data?.[from] ?? null;
    }

    return out as T;
}

export type RawDateRange = {
    min_date: string;
    max_date: string;
};

export type DateRange = {
    minDate: string;
    maxDate: string;
};

export type RawEstimateMetrics = {
    row_count: number;
    size_estimate: number;
};

export type EstimateMetrics = {
    rowCount: number;
    sizeEstimate: number;
};

// TODO: We really should combine the TaxonNodeType and TaxonInfo type
