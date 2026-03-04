from pydantic import BaseModel
from typing import Literal, Optional, List


NSRank = Literal['x', 'h', '1', '2', '3', '4', '5', 'u']


# Params used to make queries for taxon information only
class TaxaRequestParams(BaseModel):
    taxon_ids: List[int] | int
    taxon_rank: Optional[str] = None
    ns_ranks: Optional[List[NSRank]] = None


# Params used to make queries which rely on filtered observation data
class ObservationsRequestParams(TaxaRequestParams):
    include_inat: Optional[bool] = True
    data_providers: Optional[List[str]] | None = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    include_invasives: Optional[bool] = False


# Params used to make download request queries
class DownloadRequestParams(ObservationsRequestParams):
    estimate: bool = False  # If true, trigger query size estimate


class TextData(BaseModel):
    text: str
