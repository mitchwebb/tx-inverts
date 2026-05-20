from pydantic import BaseModel
from typing import Literal, Optional, List

# Literal type for possible NSRanks
NSRank = Literal['x', 'h', '1', '2', '3', '4', '5', 'u']


# Params used to make queries for taxon information only
class TaxaRequestParams(BaseModel):
    taxon_ids: Optional[List[int] | int] = None
    taxon_rank: Optional[str] = None
    ns_ranks: Optional[List[NSRank]] = None


# Params used to make queries which rely on filtered observation data
class ObservationsRequestParams(TaxaRequestParams):
    include_inat: Optional[bool] = True
    datasets: Optional[List[str]] | None = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    include_invasives: Optional[bool] = False
    # List of UUIDs from the regions table
    regiosns: Optional[List[str]] = None


# Params used to make download request queries
class DownloadRequestParams(ObservationsRequestParams):
    estimate: bool = False  # If true, trigger query size estimate


class TextData(BaseModel):
    text: str
