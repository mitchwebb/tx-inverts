# Logic for processing/filtering GBIF observations downloads in darwincore format
import datetime
import os
from typing import Iterator, cast

from backend.constants.paths import DATA_OUT_PATH
from backend.core.logging import data_logger
from pandas import DataFrame
from geopandas.geodataframe import GeoDataFrame
import pandas as pd
import csv
import re

from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.types.occurrence import GBIFObservationRow


### Constants for date processing ###

# Map of month names/abbreviations to numbers
MONTH_LOOKUP = {
    'january': 1, 'jan': 1, 'jan.': 1, 'i': 1, 'i.': 1,
    'february': 2, 'feb': 2, 'feb.': 2, 'ii': 2, 'ii.': 2,
    'march': 3, 'mar': 3, 'mar.': 3, 'iii': 3, 'iii.': 3,
    'april': 4, 'apr': 4, 'apr.': 4, 'iv': 4, 'iv.': 4,
    'may': 5, 'v': 5, 'v.': 5,
    'june': 6, 'jun': 6, 'jun.': 6, 'vi': 6, 'vi.': 6,
    'july': 7, 'jul': 7, 'jul.': 7, 'vii': 7, 'vii.': 7,
    'august': 8, 'aug': 8, 'aug.': 8, 'viii': 8, 'viii.': 8,
    'september': 9, 'sep': 9, 'sept': 9, 'sep.': 9, 'sept.': 9, 'ix': 9, 'ix.': 9,
    'october': 10, 'oct': 10, 'oct.': 10, 'x': 10, 'x.': 10,
    'november': 11, 'nov': 11, 'nov.': 11, 'xi': 11, 'xi.': 11,
    'december': 12, 'dec': 12, 'dec.': 12, 'xii': 12, 'xii.': 12,
}
MONTH_NAMES = '|'.join(re.escape(m) for m in MONTH_LOOKUP.keys())

# DWC Should use ISO 8601. This is what GBIF does.
# Strict YYYY, YYYY-MM, YYYY-MM-DD matching
ISO_YMD_PATTERN = (
    # No preceding digits OR letters OR '-' (which prevents erroneous partial matches), or '.' (which does reasonably get used)
    rf'(?<![\dA-Za-z\-/.])'
    # Year (required, four digits, not before 999)
    r'(?P<year>[1-9]\d{3})'
    # Optional group start
    # Month (optional)
    r'(?:-(?P<month>0?[1-9]|1[0-2])'
    # Day (optional, requires month)
    r'(?:-(?P<day>0?[1-9]|[12][0-9]|3[01]))?)?'
    # No trailing digits
    r'(?!\d)'
)
ISO_YMD_REGEX = re.compile(ISO_YMD_PATTERN, re.IGNORECASE)

# Ambigious DMY strings (will match on something like 01/06/2023)
AMBIGUOUS_DMY_PATTERN_REGEX = re.compile(
    # No preceding digits, letters, or dash
    rf'(?<![\dA-Za-z\-/])'
    # Day (optional), including number suffixes, followed by separator
    r'(?:(?P<day>0?[1-9]|[12][0-9]|3[01])(?P<daySuffix>st|nd|rd|th)?(?P<sep>[\s\-/.,]+))?'
    # Month (required), either number or text
    rf'(?:(?P<monthNumber>0?[1-9]|1[0-2])|(?P<monthText>{MONTH_NAMES}))'
    # Same separator
    r'(?(sep)(?P=sep)|[\s\-/.,]+)'
    # Year (required, four digits, not before 999)
    r'(?P<year>[1-9]\d{3})'
    # No trailing digits
    r'(?!\d)',
    re.IGNORECASE
)

COMPACT_DMY_PATTERN_REGEX = re.compile(
    # No preceding digits, letters, or dash
    rf'(?<![\dA-Za-z\-/])'
    # Day (optional), including number suffixes, followed by separator
    r'(?:(?P<day>0?[1-9]|[12][0-9]|3[01]))?'
    # Month (required, spelled)
    rf'(?:(?P<monthText>{MONTH_NAMES}))'
    # Year (required, four digits, not before 999)
    r'(?P<year>[1-9]\d{3})'
    # No trailing digits
    r'(?!\d)',
    re.IGNORECASE
)

