from uuid import UUID
from pydantic import BaseModel


class County(BaseModel):
    id: UUID
    county: str


class Park(BaseModel):
    id: UUID
    prop_name: str
    alt_prop_name: str
    prop_class: str
    owner: str
