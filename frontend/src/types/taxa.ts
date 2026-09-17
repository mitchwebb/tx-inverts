export type TaxonomicRank =
    | 'kingdom'
    | 'phylum'
    | 'class'
    | 'subclass'
    | 'order'
    | 'superfamily'
    | 'family'
    | 'sub'
    | 'tribe'
    | 'subtribe'
    | 'genus'
    | 'subgenus'
    | 'species'
    | 'subspecies';

// Taxonomic ranks with _key columns in our database
// These are the only ranks by which occurrences can be hierarchically sorted
export type KeyedTaxonomicRank =
    | 'kingdom'
    | 'phylum'
    | 'class'
    | 'order'
    | 'superfamily'
    | 'family'
    | 'subfamily'
    | 'tribe'
    | 'subtribe'
    | 'genus'
    | 'subgenus'
    | 'species';

export type TaxonomicStatus =
    | 'accepted'
    | 'doubtful'
    | 'synonym'
    | 'heterotypic synonym'
    | 'homotypic synonym'
    | 'proparte synonym'
    | 'misapplied'
    | 'ambiguous synonym'
    | 'provisionally accepted';
