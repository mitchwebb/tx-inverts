from .base_table import DBTable


class VernacularNames(DBTable):
    """
    Table of vernacular names in different languages, sourced from COL backbone download.
    """

    name = 'vernacular_names'
    primary_key = None
    columns = {
        'taxon_id': 'TEXT',
        'language': 'TEXT',
        'vernacular_name': 'TEXT'
    }


VERNACULAR_NAMES_TABLE = VernacularNames()
