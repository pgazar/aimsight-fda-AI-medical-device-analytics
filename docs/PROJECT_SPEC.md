# AIMSight — Project Specification (Authoritative)

**Status:** FINAL — adopted 2026-10-14. Replaces the previous `PROJECT_SPEC.md` (the earlier version remains in git history). Decisions behind every change are logged in `docs/decision_log.md` (entries dated 2026-10-14). Future changes follow §11.

**Relationship to other docs:** The original master proposal, 8-week implementation plan, and executive KPI framework remain the foundational specs for *what* AIMSight analyzes and *why*. This document locks in the *how* (tooling, architecture, sequencing). `docs/kpi_dependency_table.md` (re-audited 2026-10-14) and `docs/decision_log.md` remain in force and are referenced, not duplicated, here.

---

## 0. Revision summary (what changed vs. the original spec)

Status legend: **DECIDED** = Pegah made the call. **APPLIED** = low-risk change written in and accepted with the final spec. **REJECTED** = proposal declined; original choice kept. **DONE** = delivered.

| ID | Change | Driver | Status |
|---|---|---|---|
| C1 | Named stakeholder (VP of Regulatory Strategy) + 4 executive business questions (§1.1) | READY: E | **DECIDED** |
| C2 | Analysis method + interpretation guardrails, moved up (§8.1) | READY: A | APPLIED |
| C3 | Full source extraction made an explicit step (Step 16) | READY: R | APPLIED |
| C4 | Grain declared for every planned table, now backed by real column names (§4.4) | READY: D | APPLIED |
| C5 | SQL and dbt standards (§3.1) | READY: D | APPLIED |
| C6 | Findings & Recommendations deliverable; case study leads with the business answer (§9) | READY: Y | APPLIED |
| C7 | Roadmap resequenced into phases with an analysis-first thin slice (§7) | READY: E/Y | **DECIDED** |
| C8 | Mac compatibility matrix, updated with the actual machine: M4 Max, 36 GB RAM (§2, §2.1) | Platform fit | APPLIED |
| C9 | Power BI on Mac via Windows VM | Platform fit | **WITHDRAWN** — superseded by C18 |
| C10 | Proposal to run Airflow only locally — **rejected**: Airflow is hosted on Azure (self-managed VM), developed locally in Docker (§4.1, §5, Step 25) | Pegah's explicit choice | **REJECTED** (original choice kept) |
| C11 | Snowflake: **let each trial lapse and rebuild on a new trial from code** (Step 14) | Platform fit | **DECIDED** |
| C12 | Cost guardrails: Azure budget alert; Snowflake trial-credit check | Platform | APPLIED |
| C13 | Excel/Power Query fed by a CSV extract | Platform fit | APPLIED — merged into C20 |
| C14 | CI/CD moved earlier (Step 17) | Data best practices | APPLIED |
| C15 | Azure DevOps Boards: **start using now** (Step 12) | Credibility of artifacts | **DECIDED** |
| C16 | Consistency fixes: KPI table re-audit + stale references | Spec consistency | **DONE** (`docs/kpi_dependency_table.md`) |
| C17 | Interview-readiness deliverable + 7-layer coverage map (§9, Appendix A) | Interview layer | APPLIED |
| C18 | **Dashboard tool: Power BI → Tableau** (Tableau Desktop Public Edition → Tableau Public) | Pegah's choice + Mac fit | **DECIDED** |
| C19 | Snowflake service user rebuilt as `TYPE = SERVICE` with key-pair auth (Step 14) | Required by Snowflake's password deprecation; needed for C11 | APPLIED |
| C20 | Mart export step: Snowflake marts → CSV extract, feeding both Tableau Public and Excel/Power Query (Step 22) | Tableau Public can't connect to Snowflake | APPLIED |
| C21 | Repo hygiene from audit: commit the untracked dbt project, remove dbt example models, back up the Step 1 checksum claim with code or correct it (Step 13) | "Done = tested + committed" rule | APPLIED |
| C22 | Data-modeling depth: recall↔submission bridge table, role-playing date dimension, star tables exported separately and related in Tableau, ERD deliverable (§4.4, Steps 22/24/27, §9) | Data-modeling layer; "data modeling" in job postings | **DECIDED** |
| C23 | Kafka kept as an optional extension (Step 31), clearly labeled a simulation | Pegah's choice | **DECIDED** |

