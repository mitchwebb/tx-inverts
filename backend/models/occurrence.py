from typing import List
from pydantic import computed_field, field_validator, BaseModel, model_validator
from datetime import date, datetime


# Model for OccurrenceFilter (typically made with create_occurrence_filter)
# Includes validation and normalization of various params
class OccurrenceFilter(BaseModel):
    taxon_ids: List[int] | None = None
    include_inat: bool = True
    datasets: List[str] | None = None
    include_invasives: bool = False
    date_start: date | None = None
    date_end: date | None = None
    regions: List[str] | None = None

    @field_validator('taxon_ids', mode='before')
    def normalize_taxon_ids(cls, v):
        # Default to Animalia if taxon_ids not provided
        if v is None:
            return [1]
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [int(v)]
        return v

    # These validators are really only necessary with our tile request, as nulls are passed as 'null'
    @field_validator('datasets', mode='before')
    def normalize_datasets(cls, v):
        if v is None or v in ("null", "", "undefined"):
            return None
        # If it's a comma-separated string, convert to list
        if isinstance(v, str):
            result = [p for p in v.split(
                ',') if p not in ("null", "", "undefined")]
            return result or None
        return v

    @field_validator('date_start', 'date_end', mode='before')
    def normalize_dates(cls, v):
        if v in ('null', '', 'undefined') or v is None:
            return None
        if isinstance(v, date):
            return v  # already a date, pass through
        return datetime.fromisoformat(v).date()

    @field_validator('regions', mode='before')
    def normalize_regions(cls, v):
        if v is None or v in ("null", "", "undefined"):
            return None
        if isinstance(v, str):
            result = [r for r in v.split(
                ',') if r not in ("null", "", "undefined")]
            return result or None
        return v


# Version of occurrence filter for a single taxon
class SingleTaxonOccurrenceFilter(OccurrenceFilter):
    # Allow use of taxon_id param, as it makes more sense here
    @model_validator(mode='before')
    @classmethod
    def handle_taxon_id_alias(cls, values):
        if 'taxon_id' in values and 'taxon_ids' in values:
            raise ValueError('Cannot specify both taxon_id and taxon_ids')
        if 'taxon_id' in values:
            values['taxon_ids'] = [values.pop('taxon_id')]
        return values

    @model_validator(mode='after')
    def validate_single_taxon(self):
        if len(self.taxon_ids) != 1:
            raise ValueError(
                'SingleTaxonFilter only supports a single taxon_id')
        return self

    @computed_field
    @property
    def taxon_id(self) -> int:
        return self.taxon_ids[0]
