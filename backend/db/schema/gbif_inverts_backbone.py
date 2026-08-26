# Model for gbif_observations table
from .base_table import DBTable


class GBIFInvertsBackbone(DBTable):
    """
    GBIF backbone for all inverts.
    Includes lineage columns (<rank>_id) for each taxonomic rank.
    """

    name = 'gbif_inverts_backbone'
    primary_key = 'taxon_id'
    columns = {
        'taxon_id': 'TEXT PRIMARY KEY',
        'parent_name_usage_id': 'TEXT',
        'accepted_name_usage_id': 'TEXT',
        'original_name_usage_id': 'TEXT',
        'scientific_name': 'TEXT NOT NULL',
        'scientific_name_authorship': 'TEXT',
        'canonical_name': 'TEXT',
        'generic_name': 'TEXT',
        'taxon_rank': 'TEXT',
        'name_published_in': 'TEXT',
        'taxonomic_status': 'TEXT',
        'taxon_remarks': 'TEXT',
        'kingdom': 'TEXT',
        'phylum': 'TEXT',
        'class': 'TEXT',
        'order': 'TEXT',
        'superfamily': 'TEXT',
        'family': 'TEXT',
        'subfamily': 'TEXT',
        'tribe': 'TEXT',
        'subtribe': 'TEXT',
        'genus': 'TEXT',
        'subgenus': 'TEXT',
        'species': 'TEXT',
        'subspecies': 'TEXT',
        'ns_rank_state': 'TEXT',
        'ns_rank_state_no_inat': 'TEXT',
        'us_invasive': 'BOOLEAN'
    }


GBIF_INVERTS_BACKBONE = GBIFInvertsBackbone()
