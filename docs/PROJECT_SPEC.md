# AIMSight — Project Specification (Authoritative)

**Status:** Living document. This file is the single source of truth for scope, architecture, and progress. If anything in a conversation conflicts with this file, this file wins unless the person explicitly updates it.

**Relationship to other docs:** The original master proposal, 8-week implementation plan, and executive KPI framework remain the foundational specs for *what* AIMSight analyzes and *why*. This document is additive — it locks in the *how* (tooling, architecture, sequencing) after the Week 2 pivot described below. `docs/kpi_dependency_table.md` and `docs/decision_log.md` remain in force and are referenced, not duplicated, here.

---

## 1. Project purpose

AIMSight is a healthcare data analytics portfolio project targeting a healthcare data analyst / data engineering role. It ingests FDA data — AI-enabled device authorizations, adverse events, recalls — and surfaces executive KPIs through a modern cloud data stack ending in a published BI dashboard.

**Learning mode is on.** Every step is explained — design decisions, concepts, and rationale — not just executed silently. This is a teaching engagement as much as a build engagement.

---

## 2. Environment snapshot

| Item | Value |
|---|---|
| Working directory | `workspace/fda-ai-device-safety/` under `/Users/pegahzargarian/projects/MCP-1/workspace/` |
| GitHub repo | `aimsight-fda-AI-medical-device-analytics`, account `pgazar`, public |
| Python | pyenv 3.11.11 (chosen over system Python 3.14.3 — too new for stable data-stack dependencies; decision logged) |
| Data sources | FDA API (`OPENFDA_API_KEY` in gitignored `.env`); real FDA AI/ML device CSVs in `data/` (gitignored) |
| Testing | pytest, `pytest.ini` sets `pythonpath = src` |

**Tool architecture note:** Claude's `str_replace` and `create_file` tools operate in an isolated sandbox, not on the local Mac. Every file write Claude produces must be relayed as exact content/commands for Pegah to apply locally via terminal.

---

## 3. Working principles (unchanged, non-negotiable)

- **Micro-step methodology** — one small, testable step at a time. Explicit stop points for confirmation before advancing.
- **No premature commits** — no `git add .` until output is validated.
- **Test before commit** — no file is committed without a corresponding test.
- **Synthetic fixtures** — tests use `tests/fixtures/`, not real FDA data files.
- **Decision logging** — every architectural or analytical decision goes in `docs/decision_log.md`.
- **Learning-first explanations** — Claude explains the *why*, not just the *what*, at every step.

---

## 4. Updated architecture

### 4.1 Main batch pipeline

```
FDA API / CSVs
   → Azure Blob Storage (raw landing zone)
   → Airflow (orchestration, hosted on Azure)
   → Snowflake (warehouse)
   → dbt (transformation: star schema, entity resolution / MDM, tests)
   → Power BI (published dashboard, public web link)
```

### 4.2 Downstream / parallel modules

```
Snowflake → Excel / Power Query   (ad-hoc business-user extract, small, non-core)

Historical adverse-event records → Kafka producer (replay/simulate)
   → Kafka topic
   → Kafka consumer (windowed aggregation)
   (Separate streaming demo module — clearly labeled as a simulation,
    not part of the main batch path, since FDA data updates at most daily)
```

### 4.3 Supporting artifacts (not data-flow, but part of the architecture)

- `docs/` — governance catalog + lineage documentation (stands in for Collibra; see §6)
- Azure DevOps Boards — sprint/task tracking (stands in for Jira)

---

## 5. Tool decisions: chosen vs. rejected, and why

