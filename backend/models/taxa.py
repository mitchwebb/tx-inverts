# Taxon related models
from typing import List

from pydantic import BaseModel, ConfigDict, Field, alias_generators
from backend.constants.taxa import TaxonomicRank


class TaxonSuggestion(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )
    canonical_name: str | None
    scientific_name_authorship: str | None
    taxon_id: str = Field(alias='taxonID')
    taxon_rank: str | None
    us_invasive: bool | None = Field(alias='uSInvasive')
    taxonomic_status: str | None


class TaxonInfo(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )
    # Fit convention of acronym caps
    taxon_id: str = Field(alias='taxonID')
    scientific_name_authorship: str | None
    vernacular_names: List[str] | None
    # Fit convention of acronym caps
    accepted_name_usage_id: str | None = Field(
        None, alias='acceptedNameUsageID')
    # Fit convention of acronym caps
    parent_name_usage_id: str | None = Field(None, alias='parentNameUsageID')
    canonical_name: str | None
    scientific_name: str | None
    taxon_rank: TaxonomicRank | None
    us_invasive: bool | None = Field(None, alias='uSInvasive')
    taxonomic_status: str | None
    ns_rank_state: str | None = Field(None, alias='nSRankState')
    ns_rank_state_no_inat: str | None = Field(None, alias='nSRankStateNoINat')
    kingdom: str | None
    phylum: str | None
    # Aliased for reserved word 'class'
    taxon_class: str | None = Field(None, alias='class')
    order: str | None
    family: str | None
    generic_name: str | None
    infrageneric_epithet: str | None
    specific_epithet: str | None
    infraspecific_epithet: str | None
