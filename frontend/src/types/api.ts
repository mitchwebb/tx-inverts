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
    taxonID: string | null;
    taxonRank: TaxonomicRank | null;
    usInvasive: boolean | null;
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

export type RawTaxonInfo = {
    accepted_name_usage_id: string | null;
    canonical_name: string | null;
    scientific_name: string | null;
    scientific_name_authorship: string | null;
    vernacular_names: string[] | null;
    taxon_rank: TaxonomicRank | null;
    kingdom: string | null;
    phylum: string | null;
    class: string | null;
    order: string | null;
    family: string | null;
    generic_name: string | null;
    infrageneric_epithet: string | null;
    specific_ephitet: string | null;
    infraspecific_ephitet: string | null;
    us_invasive: boolean | null;
    taxonomic_status: TaxonomicStatus | null;
    ns_rank_state: NSRank | null;
    ns_rank_state_no_inat: NSRank | null;
} | null;

export type TaxonInfo = {
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
    specificEphitet: string | null;
    infraspecificEpithet: string | null;
    usInvasive: boolean | null;
    taxonomicStatus: TaxonomicStatus | null;
    nSRankDB: NSRank | null; // NS Rank from Database
    nSRankDBNoINat: NSRank | null; // NS Rank from Database without iNat

    // // Locally calculated rank (derived from nSValues)
    // nSRankLocal: NSRank | null;
};

export const TAXON_INFO_MAP = {
    accepted_name_usage_id: 'acceptedNameUsageID',
    canonical_name: 'canonicalName',
    scientific_name: 'scientificName',
    scientific_name_authorship: 'scientificNameAuthorship',
    vernacular_names: 'vernacularNames',
    taxon_rank: 'taxonRank',
    kingdom: 'kingdom',
    phylum: 'phylum',
    class: 'class',
    order: 'order',
    family: 'family',
    generic_name: 'genericName',
    infrageneric_epithet: 'infragenericEpithet',
    specific_epithet: 'specificEphitet',
    infraspecific_epithet: 'infraspecificEpithet',
    us_invasive: 'usInvasive',
    taxonomic_status: 'taxonomicStatus',
    ns_rank_state: 'nSRankDB',
    ns_rank_state_no_inat: 'nSRankDBNoINat',
} as const;

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

// We're gonna have to keep these looking RAW in order to prevent renaming
// tens of thousands of keys
export type TaxonNodeType = {
    taxon_id: string;
    parent_name_usage_id: string;
    effective_parent_id: string | null;
    accepted_name_usage_id: string | null;
    taxon_rank: TaxonomicRank;
    canonical_name: string | null;
    scientific_name: string | null;
    scientific_name_authorship: string | null;
    ns_rank_state: NSRank | null;
    ns_rank_state_no_inat: NSRank | null;
    taxonomic_status: TaxonomicStatus;
    phylum: string | null;
    class: string | null;
    order: string | null;
    family: string | null;
    generic_name: string | null;
    infrageneric_epithet: string | null;
    specific_epithet: string | null;
    infraspecific_epithet: string | null;
    us_invasive: boolean | null;
};

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
