from backend.db.schema.base import DBTable


class TaxonLineage(DBTable):
    """
    Materialized view definition mapping each distinct accepted_taxon_key in occurrences table
    with its ancestor_id for each taxonomic rank for easy lineage lookup.
    """

    name = 'taxon_lineage'
    primary_key = None
    columns = {
        'accepted_taxon_key': 'BIGINT NOT NULL',
        'ancestor_id': 'BIGINT'
    }


TAXON_LINEAGE_TABLE = TaxonLineage()
