import pandas as pd
import pytest

from backend.data_util.invasives_data import prep_invasives_dataset
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE

# Test taxon data for
test_data = [
    {
        'kingdom': 'Plantae',
        'phylum': 'Tracheophyta',
        'class': 'Ascidiacea',
        'taxonRank': 'SPECIES',
        'taxonKey': '4283320'
    },
    {
        'kingdom': 'Animalia',
        'phylum': 'Arthropoda',
        'class': 'Leptocardii',
        'taxonRank': 'SPECIES',
        'taxonKey': '7417639'
    },
    {
        'kingdom': 'Plantae',
        'phylum': 'Tracheophyta',
        'class': 'Appendicularia',
        'taxonRank': 'SPECIES',
        'taxonKey': '2337575'
    },
    {
        'kingdom': 'Viruses',
        'phylum': 'Uroviricota',
        'class': 'Thaliacea',
        'taxonRank': 'SPECIES',
        'taxonKey': '2273178'
    },
    {
        'kingdom': 'Animalia',
        'phylum': 'Chordata',
        'class': 'Mammalia',
        'taxonRank': 'SPECIES',
        'taxonKey': '370529'
    },
    {
        'kingdom': 'Plantae',
        'phylum': 'Tracheophyta',
        'class': 'Appendicularia',
        'taxonRank': 'SPECIES',
        'taxonKey': '4308480'
    },
    {
        'kingdom': 'Animalia',
        'phylum': 'Bryozoa',
        'class': 'Leptocardii',
        'taxonRank': 'SPECIES',
        'taxonKey': '2362833'
    },
    {
        'kingdom': 'Chromista',
        'phylum': 'Foraminifera',
        'class': 'Ascidiacea',
        'taxonRank': 'SPECIES',
        'taxonKey': '1539725'
    },
    {
        'kingdom': 'Animalia',
        'phylum': 'Arthropoda',
        'class': 'Insecta',
        'taxonRank': 'PHYLUM',
        'taxonKey': '6173164'
    },
    {
        'kingdom': 'Plantae',
        'phylum': 'Tracheophyta',
        'class': 'Magnoliopsida',
        'taxonRank': 'SPECIES',
        'taxonKey': '4289850'
    },
]

test_df = pd.DataFrame(test_data)


# Test invasives filtering behaviors
# I could split these out, but honestly, it's a pretty simple filter
@pytest.mark.asyncio
async def test_prep_invasives_filter():
    result = await prep_invasives_dataset(test_df)
    # Non-Animalia (Plantae) excluded
    assert '4283320' not in result['taxon_id'].values
    # Animalia, non-Chordata included
    assert '7417639' in result['taxon_id'].values
    # Animalia, Chordata, not in special classes excluded
    assert '370529' not in result['taxon_id'].values
    # Animalia, Chordata special cases included
    assert '2362833' in result['taxon_id'].values
    # Greater taxonRanks excluded (PHYLUM)
    assert '6173164' not in result['taxon_id'].values


# See that prep_invasives successfully outputs coerced tabled
@pytest.mark.asyncio
async def test_prep_invasives_coerces_columns():
    result = await prep_invasives_dataset(test_df)
    assert set(result.columns) == set(US_INVASIVES_TABLE.column_order())
