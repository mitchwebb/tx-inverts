from dataclasses import dataclass
from typing import Optional

@dataclass
class GBIFRecord:
    export interface GbifRecord 
    // DarwinCore / GBIF field names

    // startDate must be constructed from GBIF's year/month/day fields, because
    // it randomly wrong, and not even consistent for the same catalog number.

    catalogNumber: string;
    occurrenceID: string;

    kingdom: string;
    phylum?: string;
    class?: string;
    order?: string;
    family?: string;
    genus?: string;
    specificEpithet?: string;
    infraspecificEpithet?: string;
    scientificName: string;

    continent: string;
    country?: string;
    stateProvince?: string;
    county?: string;
    locality?: string;
    decimalLatitude?: string;
    decimalLongitude?: string;

    startDate?: string; // constructed from GBIF year/month/day
    recordedBy?: string; // collectors, |-delimited names, last name last
    dateIdentified?: string; // determination date (not just year)
    identifiedBy?: string; // determiners, |-delimited names, last name last
    eventRemarks?: string; // collecting event/info/habitat/end date
    occurrenceRemarks?: string;
    identificationRemarks?: string;
    typeStatus?: string;
    organismQuantity?: string;
    lifeStage?: string;


@dataclass
class Specimen:
    # Core specimen fields
    catalog_number: str
    occurrence_guid: str
    taxon_id: int
    locality_id: int
    collection_start_date: Optional[str] = None
    partial_start_date: Optional[str] = None
    collection_end_date: Optional[str] = None
    partial_end_date: Optional[str] = None
    collectors: Optional[str] = None
    normalized_collectors: Optional[str] = None
    determination_year: Optional[int] = None
    determiners: Optional[str] = None
    locality_notes: Optional[str] = None
    specimen_notes: Optional[str] = None
    determination_notes: Optional[str] = None
    type_status: Optional[str] = None
    specimen_count: Optional[int] = None
    life_stage: Optional[str] = None
    problems: Optional[str] = None

    # Taxa cache
    kingdom_name: str
    kingdom_id: int
    phylum_name: Optional[str] = None
    phylum_id: Optional[int] = None
    class_name: Optional[str] = None
    class_id: Optional[int] = None
    order_name: Optional[str] = None
    order_id: Optional[int] = None
    family_name: Optional[str] = None
    family_id: Optional[int] = None
    genus_name: Optional[str] = None
    genus_id: Optional[int] = None
    subgenus: Optional[str] = None
    species_name: Optional[str] = None
    species_id: Optional[int] = None
    subspecies_name: Optional[str] = None
    subspecies_id: Optional[int] = None
    taxon_unique: str
    taxon_author: Optional[str] = None
    karst_obligate: Optional[str] = None
    is_federally_listed: bool = False
    state_rank: Optional[str] = None
    tpwd_status: Optional[str] = None

    # Location cache
    county_name: Optional[str] = None
    county_id: Optional[int] = None
    locality_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_aquatic_karst: bool = False
    is_terrestrial_karst: bool = False