---

## 1. Project purpose

AIMSight is a healthcare data analytics portfolio project targeting a healthcare data analyst / data engineering role. It ingests FDA data — AI-enabled device authorizations, adverse events, recalls — and answers a small set of executive business questions (§1.1), using a modern cloud data stack that ends in a public Tableau dashboard and a written set of findings and recommendations.

**Learning mode is on.** Every step is explained — design decisions, concepts, and rationale — not just executed silently. This is a teaching engagement as much as a build engagement.

### 1.1 Stakeholder and executive questions — [C1, DECIDED]

**Primary stakeholder (confirmed by Pegah):** VP of Regulatory Strategy at a mid-size medtech company deciding where and how to bring its next AI-enabled device to market.

**Secondary audience:** hospital value-analysis / procurement teams evaluating AI device vendors (they read the post-market sections).

| # | Executive question | Decision it informs | KPIs used as evidence | Earliest answerable |
|---|---|---|---|---|
| Q1 | Where is AI device authorization growth concentrated (clinical panel, regulatory pathway), and how crowded is each area? | Which clinical area to enter | 1, 2 (growth); 3, 4 (concentration, after MDM) | Q1a (growth) at Step 21; Q1b (concentration) at Step 26 |
| Q2 | How long does FDA review take by pathway (510(k) / De Novo / PMA) and panel? | Pathway choice and launch timeline | 5 | Step 26 (needs Step 16 extraction) |
| Q3 | Which pathways, panels, or manufacturers show more post-market problems *relative to their size*? | Risk planning; vendor due diligence | 6, 7, 8 (normalized, §8.1) | Step 26 |
| Q4 | How far can these signals be trusted? | How much weight to give Q1–Q3 | 9, 10 + guardrails | Alongside Q3 |

Rule: every dashboard sheet and every SQL analysis names the question (Q1–Q4) it serves. A KPI that serves no question gets cut or moved to an appendix sheet.

Pathway can be derived from the submission-number prefix (K = 510(k), DEN = De Novo, P = PMA); confirm the prefix set against the real file in Step 19.

---

## 2. Environment snapshot

| Item | Value |
|---|---|
| Machine | MacBook Pro, Apple **M4 Max** (14-core CPU: 10 performance + 4 efficiency), **36 GB** unified memory, ~1 TB SSD — arm64 architecture [C8] |
| Working directory | `workspace/fda-ai-device-safety/` under `/Users/pegahzargarian/projects/MCP-1/workspace/` |
| GitHub repo | `aimsight-fda-AI-medical-device-analytics`, account `pgazar`, public |
| Python | pyenv 3.11.11 (chosen over system Python 3.14.3 — too new for stable data-stack dependencies; decision logged). Native arm64 build. |
| Data sources | FDA API (`OPENFDA_API_KEY` in gitignored `.env`); real FDA AI/ML device CSVs in `data/` (gitignored) |
| Testing | pytest, `pytest.ini` sets `pythonpath = src` |

Machine identifiers (serial number, hardware UUID, provisioning UDID) are deliberately **not** recorded here — this spec lives in a public repo.

**Tool architecture note:** Claude's `str_replace` and `create_file` tools operate in an isolated sandbox, not on the local Mac. Every file write Claude produces must be relayed as exact content/commands for Pegah to apply locally via terminal.

### 2.1 Mac compatibility matrix — [C8, C18, C20]

