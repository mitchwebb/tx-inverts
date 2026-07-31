from typing import Annotated, List
from pydantic import BeforeValidator, ConfigDict, field_validator, BaseModel, model_validator
from datetime import date, datetime


def _normalize_taxon_ids(v: int | List[int] | str | None): return ([1] if v is None else [
    int(v)] if isinstance(v, (int, str)) else v)


# Model for OccurrenceFilters
# Includes validation and normalization of various params
class OccurrenceFilters(BaseModel):
    # Normalize taxon_ids to list, default to [1] (Animalia) if None provided
    taxon_ids: Annotated[
        List[int],
        BeforeValidator(_normalize_taxon_ids)
    ] = [1]
    include_inat: bool | None = True
    datasets: List[str] | None = None
    include_invasives: bool = False
    date_start: date | str | None = None
    date_end: date | str | None = None
    regions: List[str] | None = None
    coord_uncertainty: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Convert include_inat None to True
    @field_validator('include_inat', mode='before')
    def normalize_include_inat(cls, v):
        return True if v is None else v

    # These validators are really only necessary with our tile request, as nulls are passed as 'null'
    @field_validator('datasets', mode='before')
    def normalize_datasets(cls, v):
        if v is None or v in ('null', '', 'undefined'):
            return None
        # If it's a comma-separated string, convert to list
        if isinstance(v, str):
            result = [p for p in v.split(
                ',') if p not in ('null', '', 'undefined')]
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
        if v is None or v in ('null', '', 'undefined'):
            return None
        if isinstance(v, str):
            result = [r for r in v.split(
                ',') if r not in ('null', '', 'undefined')]
            return result or None
        return v
