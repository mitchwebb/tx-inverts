import datetime
from typing import Any

from pandas import DataFrame, Series
import pytest
from backend.data_util.gbif.process_observations import filter_texas_bounding_box, parse_date_to_date_range_string, parse_iso_date_range_string, parse_dwc_dates, parse_iso_date_string, process_dwc_observations
import pandas as pd
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE


def make_row(**kwargs):
    """Build a minimal single-row DataFrame with DWC defaults."""
    defaults = {
        'eventDate': '', 'verbatimEventDate': '', 'eventRemarks': '',
        'year': None, 'month': None, 'day': None,
    }
    return pd.DataFrame([{**defaults, **kwargs}])


def parse_single_dwc_row(**kwargs) -> Series:
    df = make_row(**kwargs)
    result = parse_dwc_dates(df).iloc[0]
    return result


class TestParseDWCDates:
    # We trust ISO format, even when day and month could be swapped
    # yyyy-dd-mm is so uncommon (it's not even recognized)
    def test_parses_iso_date(self):
        result = parse_single_dwc_row(eventDate='2021-03-04')
        assert result['collectionStartDate'] == '2021-03-04'

    # Test this odd A&M format that shows up in eventRemarks
    def test_parses_semicolon_end_date(self):
        result = parse_single_dwc_row(
            eventDate='2021-02-01', eventRemarks='; ended 2021-03-04')
        assert result['collectionStartDate'] == '2021-02-01'
        assert result['collectionEndDate'] == '2021-03-04'

    def test_parses_unambiguous_datetime_string(self):
        result = parse_single_dwc_row(eventDate='8/22/2013 11:15:41 AM')
        assert result['collectionStartDate'] == '2013-08-22'

    # Make sure date range is retrieved over individual date
    def test_date_range_supercedes_dmy_columns(self):
        result = parse_single_dwc_row(
            eventDate='2021-02-21/2021-03-21',
            year='2023'
        )
        assert result['collectionStartDate'] == '2021-02-21'
        assert result['collectionEndDate'] == '2021-03-21'

    # Test that unambiguous date with spelled month is assigned
    def test_verbatim_unambiguous_spelled_date(self):
        result = parse_single_dwc_row(verbatimEventDate='2 April 2000')
        assert result['collectionStartDate'] == '2000-04-02'

    # Reject two digit years (can't be fully trusted)
    def test_rejects_two_digit_year(self):
        result = parse_single_dwc_row(eventRemarks='22-Apr-00')
        assert result['collectionStartDate'] == None

    # Reject two digit roman years (can't be fully trusted)
    def test_rejects_two_digit_roman_year(self):
        result = parse_single_dwc_row(verbatimEventDate='22-VI-97')
        assert result['collectionStartDate'] == None

    def test_parses_unambiguous_dot_separated_date(self):
        result = parse_single_dwc_row(eventRemarks='19.VIII.2022')
        assert result['collectionStartDate'] == '2022-08-19'

    # Parse out lone year as date
    def test_parses_lone_year(self):
        result = parse_single_dwc_row(verbatimEventDate='1960')
        assert result['collectionStartDate'] == '1960'

    # Reject day-month date (spelled)
    def test_rejects_spelled_dm(self):
        result = parse_single_dwc_row(eventDate='20-Apr')
        assert result['collectionStartDate'] == None

    # Reject day-month date (numeric)
    def test_rejects_numeric_dm(self):
        result = parse_single_dwc_row(verbatimEventDate='20-04')
        assert result['collectionStartDate'] == None

    # Reject month-day date (spelled)
    def test_rejects_spelled_md(self):
        result = parse_single_dwc_row(eventRemarks='Apr-20')
        assert result['collectionStartDate'] == None

    # Reject month-day date (numeric)
    def test_rejects_numeric_md(self):
        result = parse_single_dwc_row(verbatimEventDate='04-20')
        assert result['collectionStartDate'] == None

    # Reject lone spelled month
    def test_rejects_lone_month(self):
        result = parse_single_dwc_row(eventDate='April')
        assert result['collectionStartDate'] == None

    # While this could sometimes be an valid, unambiguous date, it is safer to reject
    def test_rejects_datelike_number(self):
        result = parse_single_dwc_row(verbatimEventDate='12242009')
        assert result['collectionStartDate'] == None

    # While the month and day are ambiguous here, the year is not
    def test_retrieves_unambiguous_year(self):
        result = parse_single_dwc_row(eventRemarks='1/5/1937')
        assert result['collectionStartDate'] == '1937'

    def test_retrieves_roman_my(self):
        result = parse_single_dwc_row(eventDate='VIII-1897')
        assert result['collectionStartDate'] == '1897-08'

    def test_parses_roman_dmy(self):
        result = parse_single_dwc_row(verbatimEventDate='6-V-1999')
        assert result['collectionStartDate'] == '1999-05-06'

    def test_parses_roman_mdy(self):
        result = parse_single_dwc_row(eventRemarks='V-6-1999')
        assert result['collectionStartDate'] == '1999-05-06'

    # Make sure that Roman numerals are more strictly adhered to
    # Prevent IIV from being read like IV
    def test_rejects_fake_romans(self):
        result = parse_single_dwc_row(verbatimEventDate='IIV-5-1995')
        assert result['collectionStartDate'] == None

    def test_rejects_future_date(self):
        # Construct ISO style date for one year from now
        today = datetime.date.today()
        next_year_string = f'{today.year + 1}-{today.month}-{today.day}'
        result = parse_single_dwc_row(verbatimEventDate=next_year_string)
        assert result['collectionStartDate'] == None

    def test_rejects_mdy_zeroes_year(self):
        result = parse_single_dwc_row(eventDate='02/28/0000')
        assert result['collectionStartDate'] == None

    def test_rejects_dmy_zeroes_year(self):
        result = parse_single_dwc_row(verbatimEventDate='28/02/0000')
        assert result['collectionStartDate'] == None

    def test_rejects_ymd_zeroes_year(self):
        result = parse_single_dwc_row(eventRemarks='0000-04-28')
        assert result['collectionStartDate'] == None

    def test_drops_ambiguous_dm(self):
        result = parse_single_dwc_row(verbatimEventDate='4/4/1987')
        assert result['collectionStartDate'] == '1987'

    def test_parses_compact_spelled_dmy(self):
        result = parse_single_dwc_row(verbatimEventDate='08SEP1995')
        assert result['collectionStartDate'] == '1995-09-08'

    def test_rejects_mismatched_separators(self):
        result = parse_single_dwc_row(eventDate='Oct. 1-15, 1927')
        # Preserve consistent year
        assert result['collectionStartDate'] == '1927'

    def test_gets_first_of_unrecognized_range(self):
        result = parse_single_dwc_row(eventRemarks='X-1971--III-1972')
        assert result['collectionStartDate'] == '1971-10'

    def test_parses_date_to_date_string(self):
        result = parse_single_dwc_row(
            eventDate='2021-04-23 to 2021-05-28')
        assert result['collectionStartDate'] == '2021-04-23'
        assert result['collectionEndDate'] == '2021-05-28'

    # Uncaught Date Types
    # 'X-1971--III-1972' (Catching -- as a range feels... questionable)
    # '10 to 24 August' 2009 OR '25 April to 24 June 2013' (Opening up this door would be dangerous)
    # We currently get uncertain ranges like this unpredictably. In the above cases, we get the end date as the collection date.

    # NOTE: While this behavior would be ideal, we're letting these
    # cases go for now. This opens up additional doors more than it recovers dates
    # def test_gets_unambiguous_to_range_string(self):
    #     df = make_row(verbatimEventDate='02 Jan 1999 to 31 Dec 2001')
    #     result = parse_dwc_dates(df).iloc[0]
    #     assert result['collectionStartDate'] == '1999-01-02'
    #     assert result['collectionEndDate'] == '2001-12-31'

    # # Is this behavior that we want? Or will this lead to more false dates?
    # def test_parses_year_range(self):
    #     df = make_row(verbatimEventDate='2001-2002')
    #     result = parse_dwc_dates(df).iloc[0]
    #     assert result['collectionStartDate'] == '2001'
    #     assert result['collectionEndDate'] == '2002'


