# Taxon related models
from typing import List

from pydantic import BaseModel, Field
from backend.constants.taxa import TaxonomicRank


class TaxonSuggestion(BaseModel):
    canonical_name: str | None
    scientific_name_authorship: str | None
    taxon_id: str | None
    taxon_rank: str | None
    us_invasive: bool | None
    taxonomic_status: str | None


class TaxonInfo(BaseModel):
    scientific_name_authorship: str | None
    vernacular_names: List[str] | None
    accepted_name_usage_id: int | None
    canonical_name: str | None
    scientific_name: str | None
    taxon_rank: TaxonomicRank | None
    us_invasive: bool | None
    taxonomic_status: str | None
    ns_rank_state: str | None
    ns_rank_state_no_inat: str | None
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


# Class for backbone tree node (used for frontend table display and navigation)
class TaxonTreeNode(BaseModel):
    taxon_id: str | None
    taxon_rank: str | None
    parent_name_usage_id: str | None
    accepted_name_usage_id: str | None
    scientific_name: str | None
    scientific_name_authorship: str | None
    canonical_name: str | None
    ns_rank_state: str | None
    ns_rank_state_no_inat: str | None
    taxonomic_status: str | None
    us_invasive: bool | None
    phylum: str | None
    # Aliased for reserved word 'class'
    taxon_class: str | None = Field(None, alias='class')
    order: str | None
    family: str | None
    generic_name: str | None
    infrageneric_epithet: str | None
    specific_epithet: str | None
    infraspecific_epithet: str | None
