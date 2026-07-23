"""Tests for aimsight.config path resolution.

These are intentionally run from more than one working directory (see the
Exact Command to Run section in the corresponding project-log entry) to
prove PROJECT_ROOT does not depend on cwd.
"""

from aimsight.config import PROJECT_ROOT, RAW_DATA_DIR, ENV_PATH


def test_project_root_contains_expected_marker_files():
    # requirements.txt and .gitignore only exist at the true project root.
    assert (PROJECT_ROOT / "requirements.txt").exists()
    assert (PROJECT_ROOT / ".gitignore").exists()


def test_raw_data_dir_is_under_project_root():
    assert RAW_DATA_DIR == PROJECT_ROOT / "data" / "raw"
    assert RAW_DATA_DIR.exists()


def test_env_path_is_under_project_root():
    assert ENV_PATH == PROJECT_ROOT / ".env"
