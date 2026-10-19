import hashlib
import logging

import pytest

from aimsight.ingest.checksum import (
    ChecksumMismatchError,
    compute_md5,
    verify_checksum,
)


# --- compute_md5 -----------------------------------------------------------

def test_compute_md5_matches_hashlib_for_known_content(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("Date,Device\n01/15/2023,Example\n")

    expected = hashlib.md5(f.read_bytes()).hexdigest()
    assert compute_md5(f) == expected


def test_compute_md5_handles_multiple_chunks(tmp_path):
    # chunk_size=4 forces several read iterations over a small file,
    # proving the chunked loop reconstructs the same digest as reading
    # the whole file at once.
    f = tmp_path / "sample.csv"
    f.write_text("a" * 100)

    expected = hashlib.md5(f.read_bytes()).hexdigest()
    assert compute_md5(f, chunk_size=4) == expected


def test_compute_md5_raises_file_not_found_for_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError, match="does_not_exist.csv"):
        compute_md5(missing)


# --- verify_checksum --------------------------------------------------------

def test_verify_checksum_passes_silently_when_checksum_matches(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("good data\n")
    correct_md5 = hashlib.md5(f.read_bytes()).hexdigest()

    verify_checksum(f, correct_md5)  # no exception = success


def test_verify_checksum_is_case_insensitive(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("good data\n")
    correct_md5 = hashlib.md5(f.read_bytes()).hexdigest()

    verify_checksum(f, correct_md5.upper())  # no exception = success


def test_verify_checksum_raises_on_mismatch(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text("good data\n")
    wrong_md5 = "0" * 32

    with pytest.raises(ChecksumMismatchError, match="Checksum mismatch"):
        verify_checksum(f, wrong_md5)


def test_verify_checksum_logs_error_on_mismatch(tmp_path, caplog):
    f = tmp_path / "sample.csv"
    f.write_text("good data\n")
    wrong_md5 = "0" * 32

    with caplog.at_level(logging.ERROR, logger="aimsight.ingest.checksum"):
        with pytest.raises(ChecksumMismatchError):
            verify_checksum(f, wrong_md5)

    assert "checksum mismatch" in caplog.text


def test_verify_checksum_raises_file_not_found_for_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError, match="does_not_exist.csv"):
        verify_checksum(missing, "irrelevant")
