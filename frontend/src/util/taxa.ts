import { italicizedRanks, type ItalicizedRank } from '../constants/taxa';
import type { TaxonNodeType } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';

// Helper function to check if a provided value is a member of italicizedRanks
export function isItalicizedRank(value: unknown): value is ItalicizedRank {
    return (
        typeof value === 'string' &&
        italicizedRanks.includes(value.toLowerCase() as ItalicizedRank)
    );
}

export function constructItalicizedName(
    taxonNode: TaxonNodeType
): string | undefined {
    const rank = taxonNode.taxon_rank;
    if (!isItalicizedRank(rank)) return;

    let nameString = taxonNode.generic_name || '';

    switch (rank) {
        case 'genus':
            break;
        case 'subgenus':
            nameString += ` (${taxonNode.infrageneric_epithet})`;
            break;
        case 'species':
            nameString += ` ${taxonNode.specific_epithet}`;
            break;
        case 'subspecies':
            nameString += ` ${taxonNode.specific_epithet}`;
            nameString += ` ${taxonNode.infraspecific_epithet}`;
            break;
    }
    return nameString;
}
