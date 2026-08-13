import pytest

from backend.data_util.case import camel_to_snake_case


@pytest.mark.parametrize('input_string, expected', [
    ('gbifID', 'gbif_id'),
    ('institutionCode', 'institution_code'),
    ('verbatimEventDate', 'verbatim_event_date'),
    ('coordinateUncertaintyInMeters', 'coordinate_uncertainty_in_meters'),
    ('issue', 'issue'),
    ('taxon_key', 'taxon_key'),
    ('1223', '1223'),
    ('CAPITALS', 'capitals'),
    ('wordsANDAcronyms', 'words_and_acronyms'),
    ('', '')
])
@pytest.mark.asyncio
async def test_converts_camel_case(input_string, expected):
    assert camel_to_snake_case(input_string) == expected