# Ambiguous MDY strings (will match on something like 01/06/2023)
AMBIGUOUS_MDY_PATTERN_REGEX = re.compile(
    # No preceding digits, letters, or dash
    rf'(?<![\dA-Za-z\-/])'
    # Month (required), either number or text
    rf'(?:(?P<monthNumber>0?[1-9]|1[0-2])|(?P<monthText>{MONTH_NAMES}))'
    # Separator
    r'(?P<sep>[\s\-/.,]+)'
    # Day (optional), including number suffixes
    r'(?P<day>0?[1-9]|[12][0-9]|3[01])(?P<daySuffix>st|nd|rd|th)?'
    # Same sep as earlier
    r'(?P=sep)'
    # Year (required, four digits, not before 999)
    r'(?P<year>[1-9]\d{3})'
    # No trailing digits
    r'(?!\d)',
    re.IGNORECASE
)

# Some unambiguous key words found in GBIF entries (followed by strict YMD matches)
EVENT_REMARKS_DATE_PATTERN = (
    r'(?P<keyword>dated|started|ended)[:= ]+' + ISO_YMD_PATTERN
)
EVENT_REMARKS_DATE_REGEX = re.compile(EVENT_REMARKS_DATE_PATTERN, re.IGNORECASE)


# Internal helper for parsing ambiguous matches
def _parse_ambiguous_match(match: re.Match[str]) -> dict[str, int | None] | None:
    """
    Parse ambiguous date match into unambiguous 'year', 'month', and 'day' groups

    Args:
        match (re.Match[str]): A re.match() result with possible match groups
            'year', 'month', 'monthNumber', 'monthText, 'day', and 'daySuffix'

    Returns:
        Parts dict (dict[str, int | None] | None): Dict of unambiguous date parts (or None)
    """

    # If no year is provided, date is useless
    groups = match.groupdict()

    if not groups.get('year'):
        return None
    day = groups.get('day')
    day_suffix = groups.get('daySuffix')
    month_number = groups.get('monthNumber')
    # Includes roman numerals
    month_text = groups.get('monthText')

    # Dict for final matched parts for return
    parts = {
        'year': int(match.group('year')),
        'month': None,
        'day': None
    }

    # Textual month match is always unambiguous
    if month_text:
        parts['month'] = MONTH_LOOKUP[month_text.lower().strip()]
        # If there is also a day, it is also unambiguous
        if day:
            parts['day'] = int(day)
    # Month number takes extra work
    elif month_number:
        # Consider month unambiguous if day is missing or if day is unambiguous
        if not day or day_suffix or (int(day) > 12):
            parts['month'] = int(month_number)
        # Day is unambiguous if day_suffix or day > 12
        if day and (day_suffix or int(day) > 12):
            parts['day'] = int(day)

    # If we have an unambiguous month (and year), our date is unambiguous
    return parts


def parse_iso_date_string(date_string: str) -> str | None:
    """
    Expecting a string in yyyy-MM-dd (ISO 8601) format, parse into a date string.
    Intentionally strict.

    When matching on multiple YMD dates, function will use first.

    Args:
        date_string (str): Date string to parse
    Returns:
        date string, or None if invalid
    """
    match = list(ISO_YMD_REGEX.finditer(date_string))

    if not match:
        return None
    elif len(match) > 1:
        data_logger.warning(
            f"Expected a single date, found {len(match)} in '{date_string}'")

    match = match[0]

    date = match.group('year')
    if match.group('month'):
        date += f'-{match.group('month').zfill(2)}'
        if match.group('day'):
            date += f'-{match.group('day').zfill(2)}'

    # Quick way to verify valid date format
    try:
        d = datetime.date(
            int(match.group('year')),
            int(match.group('month') or 1),
            int(match.group('day') or 1),
        )
    except ValueError:
        return None

    # Throw out future dates and return None
    if d > datetime.date.today():
        return None

    return date


