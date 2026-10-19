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

## 2026-10-16 — Step 14(b): aimsight_dev migrated to key-pair auth, TYPE = SERVICE

**Decision:** `aimsight_dev` now authenticates with an RSA key pair instead of
a password, and its `TYPE` is set to `SERVICE`. Password login for this
user is now fully disabled.

**Reason:** Required by Snowflake's ongoing password deprecation for
service/automation accounts (C19), and removes the whole class of
password problems logged on 2026-09-30.

**How:** Generated a 2048-bit RSA key pair with `openssl` (private key
encrypted with a passphrase, stored at `~/.snowflake/rsa_key.p8`, outside
the repo). Registered the public key with
`ALTER USER aimsight_dev SET RSA_PUBLIC_KEY='...'`. Confirmed via
`DESCRIBE USER` (`RSA_PUBLIC_KEY_FP` populated). Updated `~/.dbt/profiles.yml`
to use `private_key_path` + `private_key_passphrase` (both read from
environment variables, same pattern as the password before it) in place of
`password`. Verified with `dbt debug` (passed). Only then — confirmed
Snowflake docs recommend this order, since switching `TYPE` first would
remove the password fallback before the key was proven to work — ran
`ALTER USER aimsight_dev SET TYPE = SERVICE;` and re-ran `dbt debug` to
confirm it still passed with password login now closed off.