class TestParseISODateString:
    # Test that, when given two dates, the first date is returned
    def test_gets_first_date(self):
        parsed = parse_iso_date_string('2001-06-25/2001-06-27')
        assert parsed == '2001-06-25'

    def test_parses_ym(self):
        parsed = parse_iso_date_string('2025-1')
        assert parsed == '2025-01'


class TestParseDatetoDateRangeString:
    def test_parses_iso_date_to_date(self):
        start_date, end_date = parse_date_to_date_range_string(
            '2021-03-04 to 2024-05-06')
        assert start_date == '2021-03-04'
        assert end_date == '2024-05-06'

    def test_parses_unambiguous_mdy_date_to_date(self):
        start_date, end_date = parse_date_to_date_range_string(
            '04/23/2023 to 04/27/2023')
        assert start_date == '2023-04-23'
        assert end_date == '2023-04-27'

    def test_rejects_ambiguous_month_and_day(self):
        start_date, end_date = parse_date_to_date_range_string(
            '04/05/2023 to 04/06/2023')
        assert start_date == '2023'
        assert end_date == '2023'

    def test_rejects_uneven_range(self):
        start_date, end_date = parse_date_to_date_range_string(
            '04/2023 to 04/06/2023')
        assert start_date == None
        assert end_date == None

    def test_parses_year_to_year_string(self):
        start_date, end_date = parse_date_to_date_range_string(
            '1992 to 1993')
        assert start_date == '1992'
        assert end_date == '1993'


