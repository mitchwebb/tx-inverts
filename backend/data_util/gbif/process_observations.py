# Logic for processing GBIF observations download

import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from pandas import DataFrame
from geopandas.geodataframe import GeoDataFrame
from backend.constants.map import TEXAS_GEOJSON
import csv
from pathlib import Path
import re
from backend.config.data import DATA_OUT_PATH
import os
from backend.core.logging import data_logger


# Year is required, day cannot exist without month
# No trailing digits allowed
ISO_YMD_PATTERN = (
    r'(?P<year>\d{4})'
    r'(?:-(?P<month>0?[1-9]|1[0-2])'
    r'(?:-(?P<day>0?[1-9]|[12][0-9]|3[01]))?)?'
    r'(?!\d)'
)
ISO_YMD_REGEX = re.compile(ISO_YMD_PATTERN, re.IGNORECASE)

# Mapping month names/abbreviations to numbers
MONTH_LOOKUP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

MONTH_NAMES = "|".join(re.escape(m) for m in MONTH_LOOKUP.keys())

AMBIGUOUS_DMY_PATTERN_REGEX = re.compile(
    rf'(?<!\d)'
    # optional day
    r'(?:(?P<day>0?[1-9]|[12][0-9]|3[01])(?P<daySuffix>st|nd|rd|th)?[-/\s,]+)?'
    # month always required
    rf'(?:(?P<monthNumber>0?[1-9]|1[0-2])|(?P<monthText>{MONTH_NAMES}))'
    r'[\s\-/.,]+'
    r'(?P<year>\d{4})'
    r'(?!\d)',
    re.IGNORECASE
)

AMBIGUOUS_MDY_PATTERN_REGEX = re.compile(
    rf'(?<!\d)'
    # Either number or text
    rf'(?:(?P<monthNumber>0?[1-9]|1[0-2])|(?P<monthText>{MONTH_NAMES}))'
    r'[\s\-/.,]+'                               # Separator
    # optional day
    r'(?:(?P<day>0?[1-9]|[12][0-9]|3[01])(?P<daySuffix>st|nd|rd|th)?[-/\s,]+)?'
    r'(?P<year>\d{4})'                          # Year
    r'(?!\d)',                                  # No trailing digits
    re.IGNORECASE
)


EVENT_REMARKS_DATE_PATTERN = (
    r'(?P<keyword>dated|started|ended)[:= ]+' + ISO_YMD_PATTERN
)
EVENT_REMARKS_DATE_REGEX = re.compile(EVENT_REMARKS_DATE_PATTERN, re.IGNORECASE)


def _parse_ambiguous_match(match: re.Match[str]) -> dict[str, int | None] | None:
    '''
        Args:
            match
        Return: Unambiguous date dict or None
    '''

    # If no year is provided, date is useless
    if not match.group('year'):
        return None

    day = match.group('day')
    day_suffix = match.group('daySuffix')
    month_number = match.group('monthNumber')
    month_text = match.group('monthText')

    parts = {
        'year': int(match.group('year')),
        'month': None,
        'day': None
    }

    if month_text:
        # Textual month is always unambiguous
        parts['month'] = MONTH_LOOKUP[month_text.lower().strip()]
        if day:
            parts['day'] = int(day)
    elif month_number:
        # Numeric month is unambiguous if day is missing or day is unambiguous
        if not day or day_suffix or (day and int(day) > 12):
            parts['month'] = int(month_number)
        # Day is unambiguous if day_suffix or day > 12
        if day and (day_suffix or int(day) > 12):
            parts['day'] = int(day)

    # If we have an unambiguous month (and year), our date is unambiguous
    return parts if parts['month'] else None


