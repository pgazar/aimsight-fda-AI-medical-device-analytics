"""Checksum verification for raw data files.

Computes and checks MD5 checksums so a corrupted or incomplete download
can be caught explicitly at ingest time, rather than silently feeding
bad bytes into the rest of the pipeline. Backs the Step 1 integrity-check
claim with real, tested code (see docs/decision_log.md, Step 13).
"""

from pathlib import Path

import hashlib

from aimsight.logging_config import get_logger

logger = get_logger(__name__)


class ChecksumMismatchError(Exception):
    """Raised when a file's computed checksum does not match what was expected."""


def compute_md5(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute the MD5 checksum of a file, reading it in fixed-size chunks.

    Reading in chunks (rather than one `file.read()` call) keeps memory
    use constant no matter the file size — this matters once Step 16
    pulls full openFDA bulk files, which can be far larger than the
    current sample CSVs.

    Raises:
        FileNotFoundError: if `file_path` does not exist.
    """
    if not file_path.exists():
        logger.error("cannot compute checksum — file not found: %s", file_path)
        raise FileNotFoundError(
            f"Cannot compute checksum — file not found: {file_path}"
        )

    md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)

    digest = md5.hexdigest()
    logger.info("computed md5 for %s: %s", file_path, digest)
    return digest


def verify_checksum(file_path: Path, expected_md5: str) -> None:
    """Verify that `file_path`'s MD5 checksum matches `expected_md5`.

    Comparison is case-insensitive, since MD5 hex digests are conventionally
    written in either case depending on the tool that produced them.

    Raises:
        FileNotFoundError: if `file_path` does not exist.
        ChecksumMismatchError: if the computed checksum does not match.
    """
    actual_md5 = compute_md5(file_path)

    if actual_md5.lower() != expected_md5.lower():
        logger.error(
            "checksum mismatch for %s: expected %s, got %s",
            file_path, expected_md5, actual_md5,
        )
        raise ChecksumMismatchError(
            f"Checksum mismatch for {file_path}: "
            f"expected {expected_md5}, got {actual_md5}."
        )

    logger.info("checksum verified for %s", file_path)
