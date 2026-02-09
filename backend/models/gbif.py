from enum import Enum

class GBIFFormat(str, Enum):
    dwca = "DWCA"
    simple_csv = "SIMPLE_CSV"