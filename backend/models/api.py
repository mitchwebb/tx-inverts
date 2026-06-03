from pydantic import BaseModel
from typing import Literal, List

# Literal type for possible NSRanks
NSRank = Literal['x', 'h', '1', '2', '3', '4', '5', 'u']


# Params used to make queries for taxon information only
class TaxaRequestParams(BaseModel):
    taxon_ids: List[int] | int | None = None
    taxon_rank: str | None = None
    ns_ranks: List[NSRank] | None = None


# Params used to make queries which rely on filtered observation data
class ObservationsRequestParams(TaxaRequestParams):
    include_inat: bool | None = True
    datasets: List[str] | None = None
    date_start: str | None = None
    date_end: str | None = None
    include_invasives: bool | None = False
    # List of UUIDs from the regions table
    regions: List[str] | None = None


# Params used to make download request queries
class DownloadRequestParams(ObservationsRequestParams):
    estimate: bool = False  # If true, trigger query size estimate


class TextData(BaseModel):
    text: str