| Layer | Chosen | Rejected alternatives | Rationale |
|---|---|---|---|
| Host | Azure (Blob Storage, Airflow hosting, DevOps Boards) | — | Explicit requirement; also gives a real cloud-hosting story for interviews |
| Orchestrator | Airflow (self-hosted on Azure) | Azure Data Factory, Prefect | Airflow is more portable across employers than ADF; ADF and Airflow are alternatives, not additions — using both would be redundant |
| Warehouse | Snowflake | Postgres, BigQuery, Databricks | Higher market signal than Postgres; dbt is warehouse-agnostic so the swap from the original Postgres plan is a config change, not a rebuild. BigQuery/Databricks are alternatives to Snowflake — building all three would dilute depth for no added signal |
| Transformation | dbt (targeting Snowflake) | — | Unchanged tool, new connection target |
| Dashboard | Power BI, published to web | Tableau, Looker, Streamlit | Explicit requirement; Power BI's public web-publish feature preserves the "clean, linkable dashboard" deliverable |
| Business-user export | Excel / Power Query | — | Kept deliberately small — a downstream convenience layer, not core infrastructure |
| MDM | Entity resolution with confidence levels (already planned), explicitly named and framed as MDM | Profisee | Profisee is a licensed commercial MDM tool with no realistic individual access; the *concept* of MDM is fully demonstrated by the golden-record entity resolution work already in the 8-week plan |
| Governance | Documented data catalog + lineage in `docs/` | Collibra | **Confirmed:** Collibra offers no public free trial; access is enterprise-sales-only. The documented artifact demonstrates the same governance thinking without a tool that can't be obtained |
| Streaming | Kafka producer/consumer demo, local Docker, clearly separate module | — | Genuinely buildable and free (local KRaft-mode broker); kept isolated from the main batch pipeline so it doesn't misrepresent FDA data as real-time |
| Task tracking | Azure DevOps Boards | Jira | Free, and already using Azure — no separate account needed |
| **Explicitly out of scope** | SAP / SAP S/4HANA | — | SAP has a free 30-day trial, but it's a preloaded fictional ERP company (sales orders, procurement, financials) with no natural bridge to FDA regulatory/device-safety data. Forcing it in would look like a checkbox exercise, not a real integration. If SAP exposure is needed for job applications, address it separately (a short course, a resume line) — not inside this project |

---

## 6. Progress log — Steps 1-8 (COMPLETE, unaffected by the pivot)

None of the work below depends on the warehouse/dashboard choice — it's all upstream, pure Python/pandas working on local files. **Nothing here needs to change.**

| Step | What was built | Status |
|---|---|---|
| 1 | Raw CSVs copied with MD5 checksum verification | ✅ Done, tested, committed |
| 2 | Git initialized on `main`; `.gitignore` protects `.env`, `.venv/`, all `data/` subdirectories | ✅ Done |
| 3 | Virtual environment using pyenv Python 3.11.11 | ✅ Done |
| 4 | pandas 2.3.3 pinned; confirmed loading 1,524 rows × 6 columns | ✅ Done |
| 5 | `src/aimsight/config.py` path helper using `Path(__file__).resolve().parents[2]`; `pytest.ini` sets `pythonpath = src` | ✅ Done |
| 6 | `src/aimsight/logging_config.py` — idempotent `configure_logging()` + `get_logger(__name__)` pattern | ✅ Done |
| 7 | `src/aimsight/transform/clean_ai_devices.py` — `load_raw_ai_devices()`, `standardize_columns()` | ✅ Done |
| 8 | `parse_decision_date()` — explicit `%m/%d/%Y` format; zero parse failures on real 1,524-row file | ✅ Done |

