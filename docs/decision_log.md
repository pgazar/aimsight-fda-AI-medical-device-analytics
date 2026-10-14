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

## 2026-10-14 — Project spec revised against the READY framework and finalized

**Decision:** `docs/PROJECT_SPEC.md` is replaced by a revised version (changes C1–C23 listed in its §0). `docs/kpi_dependency_table.md` is replaced by a re-audited version.

**Reason:** A review against Christine Jiang's READY portfolio framework found the plan strong on Representative data and Data best practices but missing Exec-driven questions and Insights/impact. A Mac (Apple silicon) compatibility review and a read-only repo audit found further gaps. The individual decisions are logged below.

**Alternatives considered:** Keeping the revision as a separate `UPDATED_PROJECT_SPEC.md` — rejected, because two specs would break the single-source-of-truth rule. The previous version stays in git history.

**Consequences:** Step numbers changed. The spec's §7 "Old #" column maps new steps to the original numbering used in earlier entries of this log.

## 2026-10-14 — Primary stakeholder: VP of Regulatory Strategy (C1)

**Decision:** The project is framed for a VP of Regulatory Strategy at a mid-size medtech company deciding where and how to bring its next AI-enabled device to market. Four executive questions (Q1–Q4, spec §1.1) drive all analysis; every dashboard sheet and SQL analysis names the question it serves.

**Reason:** READY's "E" requires specific, decision-relevant stakeholder questions; the existing 10 KPIs were metrics without an owner or a decision.

**Alternatives considered:** Hospital procurement lead (kept as secondary audience); investor (rejected — would shift focus away from regulatory pathways).

**Consequences:** KPIs that serve no question get cut or moved to an appendix sheet.

## 2026-10-14 — Analysis-first roadmap (C7)

**Decision:** Build a thin end-to-end slice for Q1a (authorization growth by panel and pathway) — load, dbt model, SQL, export, Tableau sheet, written insight — before MDM, Airflow, and the remaining facts.

**Reason:** Near-term target is data analyst roles; the portfolio helps most when a question-to-insight loop is showable early. Answering a real question also surfaces data problems while they are cheap to fix.

**Alternatives considered:** Original infrastructure-first order (rejected — first showable insight would come only near the end).

**Consequences:** The pipeline runs manually (scripts) until Step 25; those scripts later become Airflow tasks, so little is thrown away.

## 2026-10-14 — Airflow hosted on Azure, developed locally (C10 proposal rejected)

**Decision:** Airflow is hosted on a self-managed Azure Linux VM running the same `docker compose` setup used for local development on the Mac.

**Reason:** Keeps the original requirement of a real Azure-hosted orchestration story. A proposal to run Airflow only locally was considered and declined.

**Alternatives considered:** ADF-managed Airflow (not possible — deprecated and closed to new customers); local-only Airflow (rejected by choice); Azure Data Factory pipelines (rejected — less portable skill).

**Consequences:** Free-tier VM sizes are too small for Airflow, so a paid size is needed; size and price are chosen at Step 25. Mitigations: auto-shutdown or start-only-for-runs, Azure budget alert, Airflow UI via SSH tunnel only, SSH restricted to one IP, private key stored with restricted permissions.

## 2026-10-14 — Snowflake: let trials lapse and rebuild from code (C11)

**Decision:** The Snowflake account is treated as disposable. Each 30-day trial is allowed to lapse and a new one is rebuilt from `snowflake/setup.sql` using `scripts/rebuild_snowflake.sh` and `docs/runbook_snowflake_rebuild.md`.

**Reason:** Snowflake has no permanent free tier; all raw data already lives outside Snowflake (local + Azure Blob), so nothing is lost when a trial ends.

**Alternatives considered:** Converting to a paid account (rejected — ongoing cost); switching to a free warehouse such as DuckDB (rejected — lower market signal).

**Consequences:** A rebuild roughly every 30 days, with a calendar reminder. Each rebuild changes the account identifier in `~/.dbt/profiles.yml`. The first rebuild must be ready before the current trial ends (~2026-10-30). Sign up with the plain email form, not SSO (see 2026-09-30 entry).

## 2026-10-14 — Snowflake service user switches to key-pair authentication (C19)

**Decision:** `aimsight_dev` is recreated as `TYPE = SERVICE` with an RSA public key; dbt connects with `private_key_path`. The private key is stored outside the repo.

**Reason:** Snowflake is phasing out single-factor password sign-in, enforcing it for newly created users first. Rebuilt trials create new users, so password-only authentication would likely fail. It also removes the class of password problems logged on 2026-09-30.

**Alternatives considered:** Keeping password authentication (rejected — likely blocked on new users).

**Consequences:** `profiles.yml` changes; the key pair must be backed up securely and never committed.

## 2026-10-14 — Dashboard tool: Tableau instead of Power BI (C18, C20)

**Decision:** Dashboards are built in Tableau Desktop Public Edition and published to Tableau Public. A tested export script writes Snowflake star tables to CSV for Tableau (and a small flat extract for Excel).

**Reason:** Tableau runs natively on the Mac and publishes publicly for free. Power BI Desktop is Windows-only (would need an unsupported VM), and public publishing needs a work/school account with an admin-enabled setting.

**Alternatives considered:** Power BI via a Windows 11 ARM VM (rejected); Looker, Streamlit (rejected — redundant or lower market signal).

**Consequences:** The free Public Edition cannot connect to Snowflake, so it reads exported files — no scheduled refresh from Snowflake. Benefit: the public dashboard keeps working while a Snowflake trial is down. Power BI skills, if needed for target postings, are built separately.

## 2026-10-14 — Data-modeling depth (C22)

**Decision:** Add `bridge_recall_submission` (many-to-many between recalls and 510(k) submissions via `k_numbers`), a role-playing `dim_date`, separate CSV exports per star table related in Tableau's logical layer, and an ERD in `docs/architecture.md`.

**Reason:** "Data modeling" in job postings covers both warehouse modeling and BI-side relationships; these show both on real data.

**Alternatives considered:** A single flat export file (rejected — hides the star schema).

**Consequences:** Slightly more complex export and Tableau setup. Unmatched `k_numbers` are kept and counted, not dropped.

## 2026-10-14 — Azure DevOps Boards in use from now on (C15); Kafka kept optional (C23)

**Decision:** Boards is set up now (Step 12) with one work item per remaining step. Kafka stays as an optional final extension (Step 31), labeled a simulation.

**Reason:** A board created after the work would be a retroactive artifact. Kafka has no natural fit for daily-at-most FDA data but helps the scale/streaming story for data-engineering roles.

**Alternatives considered:** Dropping Boards; cutting Kafka entirely (both declined).

**Consequences:** Kafka work starts only after the core deliverables exist.

## 2026-10-14 — Repo audit corrections (C16, C21)

**Decision:** Record and fix what a read-only audit found: (1) `aimsight_dbt/` was never committed and still contains dbt's example models; (2) no code, test, or log entry backs the Step 1 MD5 checksum claim; (3) recalls have no `recall_number` field (keys are `res_event_number` / `product_res_number`); (4) the adverse-event extract has no follow-up indicator field; (5) the Snowflake trial was provisioned as Enterprise, not Standard (already noted on 2026-09-30, now reflected in the spec).

**Reason:** The spec's own rule is that a step is done only when tested and committed, and resume claims must be verifiable.

**Alternatives considered:** None — these are corrections.

**Consequences:** Step 13 deletes the example models, commits the dbt project, and either adds a tested checksum module or corrects the Step 1 claim (and the resume bullet). Step 16's extraction must include the follow-up field and both recall keys.
