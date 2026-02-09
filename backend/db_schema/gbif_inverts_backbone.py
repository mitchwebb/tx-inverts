# Model for gbif_observations table

from .base import DBTable


class GBIFInvertsBackbone(DBTable):
    name = 'gbif_inverts_backbone'
    primary_key = 'taxon_id'
    columns = {
        'taxon_id': 'BIGINT PRIMARY KEY',
        'dataset_id': 'UUID',
        'parent_name_usage_id': 'BIGINT',
        'accepted_name_usage_id': 'BIGINT',
        'original_name_usage_id': 'BIGINT',
        'scientific_name': 'TEXT NOT NULL',
        'scientific_name_authorship': 'TEXT',
        'canonical_name': 'TEXT',
        'generic_name': 'TEXT',
        'taxon_rank': "TEXT CHECK (taxon_rank IN ('genus', 'kingdom', 'family', 'phylum', 'species', 'unranked', 'subspecies', 'variety', 'form', 'class', 'order'))",
        'name_published_in': 'TEXT',
        'taxonomic_status': "TEXT CHECK (taxonomic_status IN ('accepted', 'doubtful', 'synonym', 'homotypic synonym', 'heterotypic synonym', 'proparte synonym'))",
        'taxon_remarks': 'TEXT',
        'kingdom': 'TEXT',
        'kingdom_id': 'BIGINT',
        'phylum': 'TEXT',
        'phylum_id': 'BIGINT',
        'class': 'TEXT',
        'class_id': 'BIGINT',
        'order': 'TEXT',
        'order_id': 'BIGINT',
        'family': 'TEXT',
        'family_id': 'BIGINT',
        'genus': 'TEXT',
        'genus_id': 'BIGINT',
        'species': 'TEXT',
        'species_id': 'BIGINT',
        'subspecies': 'TEXT',
        'subspecies_id': 'BIGINT',
        'ns_rank_state': 'TEXT',
        'ns_rank_state_no_inat': 'TEXT',
        'us_invasive': 'BOOLEAN'
    }

GBIF_INVERTS_BACKBONE = GBIFInvertsBackbone()