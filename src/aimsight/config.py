"""Project-root-anchored paths.

Every path in this project is derived from PROJECT_ROOT, which is computed
from this file's own location rather than the current working directory.
This means scripts, tests, and pipeline jobs all resolve the same paths
whether they're run from the repo root, from src/, from an IDE, from
pytest, or from inside a container.
"""

from pathlib import Path

# config.py lives at <root>/src/aimsight/config.py
# parents[0] = aimsight, parents[1] = src, parents[2] = <root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ENV_PATH = PROJECT_ROOT / ".env"