| Tool | Runs natively on Apple silicon? | How it runs in this project | Risk / note |
|---|---|---|---|
| Python 3.11 / pandas / pytest | Yes (arm64) | pyenv venv | None — already working |
| dbt-snowflake | Yes | Local CLI → Snowflake (cloud) | Switch to key-pair auth in Step 14 (C19) |
| Snowflake | Cloud | 30-day trials, rebuilt from code (C11) | Each rebuild = new account identifier → update `~/.dbt/profiles.yml` |
| Azure CLI / Blob Storage | Yes (Homebrew `azure-cli`) | Cloud | Budget alert (C12) |
| Docker Desktop | Yes (Apple silicon build) | Local dev for Airflow; Kafka demo | 36 GB RAM: allocate ~8 GB to Docker; Airflow and Kafka can run together comfortably |
| Airflow | Yes, via Docker (official images are multi-arch) | **Dev:** local `docker compose` on the Mac. **Prod:** same compose file on an Azure Linux VM | Free-tier VM sizes are too small for Airflow (≥4 GB RAM needed) → a paid VM size; control cost with auto-shutdown + budget alert. Mac is arm64, VM is likely x86 — multi-arch images make this transparent |
| Kafka (KRaft) | Yes, via Docker (official `apache/kafka` image is multi-arch) | Local, separate module | None |
| **Tableau Desktop Public Edition** | Yes — native macOS app | Authoring + publishing to Tableau Public | Connects only to file-type sources (text/CSV, Excel, JSON, Google Drive, etc.), **not Snowflake** → reads the Step 22 export. 15M rows per data source (marts are far smaller). Not for commercial use — fine for a portfolio of public FDA data |
| Tableau Desktop Free Edition (optional) | Yes | Live Snowflake exploration while developing marts | Cannot publish to Tableau Public — exploration only |
| Excel + Power Query | Yes (Microsoft 365 for Mac) | Reads the same Step 22 export | Mac Power Query has no Snowflake connector |
| Azure DevOps Boards | Browser | Cloud | In use from Step 12 |
| GitHub Actions CI | Cloud (Linux x86 runners) | Runs pytest on push | Local arm64 vs. CI x86 is a non-issue for pinned pure-Python deps |

No Windows VM is needed anywhere in the stack.

---

## 3. Working principles (unchanged, non-negotiable)

- **Micro-step methodology** — one small, testable step at a time. Explicit stop points for confirmation before advancing.
- **No premature commits** — no `git add .` until output is validated.
- **Test before commit** — no file is committed without a corresponding test.
- **Synthetic fixtures** — tests use `tests/fixtures/`, not real FDA data files.
- **Decision logging** — every architectural or analytical decision goes in `docs/decision_log.md`.
- **Learning-first explanations** — Claude explains the *why*, not just the *what*, at every step.

### 3.1 SQL and dbt standards — [C5]

- **Layers and naming:** `stg_` (1:1 with a source, renamed/typed only) → `int_` (joins, entity resolution) → `fct_` / `dim_` (star schema) → `mart_` (KPI views per question).
- **Readable SQL:** CTE-first structure (`with source as (...), renamed as (...), final as (...) select * from final`); one logical step per CTE; no nesting deeper than one subquery.
- **Comment header** on every model: purpose, grain, question(s) served (Q1–Q4), upstream sources.
- **dbt tests per model:** `unique` + `not_null` on the grain key; `relationships` from facts to dimensions; `accepted_values` on pathway and panel codes.
- **Grain is documented** in each model's `schema.yml` description (see §4.4).
- **Analysis SQL** lives in `models/marts/` (or `analyses/`) and uses window functions where the question calls for them (YoY growth with `lag()`, manufacturer ranking with `rank()`, running share with `sum() over`).

---

## 4. Updated architecture

### 4.1 Main batch pipeline — [C10, C18, C20, C22]

```
FDA API / CSVs
   → Azure Blob Storage (raw landing zone, cloud)
   → Airflow (orchestration — hosted on an Azure VM; developed locally in Docker)
   → Snowflake (warehouse, cloud; rebuilt from code each trial)
   → dbt (transformation: star schema, entity resolution / MDM, tests)
   → mart export (Snowflake star tables → one CSV per fact/dimension + export timestamp) [C22]
   → Tableau Desktop Public Edition (tables joined with Tableau relationships) → Tableau Public
```

Design consequence: the public dashboard holds its own copy of the mart data, so it keeps working while a Snowflake trial lapses and is rebuilt.

### 4.2 Downstream / parallel modules

