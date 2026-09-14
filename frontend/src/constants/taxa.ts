import type { ActiveTaxon } from '../contexts/activeTaxaContext';
import type { TaxonomicRank } from '../types/taxa';

export type ItalicizedRank = Extract<
    TaxonomicRank,
    'genus' | 'species' | 'subspecies' | 'subgenus'
>;

export const italicizedRanks: ItalicizedRank[] = [
    'genus',
    'species',
    'subspecies',
    'subgenus',
];

export const TAXON_COLORS = [
    '#e58606',
    '#5d69b1',
    '#52bca3',
    '#99c945',
    '#cc61b0',
    '#24796c',
    '#daa51b',
    '#2f8ac4',
    '#764e9f',
    '#ed645a',
    '#cc3a8e',
    '#a5aa99',
];

export const DUMMY_TAXON: ActiveTaxon = {
    color: TAXON_COLORS[0],
    taxonLoading: false,
    taxonError: false,
    dateCounts: null,
    dateCountsLoading: false,
    dateRangeLoading: false,
    datasetCountsLoading: false,
    nSValuesLoading: false,
    lastLoadedID: 'G9Q6',
    taxonID: 'G9Q6',
    info: {
        taxonID: 'G9Q6',
        acceptedNameUsageID: 'G9Q6',
        parentNameUsageID: '7NQXN',
        scientificName: 'Archispirostreptus gigas',
        canonicalName: 'Archispirostreptus gigas',
        taxonRank: 'species',
        scientificNameAuthorship: '(Peters, 1855)',
        kingdom: 'Animalia',
        phylum: 'Arthropoda',
        class: 'Diplopoda',
        order: 'Spirostreptida',
        family: 'Spirostreptidae',
        genericName: 'Archispirostreptus',
        specificEpithet: 'gigas',
        infragenericEpithet: null,
        infraspecificEpithet: null,
        uSInvasive: false,
        taxonomicStatus: 'accepted',
        vernacularNames: ['Giant African Millipede', 'Shongololo'],
        nSRankState: null,
        nSRankStateNoINat: null,
    },
    nSValues: {
        numberOfOccurrences: 40,
        rangeExtentKm2: 8093446,
        areaOfOccupancy1Km2Bins: 40,
        areaOfOccupancy4Km2Bins: 39,
        observationCount: 41,
    },
    datasetCounts: { 'iNaturalist Research-grade Observations': 15 },
    dateMin: null,
    dateMax: null,
};
