from pydantic import BaseModel
from typing import Optional, List


class TaxonRequest(BaseModel):
    taxon_id: int
    taxon_rank: Optional[str] = None


class ObservationsRequest(TaxonRequest):
    include_inat: bool
    data_providers: Optional[List[str]] | None = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None


class TextData(BaseModel):
    text: str
