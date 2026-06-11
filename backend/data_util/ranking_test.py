import pytest
from backend.data_util.ranking import calculate_rank


@pytest.mark.parametrize(
    "occurrences,range_extent,area_of_occupancy,expected_rank", [
        (22,   998,         4,      '2'),
        (66,   2345,        100,    '3'),
        (342,  6723,        27,     '4'),
        (300,  10000000000, 4,      '3'),
        (0,    0,          None,    'u'),
        (10,   10,         1000000, '4'),
        (1000, 1000,       None,    '4'),
    ])
def test_valid_rank_calculations(occurrences, range_extent, area_of_occupancy, expected_rank):
    assert calculate_rank(occurrences, range_extent,
                          area_of_occupancy) == expected_rank
