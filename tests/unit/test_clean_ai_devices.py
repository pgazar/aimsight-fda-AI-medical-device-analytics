from pathlib import Path

import pandas as pd
import pytest

from aimsight.transform.clean_ai_devices import (
    MissingExpectedColumnsError,
    load_raw_ai_devices,
    standardize_columns,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


# --- load_raw_ai_devices ------------------------------------------------

def test_load_raw_ai_devices_loads_the_tiny_fixture_not_the_real_file():
    df = load_raw_ai_devices(raw_data_dir=FIXTURES_DIR)
    assert df.shape == (2, 6)
    assert "Primary Product Code" in df.columns


def test_load_raw_ai_devices_raises_file_not_found_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="aiml-devices-csv.csv"):
        load_raw_ai_devices(raw_data_dir=tmp_path)


def test_load_raw_ai_devices_raises_value_error_for_empty_file(tmp_path):
    empty_csv = tmp_path / "aiml-devices-csv.csv"
    empty_csv.write_text("")

    with pytest.raises(ValueError, match="empty"):
        load_raw_ai_devices(raw_data_dir=tmp_path)


def test_load_raw_ai_devices_raises_value_error_for_malformed_csv(tmp_path):
    # An unmatched quote (e.g. a stray " inside a device name) is a
    # realistic way for this to actually happen, and genuinely triggers
    # pandas' ParserError — unlike a row with extra trailing fields, which
    # pandas silently reinterprets as an index instead of raising (see
    # docs/decision_log.md for why that gap is handled in a later step,
    # not here).
    bad_csv = tmp_path / "aiml-devices-csv.csv"
    bad_csv.write_text(
        "Date of Final Decision,Submission Number,Device,Company,"
        "Panel (Lead),Primary Product Code\n"
        '01/15/2023,K230001,"Example Device,Acme,Radiology,ABC\n'
    )

    with pytest.raises(ValueError, match="not valid CSV"):
        load_raw_ai_devices(raw_data_dir=tmp_path)


# --- standardize_columns -------------------------------------------------

def _tiny_raw_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date of Final Decision": ["01/15/2023"],
            "Submission Number": ["K230001"],
            "Device": ["Example Detection System"],
            "Company": ["Acme Health Inc"],
            "Panel (Lead)": ["Radiology"],
            "Primary Product Code": ["ABC"],
        }
    )


def test_standardize_columns_renames_all_expected_columns():
    raw_df = _tiny_raw_dataframe()
    clean_df = standardize_columns(raw_df)

    assert list(clean_df.columns) == [
        "date_of_final_decision",
        "submission_number",
        "device",
        "company",
        "panel_lead",
        "primary_product_code",
    ]
    # values themselves must be untouched, only column names change
    assert clean_df["primary_product_code"].iloc[0] == "ABC"


def test_standardize_columns_does_not_mutate_the_input_dataframe():
    raw_df = _tiny_raw_dataframe()
    original_columns = list(raw_df.columns)

    standardize_columns(raw_df)

    assert list(raw_df.columns) == original_columns


def test_standardize_columns_raises_when_a_column_is_missing():
    raw_df = _tiny_raw_dataframe().drop(columns=["Company"])

    with pytest.raises(MissingExpectedColumnsError, match="Company"):
        standardize_columns(raw_df)


# --- parse_decision_date -------------------------------------------------

from aimsight.transform.clean_ai_devices import parse_decision_date  # noqa: E402
import logging  # noqa: E402


def test_parse_decision_date_converts_valid_strings_to_datetime():
    df = pd.DataFrame({"date_of_final_decision": ["01/15/2023", "12/31/2024"]})
    result = parse_decision_date(df)

    assert pd.api.types.is_datetime64_any_dtype(result["date_of_final_decision"])
    assert result["date_of_final_decision"].iloc[0] == pd.Timestamp("2023-01-15")
    assert result["date_of_final_decision"].iloc[1] == pd.Timestamp("2024-12-31")


def test_parse_decision_date_does_not_mutate_the_input_dataframe():
    df = pd.DataFrame({"date_of_final_decision": ["01/15/2023"]})
    original_dtype = df["date_of_final_decision"].dtype

    parse_decision_date(df)

    assert df["date_of_final_decision"].dtype == original_dtype
    assert df["date_of_final_decision"].iloc[0] == "01/15/2023"


def test_parse_decision_date_sets_missing_dates_to_nat_and_warns(caplog):
    df = pd.DataFrame({"date_of_final_decision": ["01/15/2023", None, ""]})

    with caplog.at_level(logging.WARNING, logger="aimsight.transform.clean_ai_devices"):
        result = parse_decision_date(df)

    assert result["date_of_final_decision"].isna().sum() == 2
    assert "missing date_of_final_decision" in caplog.text


def test_parse_decision_date_sets_malformed_dates_to_nat_and_warns(caplog):
    df = pd.DataFrame({"date_of_final_decision": ["01/15/2023", "not-a-date"]})

    with caplog.at_level(logging.WARNING, logger="aimsight.transform.clean_ai_devices"):
        result = parse_decision_date(df)

    assert result["date_of_final_decision"].isna().sum() == 1
    assert "does not match MM/DD/YYYY" in caplog.text


def test_parse_decision_date_raises_if_column_missing():
    df = pd.DataFrame({"some_other_column": ["x"]})

    with pytest.raises(MissingExpectedColumnsError, match="date_of_final_decision"):
        parse_decision_date(df)