```
Mart export (same CSV extract) → Excel / Power Query   (ad-hoc business-user extract, small, non-core)

Historical adverse-event records → Kafka producer (replay/simulate)
   → Kafka topic
   → Kafka consumer (windowed aggregation)
   (Separate streaming demo module — clearly labeled as a simulation,
    not part of the main batch path, since FDA data updates at most daily)
```

### 4.3 Supporting artifacts

- `docs/` — governance catalog + lineage documentation (stands in for Collibra; see §5)
- Azure DevOps Boards — sprint/task tracking, **in active use from Step 12** (C15)
- `snowflake/setup.sql` + `scripts/rebuild_snowflake.sh` + `docs/runbook_snowflake_rebuild.md` — the account as code (C11, C19)

### 4.4 Planned tables and their grain — [C4, updated with audit evidence]

| Table | Grain (one row per…) | Key | Evidence / open question |
|---|---|---|---|
| `fct_authorization` | FDA submission (authorization decision) | `submission_number` | Present in `aiml-devices-csv.csv` (1,524 rows). Pathway from prefix |
| `dim_manufacturer` | Resolved manufacturer golden record (MDM output) | `manufacturer_sk` (surrogate) | Raw `Company` field present; no normalization yet |
| `dim_product_code` | FDA product code | `product_code` | `classification_QIH.csv` adds `device_class`, `regulation_number`, `review_panel` — extend to all AI product codes in Step 16 |
| `dim_panel` | Clinical review panel | `panel_code` | From `Panel (Lead)` |
| `dim_date` | Calendar day | `date_key` | **Role-playing dimension** [C22]: one table, joined in several roles — decision date and received date (`fct_authorization`), event date and received date (`fct_adverse_event_report`), recall-initiated date (`fct_recall`). Each fact carries one `*_date_key` per role |
| `bridge_recall_submission` [C22] | One recall ↔ one 510(k) submission pair | (`recall key`, `submission_number`) | Resolves the many-to-many: one recall can list several 510(k) numbers in `k_numbers`, and one submission can have several recalls. Built by splitting `k_numbers`; unmatched numbers kept and counted, not dropped |
| `fct_adverse_event_report` | MDR report | `mdr_report_key` | ✅ Field confirmed in the QIH extract. **No follow-up indicator in the current 12-column extract** — Step 16 must pull one (openFDA's report-type field) for KPI 7 |
| `fct_recall` | **Decision needed:** recall event (`res_event_number`) or recalled product (`product_res_number`) | see grain | No `recall_number` field exists. KPI 8 likely counts distinct `res_event_number`. `k_numbers` allows a **direct link to 510(k) submission numbers** — better than product-code matching; check coverage in Step 16 |
| `pipeline_run` | Pipeline execution | `run_id` | Doesn't exist yet; feeds KPI 10 |

SCD note: `dim_manufacturer` is the only likely slowly changing dimension (renames/acquisitions). Default to SCD Type 1 unless a question needs history; log the choice.

**Modeling notes [C22]:**
- **Conformed dimensions:** `dim_product_code`, `dim_manufacturer` and `dim_date` are shared by all three facts — this is what makes authorizations comparable with post-market events (Q3's normalization).
- **Degenerate dimension:** `submission_number` lives on `fct_authorization` with no dimension table of its own.
- **OLTP → OLAP story:** staging stays close to openFDA's nested source records (normalized); marts are deliberately denormalized for dashboard queries. Document both shapes in the ERD.
- **ERD:** `docs/architecture.md` includes an entity-relationship diagram with the grain written under each table name (§9 item 5).

---

## 5. Tool decisions: chosen vs. rejected, and why

| Layer | Chosen | Rejected alternatives | Rationale |
|---|---|---|---|
| Host | Azure (Blob Storage, Airflow VM, DevOps Boards) | — | Explicit requirement; real cloud story for interviews |
| Orchestrator | Airflow — **hosted on a self-managed Azure Linux VM**, developed locally in Docker [C10 proposal rejected; original choice kept] | Azure Data Factory, Prefect, ADF-managed Airflow, local-only Airflow | Airflow is more portable across employers than ADF. ADF's managed Airflow is deprecated and closed to new customers, so hosting means a self-managed VM running the same `docker compose` setup used locally (dev/prod parity). Tradeoffs accepted: a paid VM size (free-tier sizes are too small), plus VM upkeep. Mitigations: auto-shutdown schedule / start only for runs and demos, Azure budget alert, Airflow UI reached via SSH tunnel (not exposed publicly), SSH allowed only from Pegah's IP, Snowflake private key stored on the VM with restricted permissions (Azure Key Vault optional) |
| Warehouse | Snowflake, **30-day trials rebuilt from code** [C11, DECIDED] | Postgres, BigQuery, Databricks; converting to a paid account | Higher market signal than Postgres. No permanent free tier, so the account is treated as disposable: everything needed to recreate it lives in the repo. Raw data always lives outside Snowflake (local + Blob), so nothing is lost when a trial lapses |
| Warehouse auth | Service user `TYPE = SERVICE` with **key-pair** auth [C19] | Password auth | Snowflake is phasing out single-factor password sign-in, with enforcement for new users first; a rebuilt trial creates new users, so password-only would break. Also removes the password problems logged at Step 10 |
| Transformation | dbt (targeting Snowflake) | — | Unchanged |
| Dashboard | **Tableau Desktop Public Edition → Tableau Public** [C18, DECIDED] | Power BI, Looker, Streamlit | Native Mac app (no VM); free; publishes to a public profile that doubles as a portfolio. Tradeoff: no direct Snowflake connection and no scheduled refresh from Snowflake, so it reads the Step 22 export — documented as a conscious choice. Power BI rejected: Desktop is Windows-only, and publish-to-web needs a work/school account with an admin-enabled setting |
| Export layer | Python export script: Snowflake star tables → **one CSV per fact/dimension** + export timestamp [C20, C22] | Manual downloads; one flat "big table" CSV | Tested, repeatable, schedulable by Airflow. Separate tables keep the star schema intact so Tableau relationships can model it (the BI-side half of "data modeling", same concept as Power BI's model view). Tradeoff: a slightly more complex export and Tableau setup — accepted for the modeling signal. Excel gets a small flat extract |
| Business-user export | Excel / Power Query reading the Step 22 extract [C13→C20] | Direct Snowflake connection | Mac Power Query has no Snowflake connector |
| MDM | Entity resolution with confidence levels, explicitly named MDM | Profisee | Unchanged |
| Governance | Documented data catalog + lineage in `docs/` | Collibra | Unchanged |
| Streaming | Kafka producer/consumer demo, local Docker, separate module | — | Unchanged |
| Task tracking | Azure DevOps Boards, **used from Step 12 onward** [C15, DECIDED] | Jira | Free, already on Azure; real usage history instead of a retroactive artifact |
| CI | GitHub Actions running pytest [C14] | Azure Pipelines | Free for public repos; README badge |
| **Explicitly out of scope** | SAP / SAP S/4HANA | — | Unchanged (see §10) |

---

## 6. Progress log — Steps 1–10 — [C16, C21: audited 2026-10-14 against commit `ee2c801` + working tree]

| Step | What was built | Status |
|---|---|---|
| 1 | Raw CSVs copied with MD5 checksum verification | ⚠️ **Needs evidence** — no checksum code, test, or decision-log entry found in the repo (may have been a one-off terminal command). Fixed in Step 13 |
| 2 | Git initialized on `main`; `.gitignore` protects `.env`, `.venv/`, all `data/` subdirectories | ✅ Done |
| 3 | Virtual environment using pyenv Python 3.11.11 | ✅ Done |
| 4 | pandas 2.3.3 pinned; confirmed loading 1,524 rows × 6 columns | ✅ Done |
| 5 | `src/aimsight/config.py` path helper; `pytest.ini` sets `pythonpath = src` | ✅ Done |
| 6 | `src/aimsight/logging_config.py` — idempotent `configure_logging()` + `get_logger(__name__)` | ✅ Done |
| 7 | `src/aimsight/transform/clean_ai_devices.py` — `load_raw_ai_devices()`, `standardize_columns()` | ✅ Done |
| 8 | `parse_decision_date()` — explicit `%m/%d/%Y`; zero parse failures on the real 1,524-row file | ✅ Done |
| 9 | Snowflake trial on `AZURE_WESTUS2` (provisioned as Enterprise edition; Standard was intended — see decision-log correction); `aimsight_wh`, `aimsight`, `aimsight.raw`, `aimsight_role`, `aimsight_dev` | ✅ Done 2026-09-30 — objects exist only in that account until `setup.sql` (Step 14) |
| 10 | dbt project `aimsight_dbt`; `dbt debug/run/test` pass | ⚠️ **Not committed** — `aimsight_dbt/` is untracked, and it still contains dbt's example models. Fixed in Step 13 |

**Key learnings already logged** (see `docs/decision_log.md`):
- Pandas silently creates a phantom MultiIndex for rows with extra trailing fields instead of raising `ParserError`.
- Asserting an absolute logging-handler count is wrong (pytest adds handlers); assert idempotency instead.
- Exception patterns: guard clauses, EAFP try/except, `raise ... from exc`, custom exceptions, non-mutation.
- Snowflake/dbt connection issues: account locator vs. name, `MUST_CHANGE_PASSWORD`, zsh `!` history expansion, login lockout.

---

## 7. Roadmap — Step 11 onward — [C7 DECIDED: analysis-first; renumbered in revision 2]

"Old #" maps each step to the original spec so `docs/decision_log.md` references stay traceable.

**Phase B — De-risk the platform and complete the data (now)**

| Step | Old # | Task | Notes |
|---|---|---|---|
| 11 | 11 | Azure Blob Storage landing zone | In progress; may pause while Step 14 meets its deadline |
| 12 | 20 (C15) | **Azure DevOps Boards — set up and start using** | Backlog = Steps 11–32, one work item per step, sized as micro-steps. Move items as work happens |
| 13 | new (C21) | **Repo hygiene** | (a) Delete `models/example/` and its `dbt_project.yml` config block; commit `aimsight_dbt/` (confirm `target/` and `logs/` are ignored). (b) Step 1 checksum: add `src/aimsight/ingest/checksum.py` + test on a fixture, **or** correct the claim in the spec and resume bullets. Log it |
| 14 | new (C11, C19, C12) | **Snowflake rebuild-ready — finish before the current trial ends (~2026-10-30; check exact date in Admin → Billing)** | (a) `snowflake/setup.sql`: warehouse (XSMALL, auto-suspend 60s), database, schemas, role, grants, `aimsight_dev` as `TYPE = SERVICE` with an RSA public key. (b) Key pair generated locally, private key **outside the repo** (e.g., `~/.snowflake/`), `profiles.yml` switched to `private_key_path`. (c) `scripts/rebuild_snowflake.sh` + `docs/runbook_snowflake_rebuild.md`: sign up with plain email (not SSO — avoids the AWS detour), choose Azure West US 2, run `setup.sql`, update account identifier, `dbt debug`, reload, `dbt build`. (d) Test the runbook once on the new trial; record the rebuild time. (e) Azure budget alert. Repeat every ~30 days; calendar reminder |
| 15 | new (C18) | **Tableau spike** (time-boxed) | Install Tableau Desktop Public Edition; build one throwaway sheet from a small CSV with a date field; publish to Tableau Public; confirm the profile URL works logged out |
| 16 | new (C3) | **Full source extraction** | Adverse events for all AI-device product codes, **including the follow-up/report-type field** (KPI 7); recalls with `res_event_number`, `product_res_number`, `k_numbers`; classification for all product codes; 510(k)/PMA records with received dates (KPI 5; check De Novo coverage). Use openFDA bulk files if paging limits are hit. Checksum + tests on synthetic fixtures |
| 17 | 15 (C14) | CI/CD — GitHub Actions runs pytest on push | Green README badge |
| 18 | new (C16) | KPI dependency table re-audit | ✅ Done 2026-10-14 (`docs/kpi_dependency_table.md`) |

**Phase C — Analysis-first thin slice: answer Q1a end to end**

| Step | Old # | Task | Notes |
|---|---|---|---|
| 19 | 13 (part) | Load authorizations to Snowflake `raw`; dbt `stg_` + `fct_authorization`, `dim_panel`, `dim_date` with grain and tests | Run manually; orchestration comes in Phase D |
| 20 | "TBD" (C2) | `docs/analysis_method.md`: normalization rules and guardrails (§8.1) | Before the first analysis |
| 21 | new | SQL analysis for Q1a (KPIs 1–2 by panel and pathway, YoY with window functions) + first written insight | §3.1 standards |
| 22 | new (C20, C22) | **Star-table export script** (`src/aimsight/export/export_marts.py`, tested) + first Tableau Public sheet for Q1a | Exports `fct_authorization`, `dim_panel`, `dim_date` as separate CSVs; relate them in Tableau's logical layer (not one flattened file). First showable artifact: question → SQL → export → visual → insight. Export writes a timestamp file used as an interim freshness indicator |

**Phase D — Productionize and answer Q1b–Q4**

| Step | Old # | Task | Notes |
|---|---|---|---|
| 23 | 14 | Entity resolution / MDM with confidence levels → `dim_manufacturer` | Unlocks Q1b and KPI 9 |
| 24 | 13 (rest) | `fct_adverse_event_report`, `fct_recall` (grain decided), `bridge_recall_submission`, `dim_product_code`, `pipeline_run`; role-playing date keys on every fact | §4.4. dbt tests on the bridge: both keys `not_null`, pair `unique`, `relationships` to both sides; unmatched `k_numbers` counted in a test or audit model |
| 25 | 12 | Airflow DAG: extract → Blob → load → `dbt build` → export → write `pipeline_run`. (a) Build and test locally in Docker. (b) Deploy to an Azure Linux VM with the same compose file; choose the VM size and check its price at this step | Retries, idempotent loads; makes KPI 10 real. VM security and cost mitigations per §5 |
| 26 | new | SQL analysis for Q1b, Q2, Q3, Q4 | Normalized per §8.1 |
| 27 | 16 | Full Tableau dashboard on Tableau Public | One dashboard per question; 3–5 KPIs above the fold; freshness indicator from `pipeline_run`. Full star schema related in Tableau, including the bridge table for recall↔submission views |

**Phase E — Finishing layer and extensions**

| Step | Old # | Task | Notes |
|---|---|---|---|
| 28 | 17 | Excel / Power Query reading the Step 22 export | C20 |
| 29 | 18 | Governance documentation (data dictionary, lineage diagram, access tiers) | Dictionary entries accumulate in `schema.yml` from Step 19 |
| 30 | new (C6) | Findings & Recommendations + case study | §9 |
| 31 | 19 | Kafka streaming demo module | Optional extension |
| 32 | new (C17) | Interview readiness pack | §9 item 6 |

---

## 8. KPI framework

See `docs/kpi_dependency_table.md` (re-audited 2026-10-14) for the status of all 10 KPIs, their questions, real field evidence, and earliest step. Before building any dashboard sheet, confirm its prerequisites are satisfied and name its question (Q1–Q4).

### 8.1 Analysis method and interpretation guardrails — [C2]

**Normalization:**
- Post-market KPIs (6–8) are reported as rates against a denominator — e.g., MDR reports or recall events per authorized device in the same product code, panel, or pathway — and by decision-year cohort.
- Small denominators are flagged or suppressed below a threshold decided and logged in Step 20.

**Guardrails (on the dashboard and in the case study):**
- MDR reports are reports, not incidence rates; reporting can be incomplete, duplicated, or influenced by publicity and litigation.
- Linkage is stated with its confidence: recalls can often link directly to 510(k) numbers via `k_numbers`; adverse events typically link via product code or brand, which is approximate.
- Patterns are associations, not evidence that a device or manufacturer caused harm.
- High-confidence match percentage (KPI 9) is shown next to any manufacturer-level post-market result.

---

## 9. Final deliverables (the finishing layer)

1. **Polished GitHub repo** — README opens with the stakeholder and the four questions, then architecture diagram, setup instructions (including Apple silicon notes and the Snowflake rebuild runbook), link to the Tableau Public dashboard; `docs/` visible; CI badge; no secrets or data dumps.
2. **Clean dashboard** — Tableau Public, one dashboard per question, 3–5 KPIs above the fold, a data-freshness indicator, one-line "how to read this" captions, guardrail notes from §8.1.
3. **Findings & Recommendations** (`docs/findings.md`) — 3–5 insights: the number → what it means → recommendation → caveat.
4. **Case study (one page)** — leads with the most important finding and recommendation, then one hard technical decision in depth, one real tradeoff (e.g., disposable Snowflake trials + extract-based dashboard), one honest "what I'd do with more time".
5. **"What was built" explanation** (`docs/architecture.md`) — data flow, **ERD with the grain under each table name** [C22], why Snowflake/dbt, star schema and grain reasoning (bridge table, role-playing dates, SCD choice), failure/recovery design, the rebuild-from-code approach, Mac/cloud tradeoffs.
6. **Interview readiness pack** (`docs/interview_prep.md`, can stay private) — two-minute walkthrough (question → answer → one hard decision) and 4–5 ownership stories from `docs/decision_log.md` in situation–action–result form.
7. **Portfolio page** — one page: hook + dashboard screenshot + three links (dashboard, repo, case study) + contact + 5–6 tech tags. Tableau Public profile linked.

---

## 10. Explicitly out of scope (and why)

- **SAP / SAP S/4HANA** — no natural connection to FDA regulatory data; trial system is a fictional ERP company.
- **Collibra** — no individual/public access path exists (verified). Documented governance artifact substitutes.
- **BigQuery, Databricks** — redundant with Snowflake. Portability noted in `docs/architecture.md`.
- **Power BI** [C18] — replaced by Tableau: Windows-only Desktop would require a VM on the Mac, and public publishing requires a work/school account with an admin-enabled setting.
- **Looker** — redundant with Tableau.
- **Redis/MongoDB, additional NoSQL** — no fit; project is relational/batch.
- **Profisee** — concept covered by the MDM work without the licensed tool.
- **ADF-managed Airflow** — deprecated and closed to new customers.
- **Converting Snowflake to a paid account** [C11] — rejected in favor of rebuilding trials from code.

If a future conversation proposes adding one of these back in, check this section first.

---

## 11. Working agreement between Pegah and Claude

- Claude explains design decisions and rationale at each step (learning-first).
- Claude never commits or assumes local file state — every change is relayed as exact content or terminal commands for Pegah to apply.
- No step is marked done without a passing test and a commit.
- Any deviation from this spec gets logged in `docs/decision_log.md` and reflected back into this file.

---

## Appendix A — Coverage map: the 7 preparation layers — [C17]

| Layer | Where AIMSight demonstrates it | Gap to watch |
|---|---|---|
| 1. Foundation | Python, CSV/JSON, openFDA API, Linux/zsh, debugging (decision log) | Consider Parquet for the Blob landing format |
| 2. SQL | Steps 21 and 26: CTEs, window functions, MDR follow-up dedup, date logic | Be able to explain each query aloud |
| 3. Data modeling | §4.4: OLTP→OLAP, facts vs. dimensions, grain, surrogate keys, SCD choice, recall-grain decision, bridge table, role-playing and conformed dimensions, BI-side relationships in Tableau, ERD | Know why each grain was chosen; practice "design a schema for X" as clarify → grain → facts/dims → one tradeoff |
| 4. Pipeline | Steps 1–8, 16, 22, 25: checksums, idempotent loads, retries, `pipeline_run`, rebuild runbook | Design one backfill and one failure-recovery scenario |
| 5. Scale | Kafka demo; warehouse sizing and auto-suspend | Honest framing: small data; discuss what changes at 100× |
| 6. Platform | Blob, Airflow on an Azure VM (dev/prod parity), Snowflake roles + key-pair auth, disposable environments, governance docs, cost guards | The rebuild-from-code story is your strongest platform answer |
| 7. Interview | §9 item 6 | Practice clarifying questions about scale and freshness |
