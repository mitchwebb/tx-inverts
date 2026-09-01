# Model for gbif_observations table
from .base_table import DBTable


class GBIFObservationsTable(DBTable):
    """
    GBIF observations data for all inverts.
    """

    name = 'gbif_observations'
    primary_key = 'gbif_id'
    columns = {
        'gbif_id': 'BIGINT PRIMARY KEY',
        'access_rights': 'TEXT',
        'license': 'TEXT',
        'modified': 'TIMESTAMPTZ',
        'publisher': 'TEXT',
        'references': 'TEXT',
        'rights_holder': 'TEXT',
        'recorded_by': 'TEXT',
        'dataset_id': 'TEXT',
        'institution_code': 'TEXT',
        'dataset_name': 'TEXT',
        'information_withheld': 'TEXT',
        'occurrence_id': 'TEXT',
        'individual_count': 'TEXT',
        'event_date': 'TEXT',
        'event_time': 'TEXT',
        'year': 'TEXT',
        'month': 'TEXT',
        'day': 'TEXT',
        'verbatim_event_date': 'TEXT',
        'field_notes': 'TEXT',
        'event_remarks': 'TEXT',
        'country_code': 'TEXT',
        'state_province': 'TEXT',
        'county': 'TEXT',
        'locality': 'TEXT',
        'verbatim_locality': 'TEXT',
        'decimal_latitude': 'DOUBLE PRECISION',
        'decimal_longitude': 'DOUBLE PRECISION',
        'coordinate_uncertainty_in_meters': 'NUMERIC',
        'coordinate_precision': 'TEXT',
        'scientific_name': 'TEXT',
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
        'generic_name': 'TEXT',
        'subgenus': 'TEXT',
        'infrageneric_epithet': 'TEXT',
        'specific_epithet': 'TEXT',
        'infraspecific_epithet': 'TEXT',
        'kingdom_key': 'TEXT',
        'phylum_key': 'TEXT',
        'class_key': 'TEXT',
        'order_key': 'TEXT',
        'superfamily_key': 'TEXT',
        'family_key': 'TEXT',
        'subfamily_key': 'TEXT',
        'tribe_key': 'TEXT',
        'subtribe_key': 'TEXT',
        'genus_key': 'TEXT',
        'subgenus_key': 'TEXT',
        'species_key': 'TEXT',
        'taxon_rank': 'TEXT',
        'taxonomic_status': 'TEXT',
        'dataset_key': 'TEXT',
        'last_interpreted': 'TIMESTAMPTZ',
        'issue': 'TEXT',
        'taxon_key': 'TEXT',
        'accepted_taxon_key': 'TEXT',
        'accepted_scientific_name': 'TEXT',
        'verbatim_scientific_name': 'TEXT',
        'geometry': 'GEOMETRY(Point, 4326)',
        'collection_start_date': 'DATE',
        'collection_end_date': 'DATE'
    }


GBIF_OBSERVATIONS_TABLE = GBIFObservationsTable()