**Key learnings already logged** (see `docs/decision_log.md` for full detail):
- Pandas silently creates a phantom MultiIndex for rows with extra trailing fields instead of raising `ParserError` — deferred to a later validation step.
- Asserting an absolute logging-handler count is wrong (pytest's plugin adds handlers); assert idempotency instead.
- Exception patterns in use: guard clauses for missing files, EAFP try/except for malformed CSV, `raise ... from exc` chaining, custom exceptions (e.g. `MissingExpectedColumnsError`), non-mutation via returned new DataFrames.

---

## 7. Roadmap — Step 9 onward (updated for the new architecture)

The step *numbers and philosophy* from the original 8-week plan are preserved. Only the target tools inside each step change, per §5.

| Step (approx.) | Task | Notes |
|---|---|---|
| 9 | Snowflake account + schema setup | Replaces "Postgres warehouse setup" 1:1 |
| 10 | dbt project init, `profiles.yml` pointed at Snowflake | Same dbt skills as originally planned, new connection |
| 11 | Azure Blob Storage landing zone | Raw data lands here before Snowflake load |
| 12 | Airflow DAG wrapping the Step 7-8 functions as tasks | This is where `clean_ai_devices.py` and `parse_decision_date()` get called by a scheduler instead of run standalone |
| 13 | dbt models: star schema (facts/dimensions per KPI dependency table) | Reference `docs/kpi_dependency_table.md` for sequencing |
| 14 | Entity resolution / MDM with confidence levels | Explicitly documented and labeled as MDM in `docs/` |
| 15 | CI/CD pipeline | Runs pytest suite on push; green badge on README |
| 16 | Power BI dashboard, connected to Snowflake, published to web | Executive KPIs per framework, 3-5 above the fold |
| 17 | Excel / Power Query extract | Small, downstream, business-user consumption artifact |
| 18 | Governance documentation (data dictionary, lineage diagram, access tiers) | `docs/` — Collibra-equivalent thinking |
| 19 | Kafka streaming demo module | Separate from main pipeline; Docker-based; producer replays historical events, consumer does windowed aggregation |
| 20 | Azure DevOps Boards setup | Sprint/task tracking artifact |
| — | Responsible-interpretation guardrails | Per project charter — timing TBD, likely alongside dashboard work (Step 16) |

Timeline reality check: given the added scope (Snowflake, Airflow, Power BI, MDM, governance docs, Kafka demo, DevOps boards) on top of the original 8-week plan, expect roughly **4-6 additional weeks** beyond the original endpoint. This is not a sign anything is behind — the original 8-week plan didn't include several of these additions.

---

## 8. KPI framework

Unchanged. `docs/kpi_dependency_table.md` maps each of the 10 executive KPIs to the earliest week its prerequisites exist, and remains additive to the master proposal. As the warehouse/dbt work in Steps 9-13 progresses, cross-check against this table to confirm each KPI's prerequisites are actually satisfied before building its dashboard tile.

---

## 9. Final deliverables (the finishing layer)

1. **Polished GitHub repo** — root README with problem statement, architecture diagram, working setup instructions, link to live Power BI dashboard; `docs/` folder linked and visible; CI badge once Step 15 lands; no secrets or data dumps.
2. **Clean dashboard** — Power BI, published to web, 3-5 KPIs above the fold, a data-freshness indicator, one-line "how to read this" captions.
3. **Case study (one page)** — the problem in plain English, one hard decision walked through in depth (e.g. the phantom-MultiIndex discovery, or Postgres→Snowflake pivot reasoning), one real tradeoff, one honest "what I'd do with more time" (e.g. gesturing at true streaming/distributed scale beyond the Kafka demo).
4. **"What was built" explanation** (`docs/architecture.md`) — the technical writeup: data flow, why Snowflake/dbt, star schema reasoning, pipeline failure/recovery design.
5. **Portfolio page** — one page, easy to find (GitHub Pages or a pinned repo README), hook + dashboard screenshot + three links (dashboard, repo, case study) + contact info + 5-6 tech tags, no more.

---

## 10. Explicitly out of scope (and why — so this doesn't get re-litigated later)

- **SAP / SAP S/4HANA** — no natural connection to FDA regulatory data; trial system is a fictional ERP company. See §5.
- **Collibra** — no individual/public access path exists (verified). Documented governance artifact substitutes.
- **BigQuery, Databricks** — redundant with Snowflake as the chosen warehouse. Portability noted in `docs/architecture.md`, not separately built.
- **Tableau, Looker** — redundant with Power BI as the chosen dashboard tool.
- **Redis/MongoDB, additional NoSQL** — no fit; project is relational/batch, not cache or document-store driven.
- **Profisee** — see MDM row in §5; concept covered without the specific tool.

If a future conversation proposes adding one of these back in, check this section first — the reasoning here should still hold unless something material has changed (e.g. a tool ships a genuine free tier where none existed before).

---

## 11. Working agreement between Pegah and Claude

- Claude explains design decisions and rationale at each step (learning-first).
- Claude never commits or assumes local file state — every change is relayed as exact content or terminal commands for Pegah to apply.
- No step is marked done without a passing test and a commit.
- Any deviation from this spec (new tool, changed sequencing, changed scope) gets logged in `docs/decision_log.md` and reflected back into this file.
