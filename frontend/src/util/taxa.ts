import { italicizedRanks, type ItalicizedRank } from '../constants/taxa';
import type { TaxonInfo } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';

// Helper function to check if a provided value is a member of italicizedRanks
export function isItalicizedRank(
    value: TaxonomicRank | null
): value is ItalicizedRank {
    return (
        typeof value === 'string' &&
        italicizedRanks.includes(value.toLowerCase() as ItalicizedRank)
    );
}

export function constructItalicizedName(
    taxonNode: TaxonInfo
): string | undefined {
    const rank = taxonNode.taxonRank;
    if (!isItalicizedRank(rank)) return;

    let nameString = taxonNode.genericName || '';

    switch (rank) {
        case 'genus':
            break;
        case 'subgenus':
            nameString += ` (${taxonNode.infragenericEpithet})`;
            break;
        case 'species':
            nameString += ` ${taxonNode.specificEpithet}`;
            break;
        case 'subspecies':
            nameString += ` ${taxonNode.specificEpithet}`;
            nameString += ` ${taxonNode.infraspecificEpithet}`;
            break;
    }
    return nameString;
}