# Test date range parsing
# Note: Some of these are just re-testing regex, but... that's not a huge issue


class TestParseIsoDateRangeString:
    # Good ranges
    def test_full_ymd_range(self):
        assert parse_iso_date_range_string(
            '2001-06-25/2001-06-27') == ['2001-06-25', '2001-06-27']

    def test_year_month_only(self):
        assert parse_iso_date_range_string(
            '2001-06/2001-07') == ['2001-06', '2001-07']

    def test_year_only(self):
        assert parse_iso_date_range_string('2001/2002') == ['2001', '2002']

    def test_zero_pads_single_digit_month_and_day(self):
        assert parse_iso_date_range_string(
            '2001-6-5/2001-7-3') == ['2001-06-05', '2001-07-03']

    # Failure cases — should return [None, None]
    def test_missing_slash(self):
        assert parse_iso_date_range_string('2001-06-25') == [None, None]

    def test_too_many_slashes(self):
        assert parse_iso_date_range_string('2001/06/25') == [None, None]

    def test_empty_string(self):
        assert parse_iso_date_range_string('') == [None, None]

    def test_invalid_dates(self):
        assert parse_iso_date_range_string(
            'not-a-date/also-not') == [None, None]

    # Asymmetric cases should return [None, None]
    def test_mismatched_precision(self):
        result = parse_iso_date_range_string('2001-06-25/2001')
        assert result == [None, None]


# Test that bounding box filter removes outliers and returns filtered db
def test_filter_texas_bounding_box():
    df = pd.DataFrame([
        # Keep: Squarely in TX
        {'id': 1, 'decimalLongitude': -99, 'decimalLatitude': 31},
        # Drop: Kansas
        {'id': 2, 'decimalLongitude': -97, 'decimalLatitude': 38},
        # Drop: None values
        {'id': 3, 'decimalLongitude': None, 'decimalLatitude': None},
    ])

    filtered = filter_texas_bounding_box(df)
    assert set(filtered['id']) == {1}


# Test the general flow of process_dwc_observations, including column renaming/removal
# and filling of 'species' column from 'specificEpithet' column
def test_process_dwc_observations(tmp_path):
    tsv = tmp_path / 'obs.tsv'
    rows = [
        ['gbifID', 'decimalLongitude', 'decimalLatitude',
            'eventDate', 'specificEpithet'],
        # valid TX record
        ['1', '-99.0', '31.0', '2021-01-01', 'texanus'],
        # Null Island - filtered
        ['2', '0.0',   '0.0',  '2021-01-01', 'nullus'],
        # bad date - filtered
        ['3', '-99.0', '31.0', 'baddate',    'texanus'],
    ]
    tsv.write_text('\n'.join('\t'.join(row) for row in rows))

    chunks = list(process_dwc_observations(tsv, chunk_size=5))

    assert len(chunks) == 1  # Only one chunk
    result = chunks[0]
    assert len(result) == 1  # Only one processed row
    # Snake case column name, int, return row 1
    assert result.iloc[0]['gbif_id'] == 1
    # Species column populates from specificEpithet
    assert result.iloc[0]['species'] == 'texanus'
    # specificEpithet column should be filtered out
    assert 'specificEpithet' not in result.columns
    assert set(result.columns) == set(
        # Columns match observations table column order
        GBIF_OBSERVATIONS_TABLE.column_order())
