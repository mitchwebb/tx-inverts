from typing import Optional, List
from pydantic import computed_field, field_validator, BaseModel, model_validator
from datetime import date, datetime


class OccurrenceFilter(BaseModel):
    taxon_ids: List[int]
    include_inat: bool = True
    data_providers: Optional[List[str]] = None
    exclude_invasive: bool = True
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    regions: Optional[List[str]] = None

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
    @field_validator('data_providers', mode='before')
    def normalize_providers(cls, v):
        if v is None or v in ("null", "", "undefined"):
            return []
        # If it's a comma-separated string, convert to list
        if isinstance(v, str):
            return [p for p in v.split(',') if p not in ("null", "", "undefined")]
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
            return []
        if isinstance(v, str):
            return [r for r in v.split(',') if r not in ("null", "", "undefined")]
        return v


class SingleTaxonOccurrenceFilter(OccurrenceFilter):
    # Allow use of taxon_id param, as it makes more sense here
    @model_validator(mode='before')
    @classmethod
    def handle_taxon_id_alias(cls, values):
        if 'taxon_id' in values and 'taxon_ids' not in values:
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
