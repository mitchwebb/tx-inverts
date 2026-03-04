from typing import Optional, List
from pydantic import field_validator, BaseModel


class OccurrenceFilter(BaseModel):
    taxon_id: int
    include_inat: bool = True
    data_providers: Optional[List[str]] = None
    exclude_invasive: bool = True
    date_start: Optional[str] = None
    date_end: Optional[str] = None

    # For now, we are only allowing one taxon_id for OccurrenceFilters
    # Even if we allow multiple active species in the future, each species
    # will need its own request

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
        if v in ('null', '', 'undefined'):
            return None
        return v