# Strict range parsing
# TODO: Could be expanded to support other DWC range types
def parse_iso_date_range_string(range_string: str):
    """
    Expecting a string in yyyy-MM-dd/yyyy-MM-dd type format,
    parse into start_date and end_date. This is intentionally strict as
    date ranges can get... sticky.

    Args:
        range_string (str): Date string to parse

    Returns:
        [start_date, end_date], [None, None] if invalid
    """

    # Attempt to split on '/', return [None, None] if unable
    parts = range_string.split('/')
    if len(parts) != 2:
        return [None, None]

    start_date = parse_iso_date_string(parts[0])
    end_date = parse_iso_date_string(parts[1])

    if start_date is not None and end_date is not None:
        # Make sure they're of the same precision
        if start_date.count('-') != end_date.count('-'):
            # Else return Nones
            return [None, None]
        return [start_date, end_date]

    else:
        return [None, None]


def parse_date_to_date_range_string(range_string: str):
    parts = range_string.split('to')

    if len(parts) != 2:
        return [None, None]

    start_date = extract_date(parts[0])
    end_date = extract_date(parts[1])

    if start_date is not None and end_date is not None:
        # Make sure they're of the same precision
        if start_date.count('-') != end_date.count('-'):
            # Else return Nones
            return [None, None]
        return [start_date, end_date]

    else:
        return [None, None]


def parse_yyyy_yyyy_range_string(range_string: str):
    """Another intentionally specific case for a date range string."""

    match = re.match(r'^(\d{4})\s*-\s*(\d{4})$', range_string.strip())
    if not match:
        return [None, None]
    return [match.group(1), match.group(2)]


