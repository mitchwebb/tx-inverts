from typing import NamedTuple


class GBIFObservationRow(NamedTuple):
    # Record-level
    gbifID: int
    accessRights: str | None
    license: str | None
    modified: str | None
    publisher: str | None
    references: str | None
    rightsHolder: str | None
    recordedBy: str | None
    datasetID: str | None
    institutionCode: str | None
    datasetName: str | None
    informationWithheld: str | None
    issue: str | None
    lastInterpreted: str | None
    datasetKey: str | None
    # Occurrence
    occurrenceID: str | None
    individualCount: str | None
    # Event
    eventDate: str | None
    eventTime: str | None
    year: str | None
    month: str | None
    day: str | None
    verbatimEventDate: str | None
    fieldNotes: str | None
    eventRemarks: str | None
    collectionStartDate: str | None
    collectionEndDate: str | None
    # Location
    countryCode: str | None
    stateProvince: str | None
    county: str | None
    locality: str | None
    verbatimLocality: str | None
    decimalLatitude: float | None
    decimalLongitude: float | None
    coordinateUncertaintyInMeters: str | None
    coordinatePrecision: str | None
    # Taxon
    scientificName: str | None
    acceptedScientificName: str | None
    verbatimScientificName: str | None
    taxonRank: str | None
    taxonomicStatus: str | None
    taxon_key: int | None
    acceptedTaxonKey: int | None
    kingdom: str | None
    phylum: str | None
    # NOTE: Class is left out for Python reserved word reasons
    # I've very sorry if you're reading this and needing a typed 'class' column
    order: str | None
    family: str | None
    genus: str | None
    species: str | None
    subspecies: str | None
