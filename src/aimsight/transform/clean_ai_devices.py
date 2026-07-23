"""Cleaning logic for the FDA AI-enabled medical device list.

This is the first transformation applied to the raw source file. It never
touches the file on disk (data/raw/aiml-devices-csv.csv stays byte-for-byte
what FDA published) — it only renames columns on an in-memory copy.
"""

from pathlib import Path

import pandas as pd

from aimsight.config import RAW_DATA_DIR
from aimsight.logging_config import get_logger

logger = get_logger(__name__)

RAW_AI_DEVICES_FILENAME = "aiml-devices-csv.csv"

# Original FDA column name -> standardized snake_case name.
COLUMN_RENAME_MAP = {
    "Date of Final Decision": "date_of_final_decision",
    "Submission Number": "submission_number",
    "Device": "device",
    "Company": "company",
    "Panel (Lead)": "panel_lead",
    "Primary Product Code": "primary_product_code",
}


class MissingExpectedColumnsError(Exception):
    """Raised when the raw AI-device file is missing a column we rely on."""


def load_raw_ai_devices(raw_data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load the raw FDA AI-enabled device CSV, unchanged.

    raw_data_dir defaults to the real project data/raw directory, but can
    be overridden — tests pass a tiny fixture directory instead, so we
    never depend on the full 1,524-row file just to test this function.

    Raises:
        FileNotFoundError: if the CSV isn't at the expected path.
        ValueError: if the file exists but is empty or not valid CSV.
    """
    csv_path = raw_data_dir / RAW_AI_DEVICES_FILENAME
    logger.info("loading raw AI device file from %s", csv_path)

    if not csv_path.exists():
        logger.error("raw AI device file not found at %s", csv_path)
        raise FileNotFoundError(
            f"Expected raw FDA AI-device CSV at {csv_path}, but it does not "
            "exist. Has data/raw/aiml-devices-csv.csv been added to the "
            "project yet?"
        )

    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        logger.error("raw AI device file at %s is empty", csv_path)
        raise ValueError(f"Raw file at {csv_path} exists but is empty.") from exc
    except pd.errors.ParserError as exc:
        logger.error("raw AI device file at %s could not be parsed: %s", csv_path, exc)
        raise ValueError(f"Raw file at {csv_path} is not valid CSV: {exc}") from exc

    logger.info("loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw FDA columns to stable snake_case names.

    Returns a new DataFrame; the one passed in is never modified.

    Raises:
        MissingExpectedColumnsError: if any column this project depends on
            is missing — e.g. because FDA changed the export format.
    """
    expected_columns = set(COLUMN_RENAME_MAP.keys())
    actual_columns = set(df.columns)
    missing = expected_columns - actual_columns

    if missing:
        logger.error("raw file is missing expected columns: %s", sorted(missing))
        raise MissingExpectedColumnsError(
            f"Expected columns {sorted(missing)} not found in the raw file. "
            f"Actual columns were: {sorted(actual_columns)}."
        )

    logger.info("standardizing %d column names", len(COLUMN_RENAME_MAP))
    return df.rename(columns=COLUMN_RENAME_MAP)


def parse_decision_date(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date_of_final_decision from 'MM/DD/YYYY' strings into real dates.

    Returns a new DataFrame; the one passed in is never modified.

    A missing or unparseable date becomes NaT (pandas' "Not a Time" null)
    rather than crashing the pipeline — but every occurrence is logged as
    a WARNING, distinguishing "was already missing" from "failed to parse",
    so nothing is silently lost. We use an explicit format string rather
    than letting pandas guess, because an ambiguous date like "01/02/2023"
    could mean Jan 2 or Feb 1 depending on locale assumptions — being
    explicit removes that ambiguity entirely.

    Raises:
        MissingExpectedColumnsError: if standardize_columns() hasn't been
            run yet (date_of_final_decision doesn't exist).
    """
    if "date_of_final_decision" not in df.columns:
        logger.error("date_of_final_decision column not found")
        raise MissingExpectedColumnsError(
            "date_of_final_decision column not found — call "
            "standardize_columns() before parse_decision_date()."
        )

    result = df.copy()
    raw_dates = result["date_of_final_decision"]

    originally_missing = raw_dates.isna() | (raw_dates.astype(str).str.strip() == "")
    parsed = pd.to_datetime(raw_dates, format="%m/%d/%Y", errors="coerce")
    newly_invalid = parsed.isna() & ~originally_missing

    if originally_missing.any():
        logger.warning(
            "%d rows have a missing date_of_final_decision value",
            int(originally_missing.sum()),
        )

    if newly_invalid.any():
        bad_examples = raw_dates[newly_invalid].head(5).tolist()
        logger.warning(
            "%d rows have a date_of_final_decision value that does not "
            "match MM/DD/YYYY (examples: %s)",
            int(newly_invalid.sum()),
            bad_examples,
        )

    result["date_of_final_decision"] = parsed
    logger.info(
        "parsed date_of_final_decision for %d rows (%d could not be parsed)",
        len(result),
        int(parsed.isna().sum()),
    )
    return result