# TODO: Handling of 'to' ranges needs to be added. This is common enough. Although... GBIF doesn't parse these, and I'd argue that it's for a reason. At the very least, they should be ignored. Currently, they're treated unpredictably.
# Some basic date parsing for DarwinCore eventDates
def parse_dwc_dates(df: DataFrame) -> DataFrame | GeoDataFrame:
    """
    Using a pandas dataframe/geodataframe (assuming it's a DWC table),
    parse out a collectionStartDate and collectionEndDate, if possible

    yyyy-MM-dd/yyyy-MM-dd event_dates are assumed to be a range.
    HOWEVER, not all eventDate ranges are formatted this way.
    UTIC, for example:
        eventDate: '2001-06-25'
        eventRemarks: '; ended 2001-06-27'

    While the accuracy of individual dates is quite conservative,
    date ranges may be parsed partially. In these cases, one of the two
    dates may be taken and assumed as the eventDate, artificially 
    increasing precision. 

    Args:
        df (DataFrame): Pandas dataframe of DWC dataset

    Returns:
        df (DataFrame | GeoDataFrame): Input df with updated
            collectionStartDate and collectionEndDate columns
    """

    df = df.copy()  # don't mutate input

    required_columns = ['eventRemarks', 'eventDate',
                        'verbatimEventDate', 'year', 'month', 'day']

    # Add missing columns with NA values
    for col in required_columns:
        if col not in df.columns:
            df[col] = pd.NA

    # Ensure columns are strings, missing as empty string
    for col in ['eventRemarks', 'eventDate', 'verbatimEventDate']:
        df[col] = df[col].fillna('').astype(str)

    for col in ['year', 'month', 'day']:
        # Convert cols to numeric
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add new columns for start/end dates
    # TODO: This could be done in a more DarwinCore way, using startDayOfYear and endDayOfYear, but it will require more changes
    df['collectionStartDate'] = pd.NA
    df['collectionEndDate'] = pd.NA

    # date_audit = []

    # Iterate through rows
    for row in df.itertuples(index=True):
        # original_event_date = row.eventDate

        idx = row.Index

        # Cast row type to GBIFObservationsRow for type recognition
        row = cast(GBIFObservationRow, row)

        start_date = None
        end_date = None

        # First check for yyyy-MM-dd/yyyy-MM-dd format in eventDate
        # This is common across several institutions, and seems safe
        if row.eventDate:
            [start_date, end_date] = parse_iso_date_range_string(row.eventDate)
            if start_date and end_date:
                df.at[idx, 'collectionStartDate'] = start_date
                df.at[idx, 'collectionEndDate'] = end_date
                # If matched here, move to next row
                continue

        # If no match, we'll assign start date from 'year', 'month', 'day' columns
        # This is the most trustworthy source for single dates
        dwc_ymd_date = None

        # Only fill if we have ALL parts. Otherwise, we should keep looking
        if pd.notna(row.year) and pd.notna(row.month) and pd.notna(row.day):
            dwc_ymd_date = f'{int(row.year)}-{int(row.month):02d}-{int(row.day):02d}'

        # Match end_date to start_date if start_date
        start_date = dwc_ymd_date if dwc_ymd_date else None
        end_date = start_date

        # If no explicit date columns, we'll just start with the eventDate
        if not start_date and row.eventDate:
            start_date = parse_iso_date_string(row.eventDate)

        # eventRemarks will sometimes contain event endDates as '; ended <date>' string (A&M)
        # We should check for this before doing the more general check
        if row.eventRemarks and (not start_date or not end_date):
            # Search through eventRemarks for all matches
            for match in EVENT_REMARKS_DATE_REGEX.finditer(row.eventRemarks):
                keyword = match.group('keyword')
                matched_date = None
                if match.group('year'):
                    matched_date = match.group('year')
                    if match.group('month'):
                        matched_date += f"-{match.group('month').zfill(2)}"
                        if match.group('day'):
                            matched_date += f"-{match.group('day').zfill(2)}"
                # Fill start_date matches (if not already filled)
                if not start_date and (keyword == 'dated' or keyword == 'started'):
                    start_date = matched_date
                # Fill end date matches (if not already filled)
                elif not end_date and keyword == 'ended':
                    end_date = matched_date
                # If we have both of our matches, stop looking
                if start_date and end_date:
                    break

        # Now check each column for general date strings
        # A&M's eventDates can end up in verbatimEventDate here in M(M)/dd/yyyy hh:mm:ss format
        # Although we can't immediately trust non-iso formats, we can attempt to parse unambiguous dates from them
        if not start_date or not end_date:
            for date_column in ['eventDate', 'verbatimEventDate', 'eventRemarks']:
                col_value = getattr(row, date_column, None)
                if not col_value:
                    continue
                # Do a quick check for 'xxxxxx to xxxxxx' range strings
                start_date, end_date = parse_date_to_date_range_string(
                    col_value)
                if start_date is None:
                    start_date, end_date = parse_yyyy_yyyy_range_string(
                        col_value)
                if start_date is None:
                    start_date = extract_date(col_value)
                if start_date:
                    break

        if start_date and not end_date:
            end_date = start_date

        df.at[idx, 'collectionStartDate'] = start_date
        df.at[idx, 'collectionEndDate'] = end_date

        # original = None
        # if pd.notna(row.year) and pd.notna(row.month) and pd.notna(row.day):
        #     original = f'{int(row.year)}-{int(row.month):02d}-{int(row.day):02d}'
        # elif pd.notna(row.year) and pd.notna(row.month):
        #     original = f'{int(row.year)}-{int(row.month):02d}'
        # elif pd.notna(row.year):
        #     original = f'{int(row.year)}'

        # if original != start_date or ((not start_date) and any([row.verbatimEventDate, row.eventDate, row.eventRemarks, pd.notna(row.year)])):
        #     date_audit.append({
        #         'index': idx,
        #         'newDate': start_date,
        #         'originalDate': original,
        #         'eventDate': row.eventDate,
        #         'verbatimEventDate': row.verbatimEventDate,
        #         'year': row.year,
        #         'month': row.month,
        #         'day': row.day,
        #         'eventRemarks': row.eventRemarks,
        #         'collectionStartDate': start_date,
        #         'collectionEndDate': end_date,
        #         'status': 'failed' if not start_date else 'altered'
        #     })

    # Convert empty strings to None for SQL/NULL compatibility
    df['collectionStartDate'] = df['collectionStartDate'].replace('', None)
    df['collectionEndDate'] = df['collectionEndDate'].replace('', None)

    # if date_audit:
    #     i = 0
    #     path = os.path.join(DATA_OUT_PATH)
    #     while os.path.exists(os.path.join(path, f'date_audit_{i}.csv')):
    #         i += 1
    #     pd.DataFrame(date_audit).to_csv(os.path.join(
    #         path, f'date_audit_{i}.csv'), index=False)

    return df


