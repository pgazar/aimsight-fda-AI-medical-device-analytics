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

## 2026-09-30 — Snowflake trial provisioned on Azure (West US 2)

**Decision:** The project's Snowflake trial account is hosted on Microsoft
Azure, region `AZURE_WESTUS2` (West US 2 / Washington), Standard edition.

**Reason:** Matches the project's chosen cloud host (Azure) per
`PROJECT_SPEC.md` §5, and West US 2 is the Azure region Snowflake supports
that is geographically closest to the developer's location (San Jose, CA).

**Alternatives considered:** The first signup attempt used an SSO shortcut
("Continue with Google/Microsoft"), which skipped the cloud/edition/region
configuration screen entirely and silently provisioned the account on AWS
(`AWS_US_EAST_2`) instead. That account was abandoned (trial accounts cost
nothing unless actively used) and a second trial was created using the
plain email signup form, which surfaced the configuration screen as
expected.

**Consequences:** Any future Snowflake trial signup for this project should
use the plain email form, not an SSO button, to guarantee the
cloud/edition/region screen appears. `SELECT CURRENT_REGION();` is the
quickest way to confirm which cloud/region an account actually landed on
after the fact.

**Correction (2026-09-30, later same day):** The Admin > Accounts list later
showed this account's edition as **Enterprise**, not Standard as originally
logged above. The Standard-edition decision reasoning in §5 of
`PROJECT_SPEC.md` (lower cost, simpler feature set) still applies as the
*intended* choice; this note just corrects the factual record of what the
trial actually provisioned. No functional impact on anything built so far.

## 2026-09-30 — dbt ↔ Snowflake connection: four compounding issues, resolved

**Decision:** `dbt debug` now connects successfully (`Connection test: [OK
connection ok]`, `All checks passed!`) using `~/.dbt/profiles.yml` with
account `vycnywb-cu58693`, user `aimsight_dev`, password supplied via the
`SNOWFLAKE_PASSWORD` environment variable.

**Reason / root causes found:** Getting here required diagnosing four
separate, stacked issues, each worth remembering on its own:

1. **Account locator vs. account name.** `CURRENT_ACCOUNT()` returns the
   account *locator* (`RI04802`), not the *account name* (`CU58693`) needed
   for the preferred `orgname-accountname` identifier format. The correct
   function is `CURRENT_ACCOUNT_NAME()` — or, more reliably, read the
   "Account Identifier" value directly from Snowsight's Admin > Accounts
   page rather than deriving it. Using the locator produced a `404 Not
   Found` from dbt, since that hostname never existed.
2. **`MUST_CHANGE_PASSWORD = TRUE` is a human-login feature, not a
   service-account one.** Setting it on `aimsight_dev` in Step 9 forced a
   password change on first interactive login, silently invalidating the
   password dbt's environment variable still held. Service/automation
   accounts should be created with `MUST_CHANGE_PASSWORD = FALSE`.
3. **zsh treats `!` as a history-expansion character even inside double
   quotes**, when typed directly in an interactive shell — a password
   containing `!` broke an `export`/`echo` command outright
   (`zsh: event not found: >`). Secrets with shell-special characters
   should be entered via `read -rs` (a hidden prompt), never embedded
   directly in a command string.
4. **Repeated failed attempts (from both `dbt debug` and manual browser
   logins while debugging) triggered Snowflake's automatic 5-failed-login,
   15-minute user lockout.** Confirmed via `DESCRIBE USER aimsight_dev`
   (`MINS_TO_UNLOCK` positive) and cleared via
   `ALTER USER aimsight_dev SET MINS_TO_UNLOCK = 0;`.

**Alternatives considered:** None — each of the four was a genuine bug to
fix, not a design choice with alternatives.

**Consequences:** For any future Snowflake service-account setup in this
project: (a) always copy the account identifier from Snowsight's Admin >
Accounts page rather than deriving it from `CURRENT_ACCOUNT()`; (b) always
set `MUST_CHANGE_PASSWORD = FALSE` on service/automation users; (c) always
enter secrets via a hidden `read -rs` prompt, never typed inline in a shell
command or pasted from a chat interface (which can also mangle
URL-shaped text into markdown links); (d) if authentication starts
failing unexpectedly after several attempts, check for a lockout via
`DESCRIBE USER` before assuming the credentials themselves are wrong.
