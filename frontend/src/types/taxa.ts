export type TaxonomicRank =
    | 'kingdom'
    | 'phylum'
    | 'subphylum'
    | 'superclass'
    | 'class'
    | 'subclass'
    | 'infraclass'
    | 'subterclass'
    | 'superorder'
    | 'order'
    | 'suborder'
    | 'infraorder'
    | 'parvorder'
    | 'nanorder'
    | 'section zoology'
    | 'subsection zoology'
    | 'superfamily'
    | 'epifamily'
    | 'series zoology'
    | 'family'
    | 'subfamily'
    | 'supertribe'
    | 'tribe'
    | 'subtribe'
    | 'infratribe'
    | 'genus'
    | 'subgenus'
    | 'species'
    | 'subspecies'
    | 'variety'
    | 'form';

export const RANK_ORDER: TaxonomicRank[] = [
    'kingdom',
    'phylum',
    'subphylum',
    'superclass',
    'class',
    'subclass',
    'infraclass',
    'subterclass',
    'superorder',
    'order',
    'suborder',
    'infraorder',
    'parvorder',
    'nanorder',
    'section zoology',
    'subsection zoology',
    'superfamily',
    'epifamily',
    'series zoology',
    'family',
    'subfamily',
    'supertribe',
    'tribe',
    'subtribe',
    'infratribe',
    'genus',
    'subgenus',
    'species',
    'subspecies',
    'variety',
    'form',
];

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
