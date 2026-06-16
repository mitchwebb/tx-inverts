from backend.data_util.gbif.process_observations import parse_date_range_string, parse_dwc_dates
import pandas as pd

# TODO: Fill these test cases out


def make_row(**kwargs):
    """Build a minimal single-row DataFrame with DWC defaults."""
    defaults = {
        'eventDate': '', 'verbatimEventDate': '', 'eventRemarks': '',
        'year': None, 'month': None, 'day': None,
    }
    return pd.DataFrame([{**defaults, **kwargs}])


class TestParseDWCDates:
    def test_date_range_supercedes_dmy(self):
        df = make_row(eventDate='2021-02-21/2021-03-21', year='2023')
        result = parse_dwc_dates(df).iloc[0]
        assert result['collectionStartDate'] == '2021-02-21'
        assert result['collectionEndDate'] == '2021-03-21'


# Test date range parsing
# Note: Some of these are just re-testing regex, but... that's not a huge issue
class TestParseDateRangeString:
    # Good ranges
    def test_full_ymd_range(self):
        assert parse_date_range_string(
            '2001-06-25/2001-06-27') == ['2001-06-25', '2001-06-27']

    def test_year_month_only(self):
        assert parse_date_range_string(
            '2001-06/2001-07') == ['2001-06', '2001-07']

    def test_year_only(self):
        assert parse_date_range_string('2001/2002') == ['2001', '2002']

    def test_zero_pads_single_digit_month_and_day(self):
        assert parse_date_range_string(
            '2001-6-5/2001-7-3') == ['2001-06-05', '2001-07-03']

    # Failure cases — should return [None, None]
    def test_missing_slash(self):
        assert parse_date_range_string('2001-06-25') == [None, None]

    def test_too_many_slashes(self):
        assert parse_date_range_string('2001/06/25') == [None, None]

    def test_empty_string(self):
        assert parse_date_range_string('') == [None, None]

    def test_invalid_dates(self):
        assert parse_date_range_string('not-a-date/also-not') == [None, None]

    # Asymmetric cases
    def test_mismatched_precision(self):
        # start has YMD, end has only year
        result = parse_date_range_string('2001-06-25/2001')
        assert result == ['2001-06-25', '2001']
