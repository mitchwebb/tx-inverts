from uuid import UUID
from pydantic import BaseModel


# County information model
class County(BaseModel):
    id: UUID
    county: str


# Park information model
class Park(BaseModel):
    id: UUID
    prop_name: str
    alt_prop_name: str
    prop_class: str
    owner: str
