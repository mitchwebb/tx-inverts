from pydantic import BaseModel
from typing import Literal, List

# Literal type for possible NSRanks
NSRank = Literal['x', 'h', '1', '2', '3', '4', '5', 'u']


# Params used to make queries for multiple taxon information only
class TaxaRequestParams(BaseModel):
    taxon_ids: List[str]
    taxon_rank: str | None = None
    ns_ranks: List[NSRank] | None = None


# Params used to make queries for a single taxon
class TaxonRequestParams(BaseModel):
    taxon_id: str
    taxon_rank: str | None = None
    ns_ranks: List[NSRank] | None = None


# Params used to filter observation data
class ObsRequestParams(BaseModel):
    include_inat: bool | None = True
    datasets: List[str] | None = None
    date_start: str | None = None
    date_end: str | None = None
    include_invasives: bool | None = False
    regions: List[str] | None = None
    coord_uncertainty: int | None = None


# Class for observations requests for multiple taxa
class MultiTaxaObsRequestParams(TaxaRequestParams, ObsRequestParams):
    pass


# Class for observations request for a single taxon
class SingleTaxonObsRequestParams(TaxonRequestParams, ObsRequestParams):
    pass


# Params used to make download request queries
class DownloadRequestParams(MultiTaxaObsRequestParams):
    get_estimate: bool = False  # If true, trigger query size estimate


class TextData(BaseModel):
    text: str
