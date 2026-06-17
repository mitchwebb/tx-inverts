# Model for gbif_observations table
from .base_table import DBTable


class GBIFObservationsTable(DBTable):
    """
    GBIF observations data for all inverts.
    Includes lineage columns (<rank>_id) for each taxonomic rank.
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
        'coordinate_uncertainty_in_meters': 'TEXT',
        'coordinate_precision': 'TEXT',
        'scientific_name': 'TEXT',
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
        'taxon_rank': 'TEXT',
        'taxonomic_status': 'TEXT',
        'dataset_key': 'TEXT',
        'last_interpreted': 'TIMESTAMPTZ',
        'issue': 'TEXT',
        'taxon_key': 'BIGINT',
        'accepted_taxon_key': 'BIGINT',
        'accepted_scientific_name': 'TEXT',
        'verbatim_scientific_name': 'TEXT',
        'geometry': 'GEOMETRY(Point, 4326)',
        'collection_start_date': 'DATE',
        'collection_end_date': 'DATE'
    }


GBIF_OBSERVATIONS_TABLE = GBIFObservationsTable()
