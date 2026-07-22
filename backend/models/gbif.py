from enum import Enum


# Small class to keep track of legitimate GBIF Format types
class GBIFFormat(str, Enum):
    dwca = 'DWCA'
    simple_csv = 'SIMPLE_CSV'
