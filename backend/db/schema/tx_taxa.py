# Model for tx_taxa table, a materialized view of GBIFInvertsBackbone
# TODO: In this case, do we even need to spell this out?
from .base_table import DBTable


class TXTaxaTable(DBTable):
    """
    Mat view to store Texas-only subset of GBIF backbone
    """

    name = 'tx_taxa'
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
        'generic_name': 'TEXT',
        'specific_epithet': 'TEXT',
        'infraspecific_epithet': 'TEXT',
        'infrageneric_epithet': 'TEXT',
        'ns_rank_state': 'TEXT',
        'ns_rank_state_no_inat': 'TEXT',
        'us_invasive': 'BOOLEAN'
    }


TX_TAXA_TABLE = TXTaxaTable()
