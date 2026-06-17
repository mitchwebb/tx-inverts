from .base_table import DBTable


class USInvasivesChecklist(DBTable):
    """
    US invasive taxa table derived from Global Register of Introduced and Invasive Species (2022)
    """

    name = 'us_invasives_checklist'
    primary_key = 'taxon_key'
    columns = {
        'taxon_id': 'BIGINT',
        'scientific_name': 'TEXT',
        'kingdom': 'TEXT',
        'phylum': 'TEXT',
        'class': 'TEXT',
        'order': 'TEXT',
        'family': 'TEXT',
        'taxon_rank': 'TEXT',
        'scientific_name_authorship': 'TEXT',
        'vernacular_name': 'TEXT',
        'taxonomic_status': 'TEXT',
        'taxon_remarks': 'TEXT',
        'license': 'TEXT',
        'rights_holder': 'TEXT',
        'bibliographic_citation': 'TEXT',
        'references': 'TEXT',
        'institution_code': 'TEXT',
        'dataset_id': 'TEXT',
        'dataset_name': 'TEXT',
        'taxon_id_link': 'TEXT'
    }


US_INVASIVES_TABLE = USInvasivesChecklist()
