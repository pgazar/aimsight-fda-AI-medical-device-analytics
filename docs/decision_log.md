# Decision Log

## 2026-07-22 — Use pyenv Python 3.11.11 instead of system Python 3.14.3

**Decision:** The project virtual environment (`.venv`) is built with `pyenv`'s
Python 3.11.11, not the machine's default system Python (3.14.3).

**Reason:** This project depends on `psycopg2-binary`, `dbt-core`, and other
libraries that typically lag several months behind supporting a brand-new
CPython release. 3.11 is a mature, widely-supported version with no known
compatibility gaps for this stack.

**Alternatives considered:** System Python 3.14.3 (rejected — too new, risk of
missing wheels for key dependencies); pyenv 3.11.9 (rejected — 3.11.11 is the
newer patch release with no known downside).

**Consequences:** Anyone setting up this project locally must have `pyenv`
(or another way to get Python 3.11.x) available; plain `python3 -m venv` using
the system interpreter will not match this environment.

## 2026-07-23 — Defer row-shape validation past column-name checks

**Decision:** `load_raw_ai_devices()` and `standardize_columns()` catch a
missing file, an empty file, unparseable CSV (e.g. an unmatched quote), and
missing expected column names — but do NOT catch a row with more fields
than the header.

**Reason:** Testing this surfaced a real pandas behavior: when a data row
has more fields than the header, pandas' C parser does not raise an error —
it silently treats the leftmost extra fields as a (Multi)Index and shifts
the remaining values into the named columns. Column names stay correct;
the data underneath them is wrong. This can't be caught by a column-name
check, since the columns are still all present and correctly named.

**Alternatives considered:** Adding a row-shape check (e.g. asserting
`df.index` is a plain `RangeIndex`) directly inside `load_raw_ai_devices()`
now — rejected for this step, since it belongs with the broader validation
work (Week 1 items 9–10: validate expected columns, report invalid values)
rather than bolted onto the loader in isolation.

**Consequences:** Until that validation step exists, a row with extra
trailing fields would load "successfully" with silently misaligned data.
Documented here so it isn't forgotten before that step is built.
