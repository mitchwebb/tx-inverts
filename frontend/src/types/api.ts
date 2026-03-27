// Types pertaining to API responses
import type { TaxonomicRank, TaxonomicStatus } from './taxa';

export type RawTaxonSearchSuggestion = {
    scientific_name: string;
    canonical_name: string;
    taxon_id: number;
    taxon_rank: TaxonomicRank;
    us_invasive: boolean;
    taxonomic_status: TaxonomicStatus;
};

export type TaxonSearchSuggestion = {
    scientificName: string | null;
    canonicalName: string | null;
    taxonID: number | null;
    taxonRank: TaxonomicRank | null;
    usInvasive: boolean | null;
    taxonomicStatus: TaxonomicStatus | null;
};

export type NSRank = 'x' | 'h' | '1' | '2' | '3' | '4' | '5' | 'u' | null;

export type NSLevel = 's' | 'g' | 'n';

export type RawNSValues = {
    number_of_occurrences: number | null;
    area_of_occupancy_4km2_bins: number | null;
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
    accepted_name_usage_id: number | null;
    canonical_name: string | null;
    taxon_rank: TaxonomicRank | null;
    scientific_name_authorship: string | null;
    kingdom: string | null;
    phylum: string | null;
    class: string | null;
    order: string | null;
    superfamily?: string | null;
    family: string | null;
    subfamily?: string | null;
    genus: string | null;
    species: string | null;
    subspecies?: string | null;
    us_invasive: boolean | null;
    taxonomic_status: TaxonomicStatus | null;
    ns_rank_state: NSRank | null;
    ns_rank_state_no_inat: NSRank | null;
} | null;

export type TaxonInfo = {
    acceptedTaxonID: number | null;
    canonicalName: string | null;
    taxonRank: TaxonomicRank | null;
    scientificNameAuthorship: string | null;
    kingdom: string | null;
    phylum: string | null;
    class: string | null;
    order: string | null;
    superfamily?: string | null;
    family: string | null;
    subfamily?: string | null;
    genus: string | null;
    species: string | null;
    subspecies?: string | null;
    usInvasive: boolean | null;
    taxonomicStatus: TaxonomicStatus | null;
    nSRankDB: NSRank | null; // NS Rank from Database
    nSRankDBNoINat: NSRank | null; // NS Rank from Database without iNat

    // // Locally calculated rank (derived from nSValues)
    // nSRankLocal: NSRank | null;

    // Merged from separate API call
    commonNames: string[] | null;
};

export const TAXON_INFO_MAP = {
    accepted_name_usage_id: 'acceptedTaxonID',
    canonical_name: 'canonicalName',
    taxon_rank: 'taxonRank',
    scientific_name_authorship: 'scientificNameAuthorship',
    kingdom: 'kingdom',
    phylum: 'phylum',
    class: 'class',
    order: 'order',
    superfamily: 'superfamily',
    family: 'family',
    subfamily: 'subfamily',
    genus: 'genus',
    species: 'species',
    subspecies: 'subspecies',
    us_invasive: 'usInvasive',
    taxonomic_status: 'taxonomicStatus',
    ns_rank_state: 'nSRankDB',
    ns_rank_state_no_inat: 'nSRankDBNoINat',
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

// // TODO: This should be merged with contexts if reasonable
// export type TaxonInfo = {
// 	taxonRank: TaxonomicRank | null;
// 	canonicalName: string | null;
// 	scientificNameAuthorship: string | null;
// 	kingdom: string;
// 	phylum: string;
//     class: string;
//     order: string;
//     superfamily?: string;
//     family: string;
//     subfamily?: string;
//     genus: string;
//     species: string;
//     subspecies?: string;
// 	commonNames?: string[] | null;
// 	usInvasive: boolean | null;
// };

// We're gonna have to keep these looking RAW in order to prevent renaming
// tens of thousands of keys
export type TaxonNodeType = {
    taxon_id: number;
    parent_name_usage_id: number;
    accepted_name_usage_id: number | null;
    taxon_rank: TaxonomicRank;
    canonical_name: string | null;
    scientific_name_authorship: string | null;
    ns_rank_state: NSRank | null;
    ns_rank_state_no_inat: NSRank | null;
    taxonomic_status: TaxonomicStatus;
    phylum: string | null;
    class: string | null;
    order: string | null;
    family: string | null;
    genus: string | null;
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
