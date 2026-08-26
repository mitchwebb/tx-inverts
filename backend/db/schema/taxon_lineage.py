from backend.db.schema.base_table import DBTable


class TaxonLineage(DBTable):
    """
    Materialized view definition mapping each distinct accepted_taxon_key in occurrences table
    with its ancestor_id for each taxonomic rank for easy lineage lookup.
    """

    name = 'taxon_lineage'
    primary_key = None
    columns = {
        'accepted_taxon_key': 'TEXT NOT NULL',
        'ancestor_id': 'TEXT'
    }


TAXON_LINEAGE_TABLE = TaxonLineage()