def parse_date_range_string(range_string: str):
    '''
    Expecting a string in yyyy-MM-dd/yyyy-MM-dd type format, 
    parse into start_date and end_date

    Return [None, None] if invalid
    '''

    start_date = None
    end_date = None

    parts = range_string.split('/')
    if len(parts) != 2:
        return [start_date, end_date]

    start_match = ISO_YMD_REGEX.search(parts[0])
    end_match = ISO_YMD_REGEX.search(parts[1])

    # If matched on start_date and end_date years, add years to output string
    if start_match and end_match and start_match.group('year') and end_match.group('year'):
        start_date = start_match.group('year')
        end_date = end_match.group('year')

        if start_match.group('month') and end_match.group('month'):
            start_date += f"-{start_match.group('month').zfill(2)}"
            end_date += f"-{end_match.group('month').zfill(2)}"

            if start_match.group('day') and end_match.group('day'):
                start_date += f"-{start_match.group('day').zfill(2)}"
                end_date += f"-{end_match.group('day').zfill(2)}"

    return [start_date, end_date]


# Some basic date parsing for eventDates
def parse_gbif_dates(df: DataFrame) -> DataFrame | GeoDataFrame:
    '''
    Take a pandas dataframe/geodataframe and, assuming it's a gbif table,
    parse out a startDate and endDate, if applicable

    If event_date has '/', then it can be assumed to be a range.
    HOWEVER, not all eventDates are formatted this way.
    UTIC, for example: 
        eventDate: '2001-06-25'
        eventRemarks: '; ended 2001-06-27'
    '''

    df = df.copy()  # don't mutate input

    # Ensure columns are strings, missing as empty string
    for col in ['eventRemarks', 'eventDate', 'verbatimEventDate']:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    for col in ['year', 'month', 'day']:
        df[col] = pd.to_numeric(df[col], errors="coerce")  # convert to numeric

    df['collection_start_date'] = ''
    df['collection_end_date'] = ''

    for row in df.itertuples(index=True):
        idx = row.Index
        start_date = ''
        end_date = ''

        # First we will check for yyyy-MM-dd/yyyy-MM-dd format in eventDate
        # This is common across several institutions, and seems trustworthy
        if row.eventDate:
            [start_date, end_date] = parse_date_range_string(row.eventDate)
            if start_date and end_date:
                df.at[idx, 'collection_start_date'] = start_date
                df.at[idx, 'collection_end_date'] = end_date
                continue

        # If no match, we'll initially assign start date to GBIF YMD columns
        # This is the most trustworthy source for single dates
        gbif_ymd_date = None

        if pd.notna(row.year) and pd.notna(row.month) and pd.notna(row.day):
            gbif_ymd_date = f'{int(row.year)}-{int(row.month):02d}-{int(row.day):02d}'

        start_date = gbif_ymd_date if gbif_ymd_date else None
        end_date = start_date

        # eventRemarks will often store event endDates as '; ended <date>' string
        if row.eventRemarks:
            match = EVENT_REMARKS_DATE_REGEX.search(row.eventRemarks)
            if match and match.group('keyword'):
                keyword = match.group('keyword')
                matched_date = None
                if match.group('year'):
                    matched_date = match.group('year')
                    if match.group('month'):
                        matched_date += f"-{match.group('month').zfill(2)}"
                        if match.group('day'):
                            matched_date += f"-{match.group('day').zfill(2)}"
                if keyword == 'dated' or keyword == 'started':
                    # print(f'Searched for start_date in eventRemarks, found {matched_date}')
                    start_date = matched_date
                elif keyword == 'ended':
                    # print(f'Searched for end_date in eventRemarks, found {matched_date}')
                    end_date = matched_date

        # Next we'll check for date strings in verbatimEventDate
        # A&M's eventDates end up here in M(M)/dd/yyyy hh:mm:ss format
        # Although we can't trust that format for sure, we can attempt to parse unambiguous dates
        if row.verbatimEventDate and not start_date:
            mdy_match = AMBIGUOUS_MDY_PATTERN_REGEX.search(
                row.verbatimEventDate)
            dmy_match = AMBIGUOUS_DMY_PATTERN_REGEX.search(
                row.verbatimEventDate)

            verbatim_parts = None
            if mdy_match:
                verbatim_parts = _parse_ambiguous_match(mdy_match)
            elif dmy_match:
                verbatim_parts = _parse_ambiguous_match(dmy_match)

            # If we parsed a date from verbatim date (and didn't succeed in a previous step), use this
            if verbatim_parts:
                verbatim_date = str(verbatim_parts['year'])
                if verbatim_parts['month']:
                    verbatim_date += f"-{verbatim_parts['month']:02d}"
                    if verbatim_parts['day']:
                        verbatim_date += f"-{verbatim_parts['day']:02d}"
                start_date = verbatim_date

        if start_date and not end_date:
            end_date = start_date

        df.at[idx, 'collection_start_date'] = start_date
        df.at[idx, 'collection_end_date'] = end_date

    # Convert empty strings to None for SQL/NULL compatibility
    df['collection_start_date'] = df['collection_start_date'].replace('', None)
    df['collection_end_date'] = df['collection_end_date'].replace('', None)

    return df


