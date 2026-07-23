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