def extract_date(string: str):
    """Attempts to extract unambiguous date from given string"""

    ymd_match = ISO_YMD_REGEX.search(string)
    mdy_match = AMBIGUOUS_MDY_PATTERN_REGEX.search(string)
    dmy_match = AMBIGUOUS_DMY_PATTERN_REGEX.search(
        string) or COMPACT_DMY_PATTERN_REGEX.search(string)

    best_match = None

    # Build candidates: (count of parts, date_string)
    candidates = []

    # Get ymd match
    if ymd_match:
        ymd_result = parse_iso_date_string(string)
        if ymd_result:
            score = ymd_result.count('-')  # 0=year, 1=YM, 2=YMD
            candidates.append((score, ymd_result))

    # Get ambiguous matches
    for ambiguous_match in [mdy_match, dmy_match]:
        if ambiguous_match:
            parts = _parse_ambiguous_match(ambiguous_match)
            if parts:
                ambiguous_date = str(parts['year'])
                score = 0
                if parts['month']:
                    ambiguous_date += f"-{parts['month']:02d}"
                    score += 1
                    if parts['day']:
                        ambiguous_date += f"-{parts['day']:02d}"
                        score += 1
                candidates.append((score, ambiguous_date))

    # If any matches, use compiled date string from match with the most parts (most complete)
    if candidates:
        best_match = max(candidates, key=lambda x: x[0])[1]

    return best_match


def filter_texas_bounding_box(df: DataFrame) -> DataFrame:
    """
    Given a pandas df with decimalLongitude and decimalLatitude columns,
    remove rows that fall outside of a basic Texas bounding box.
    """

    min_lon, max_lon = -106.65, -93.5
    min_lat, max_lat = 25.8, 36.5

    original_count = len(df)

    # Filter to Texas bounding box
    df = df[
        (df['decimalLongitude'].between(min_lon, max_lon)) &
        (df['decimalLatitude'].between(min_lat, max_lat))
    ]
    bad_location_count = original_count - len(df)

    # Log number of records removed by bounding box
    if bad_location_count:
        data_logger.info(
            f'Removed {bad_location_count} records found outside of Texas')

    return df


def process_dwc_observations(filepath: str, chunk_size: int = 1000000) -> Iterator[DataFrame]:
    """
    Take an unclean dwc observations file and process it, in chunks,
    into a format suitable for tx_inverts database insertion.
    This includes date parsing via parse_dwc_dates.

    Args:
        filepath (str): Path to the dwc observations file.
        chunk_size (int): Chunk size for reading csv

    Returns:
        Iterator[Dataframe]: Processed DataFrame chunk ready for database insertion.
    """

    for chunk in pd.read_csv(
        filepath,
        delimiter='\t',
        quoting=csv.QUOTE_NONE,
        on_bad_lines='warn',
        low_memory=False,
        chunksize=chunk_size
    ):
        total_count = len(chunk)

        # STEP 1: FILTER GEOMETRIES
        # Drop missing coordinates
        chunk = chunk.dropna(subset=['decimalLongitude', 'decimalLatitude'])

        # Filter to Texas bounding box (details filtering is performed later, in SQL)
        chunk = filter_texas_bounding_box(chunk)
        texas_count = len(chunk)

        # STEP 2: FILTER/PARSE DATES
        chunk = parse_dwc_dates(chunk)

        bad_date_count = texas_count - len(chunk)
        if bad_date_count:
            data_logger.info(
                f"Removed {bad_date_count} records found with invalid collection dates")

        # Overwrite species/subspecies values with epithet column values if they exist
        for target, source in [('species', 'specificEpithet'), ('subspecies', 'infraspecificEpithet')]:
            if source in chunk.columns:
                # If target column exists, overwrite with source; else create it
                chunk[target] = chunk[source]

        # Coerce dataframe to observations table shape
        chunk = GBIF_OBSERVATIONS_TABLE.coerce_dataframe(chunk)

        # Convert valid dates to ISO strings, leave missing as None
        # Note: This will NOT parse dates earlier than 1677-09-21
        for col in ['collection_start_date', 'collection_end_date']:
            chunk[col] = pd.to_datetime(
                chunk[col], errors='coerce', format='mixed').dt.date

        # Drop observations with dates still missing
        chunk = chunk.dropna(
            subset=['collection_start_date', 'collection_end_date'])

        data_logger.info(
            f"Processed chunk with {len(chunk)} valid records of {total_count} total records")

        yield chunk