def process_dwc_observations(filepath: Path, chunk_size: int = 1000000, save_cleaned: bool = False) -> GeoDataFrame:
    '''
    Take an unclean dwc observations file and process it into a format
    suitable for database insertion.

    Args:
        filepath (str): Path to the dwc observations file.
        chunk_size (int): Chunk size for reading csv
        save_cleaned (bool): Option to save prepped 

    Returns:
        pd.DataFrame: Processed DataFrame ready for database insertion.
    '''

    # filtered_chunks = []

    observation_count = 0

    # Use approximate bounding box for Texas to perform preliminary boundary filter
    min_lon, max_lon = -106.65, -93.5
    min_lat, max_lat = 25.8, 36.5

    for chunk in pd.read_csv(
        filepath,
        delimiter='\t',
        quoting=csv.QUOTE_NONE,
        on_bad_lines='warn',
        low_memory=False,
        chunksize=chunk_size
    ):

        # STEP 1: FILTER GEOMETRIES
        # Drop missing coordinates
        chunk = chunk.dropna(subset=['decimalLongitude', 'decimalLatitude'])

        # Filter to Texas bounding box (fine filtering is performed later in SQL)
        df = chunk[
            (chunk['decimalLongitude'].between(min_lon, max_lon)) &
            (chunk['decimalLatitude'].between(min_lat, max_lat))
        ]
        bad_location_count = len(chunk) - len(df)
        if bad_location_count:
            print(
                f'Removed {bad_location_count} records found outside of Texas')

        # STEP 2: FILTER/PARSE DATES
        df = parse_gbif_dates(df)

        # Filter out observations with missing dates
        df = df.dropna(subset=['collection_start_date', 'collection_end_date'])
        bad_date_count = (len(chunk) - bad_location_count) - len(df)
        if bad_date_count:
            print(
                f'Removed {bad_date_count} records found with invalid collection dates')

        # # Add newly filtered chunk to filtered_chunks
        # filtered_chunks.append(df)

        observation_count += len(chunk)

        print(
            f'Processed chunk with {len(df)} valid records of {len(chunk)} total records')

    # if not filtered_chunks:
    #     raise ValueError(
    #         "No valid data to process — all chunks were filtered out")

    # # Combine all filtered chunks
    # combined_df = pd.concat(filtered_chunks, ignore_index=True)
    # # Saved combined df, if needed
    # if save_cleaned:
    #     # Create cleaned directory if it doesn't exist
    #     cleaned_dir = os.path.join(DATA_OUT_PATH, 'cleaned')
    #     os.makedirs(cleaned_dir, exist_ok=True)
    #     combined_df.to_csv(os.path.join(
    #         cleaned_dir, 'observations_cleaned.csv'), sep="\t", index=False)

    # print(
    #     f'Processed {len(combined_df)} valid observations out of {observation_count} total observations')

        yield chunk
