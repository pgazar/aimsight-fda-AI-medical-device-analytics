# Executive KPI Dependency Table

Tracks the 10 required executive KPIs against the project's actual state,
so each one gets built when its real prerequisites exist — not before.
Audited 2026-07-23 against the repo as of commit d384ba3.

Status values: `Planned`, `In progress`, `Implemented`, `Validated`, `Deployed`.

| # | KPI | Status | Required source(s) | Required fields (confirmed present?) | Missing dependency | Earliest fit in the 8-week plan |
|---|-----|--------|--------------------|----------------------------------------|---------------------|----------------------------------|
| 1 | Total Authorized AI Devices | Planned | `aiml-devices-csv.csv` (cleaned) | `submission_number` — present in raw file, standardized in Step 7 | Postgres warehouse + `mart_executive_kpis` view for the *real* SQL-based KPI (an informal pandas sanity check is possible as early as end of Week 1) | Week 5 (SQL analysis), on top of Week 3 warehouse |
| 2 | YoY Authorization Growth | Planned | same as #1 | `date_of_final_decision` — present but **not yet parsed to a real date** (that's Step 8, next) | Step 8 (date parsing) + warehouse | Week 5 |
| 3 | Total Manufacturers | Planned | `dim_manufacturer` (normalized) | raw `Company` field exists; no normalization exists yet | Manufacturer normalization (Week 4, matching methodology) | Week 5, blocked on Week 4 |
| 4 | Top-Five Manufacturer Share | Planned | same as #3 | same as #3 | Same as #3 | Week 5, blocked on Week 4 |
| 5 | Median Observed Review Duration | Planned | 510(k)/PMA records with receipt + decision dates | Not extracted — the 6-column AI-device CSV has no receipt date | 510(k)/PMA extraction (Week 2) | Week 5, blocked on Week 2 |
| 6 | Unique MDR Reports | Planned | openFDA adverse-event data | `adverse_events_QIH_...csv` exists for QIH only, not yet loaded/modeled; no `mdr_report_key` field confirmed yet | Full adverse-event extraction (Week 2) + `fact_adverse_event_report` (Week 3) | Week 5, blocked on Week 2 & 3 |
| 7 | Follow-Up Report Percentage | Planned | same as #6 | Follow-up indicator logic not built | Same as #6 + follow-up detection (Week 3, spec section 23.5) | Week 5, blocked on Week 2 & 3 |
| 8 | Unique Recall Count | Planned | openFDA recall data | `recalls_QIH.csv` exists for QIH only; no `recall_number` field confirmed | Full recall extraction (Week 2) + `fact_recall` (Week 3) | Week 5, blocked on Week 2 & 3 |
| 9 | High-Confidence Match Percentage | Planned | Entity-matching framework | Nothing built yet | Full matching methodology, implemented AND manually validated (Week 4) — spec explicitly says not to use this metric before that | Week 5, blocked on Week 4 (hard blocker) |
| 10 | Last Successful Data Refresh | Planned | `pipeline_run` operational table | Table doesn't exist; only mentioned in a docstring comment | `pipeline_run` table (Week 2/3) + at least one real orchestrated run (Week 7 scheduling makes this meaningful) | Realistically Week 7 |

## Honest summary

**None of the 10 KPIs are ready to implement in their real, SQL-view form yet.**
Every one of them depends on infrastructure that doesn't exist in this repo
today: the Postgres warehouse, dbt marts, the full extraction pipeline
(510k/PMA/recall/adverse-event beyond the QIH test), manufacturer
normalization, and the entity-matching framework. That's expected — we're
still on Step 8 of Week 1's local data-foundation phase.

KPI #1 (Total Authorized AI Devices) is the *closest* to ready, exactly as
noted: it only needs a clean `submission_number` column, which Step 7
already produced. Its official implementation (SQL view + test + metric
dictionary entry) still waits for the Week 3 warehouse, but nothing stops
an informal pandas-only sanity check once Week 1's cleaning is fully done.

## What this changes about the plan

Nothing. This table is additive tracking, not a detour. The original
week-by-week sequence continues unchanged; this document exists so that
the moment each week's infrastructure lands, we immediately know which
KPI(s) just became buildable instead of re-deriving it from scratch.