**Alternatives considered:** Dropping and recreating `aimsight_dev` instead
of altering it in place — unnecessary; Snowflake's `ALTER USER ... SET
TYPE = SERVICE` works directly on an existing user.

**Consequences:** `profiles.yml` no longer contains a password anywhere.
This is only part (b) of Step 14 — see `PROJECT_SPEC.md` §7 for parts (a),
(c), (d), (e), which are still outstanding and are what actually make the
account survive the trial lapsing (~2026-10-30) without a manual redo.

## 2026-10-16 — Step 14(a)+(c) done; (d) deferred by choice

**Decision:** `snowflake/setup.sql` (warehouse, database, schema, role,
and `aimsight_dev` created directly as `TYPE = SERVICE` with its key
attached — no password step at all this time), `scripts/rebuild_snowflake.sh`
(updates `~/.dbt/profiles.yml`'s account line via `sed -i ''`, then re-runs
`dbt debug`), and `docs/runbook_snowflake_rebuild.md` (the human steps that
can't be scripted: signup, cloud/region choice, running `setup.sql`,
finding the account identifier) are all written. Part (d) — actually
running this whole process against a brand-new trial to prove it works —
is deliberately **deferred**, not forgotten.

**Reason:** Testing the rebuild now would mean signing up for a genuinely
redundant second trial while the current one still has runway, purely to
exercise a process that isn't needed yet. Deferring it to the actual
rebuild (~2026-10-30) means it gets tested exactly when it's needed, with
no wasted signup.

**Alternatives considered:** Testing immediately — rejected by Pegah as
unnecessary cost (another email/signup) for no immediate benefit.

**Consequences:** Step 14(d) remains open until the current trial is
actually rebuilt. If the rebuild script or runbook has a bug, it will
surface then, under real time pressure, rather than now — worth
re-reading both files once more before the trial actually lapses, as a
cheap hedge against that risk. Part (e), the Azure budget alert, is the
only fully untouched piece of Step 14 remaining.

## 2026-10-19 — Step 11: Azure Blob Storage landing zone built

**Decision:** Azure resources for this project now exist: resource group
`Aimsight`, storage account `aimsightstorage1692` (West US 2, minimum TLS
1.2), and a private blob container `raw-data`. The Azure CLI is installed
locally (Homebrew) and `az login` is verified against the correct personal
subscription.

**Reason:** This is the landing zone the rest of the pipeline (Airflow,
later) will read from — a second, cloud-reachable copy of the raw FDA
data, since cloud services can't reach into a personal laptop directly.

**How, including one real detour:** The Azure free account was first
signed up using a **school email address**. This silently placed the
account inside the school's own Azure Active Directory tenant ("SPS Shared
Service"), where Pegah only had limited (non-owner) permissions — blocking
resource-group creation entirely. Confirmed via **Switch directory** in
the portal, which showed only the school's tenant, no personal one
alongside it. Fixed the same way as the earlier Snowflake AWS-vs-Azure
mixup: signed out completely and redid the signup with a personal email
(`p.zargareian@gmail.com`), landing in a clean, fully-owned "Default
Directory" tenant instead.

From there: created resource group `Aimsight`, then a storage account
within it (first attempt used an invalid name containing an underscore —
Azure storage account names allow only lowercase letters and digits;
settled on `aimsightstorage1692`), then a private container `raw-data`
inside it. Installed `azure-cli` via Homebrew, ran `az login` (confirmed
only the personal subscription/tenant was offered — no sign of the school
tenant), and used `az group list`, `az storage account list`, and
`az storage container list --auth-mode login` to confirm the CLI identity
sees the exact same resources created in the browser. Tightened
`--min-tls-version` to `TLS1_2` (it defaulted to the older `TLS1_0`).

**Alternatives considered:** Trying to detach the Azure account from the
school's tenant after the fact — rejected; Microsoft's own documentation
and multiple forum reports show this is often difficult or impossible
without IT-admin help, whereas a clean restart with a personal email took
minutes.

**Consequences:** All Azure work for this project now happens under the
personal subscription tied to `p.zargareian@gmail.com` — not the school
email used for the first, abandoned attempt. One hardening item flagged
but not yet applied: the storage account's network rule set still
defaults to `defaultAction: Allow` (any network can attempt to connect;
identity-based auth is still required to actually read/write data). Worth
restricting to a specific IP range later, same spirit as the Snowflake
least-privilege work.

## 2026-10-19 — Step 12: Azure DevOps Boards set up and populated

**Decision:** Azure DevOps organization `Pegahzar`, project `AIMSight`
(Basic process template) created. Backlog populated with one work item
per remaining roadmap step (Steps 11–32, 22 items total).

**Reason:** Per C15, the board had to be created and start reflecting
real usage now, not retroactively assembled near the end of the project —
otherwise it would be an artifact, not evidence of actual tracking.

**How:** Signed in to dev.azure.com with the same personal account
(`p.zargareian@gmail.com`) used for the Azure fix in the Step 11 entry
above, keeping all project identity under one account. Chose the Basic
process template (To Do / Doing / Done) over Agile/Scrum/CMMI, since those
are built for multi-person teams with sprints — unnecessary complexity for
a solo project. Added all 22 items via the Backlog view's quick-add (type
a title, press Enter, repeat). Immediately moved Steps 11 and 18 to Done
(both already genuinely complete) and this step (12) to Doing while it was
being finished, so the board matches reality from its very first day
instead of starting as 22 blank cards.

**Alternatives considered:** Agile or Scrum process templates — rejected,
sprint planning and story points add no value for one person working
sequentially through a fixed roadmap.

**Consequences:** Going forward, each step's board card should move
To Do → Doing → Done as work actually happens, in the same turn its
status changes in `PROJECT_SPEC.md` §7 — the two should never drift out of
sync. Step 12's own card should be dragged to Done now that this entry is
written.

## 2026-10-19 — Step 13: dbt project cleaned up and committed; checksum claim corrected with real code

**Decision:** Part (a): `aimsight_dbt/models/example/` (dbt's three
scaffolded example files) deleted, along with the now-empty `models:`
block it left behind in `dbt_project.yml`; `aimsight_dbt/` committed to
git for the first time. Part (b): `src/aimsight/ingest/checksum.py`
(`compute_md5()`, `verify_checksum()`, `ChecksumMismatchError`) written
with 8 passing tests in `tests/unit/test_checksum.py`.

**Reason:** Per C21, a 2026-10-14 audit found `aimsight_dbt/` untracked
with leftover scaffolding, and no code backing the Step 1 MD5-checksum
claim. The project's own rule is "done = tested + committed" — neither
was true until now.

**How:** Deleting the example models left `dbt_project.yml`'s `models:`
block empty; running `dbt parse` afterward surfaced two warnings pointing
at exactly that (`CustomKeyInConfigDeprecation` and an "unused
configuration paths" notice) — removed the whole block rather than leave
a warning sitting in the project, re-ran `dbt parse` clean, then
committed. For the checksum module, matched the existing house style
exactly: a custom exception (`ChecksumMismatchError`, same pattern as
`MissingExpectedColumnsError`), chunked file reads (constant memory
regardless of file size — matters once Step 16 pulls much larger bulk
files), case-insensitive comparison, and `tmp_path`-based synthetic tests
matching `test_clean_ai_devices.py`'s convention rather than a committed
fixture file.

**Alternatives considered:** For part (b), the spec offered a second path
— simply correct the claim's wording instead of building real code.
Rejected: the cost of building it was low (about 20 minutes) and
checkums are explicitly named as Pipeline-layer interview evidence in
Appendix A, so correcting the claim instead would have thrown away cheap,
legitimate evidence.

**Consequences:** The checksum module is tested and real, but **not yet
called** anywhere in the live ingest flow — `load_raw_ai_devices()` does
not invoke it. Wiring it in needs a recorded "expected checksum" per real
file, captured at download time, which doesn't exist for the files
currently in `data/raw/`. That wiring is Step 16's job (full source
extraction, where files are freshly downloaded and a real expected
checksum can be captured then) — already where Appendix A lists checksums,
not Step 1. `PROJECT_SPEC.md` §6's Step 1 row is corrected to reflect
this honestly rather than mark it fully resolved.

## 2026-10-19 — Step 14(e): Azure budget alert created

**Decision:** A monthly budget (`aimsight-monthly-budget`, $20, scoped to
the subscription) with two actual-spend alert thresholds (80%, 100%),
emailing `p.zargareian@gmail.com`, is created and confirmed visible in
the Cost Management Budgets list.

**Reason:** Per C12, a cost guardrail was needed before Step 25 (the paid
Airflow VM) introduces real ongoing spend. $20/month is comfortably above
the current near-zero storage cost, but low enough to catch a problem
(e.g. an accidentally-left-running VM) early rather than at month's end.

**How:** Scope selection briefly showed only a billing-account-level
entry ("Pegah Zar") rather than the subscription directly — expected for
an individual account, where the billing account and the one subscription
cover the same resources; used it as-is rather than hunting for a
separate subscription-level entry. The Alert recipients field required
pressing Enter after typing the email to commit it as a tag — typing
alone left the field reading as empty, which is why "Unique email address
is required" appeared even though text had been entered.

**Alternatives considered:** A single 100%-only threshold — rejected in
favor of two thresholds (80% and 100%), since a single alert only fires
once and a second, later threshold catches ongoing drift the first one
missed.

**Consequences:** With this, **Step 14 is complete except for part (d)**,
which remains intentionally deferred to the actual rebuild (~2026-10-30)
per the 2026-10-16 entry above. Remember this alert is a notification
only — it does not pause or stop any resource automatically.
