# Executive KPI Dependency Table

Tracks the 10 required executive KPIs against the project's actual state,
so each one gets built when its real prerequisites exist — not before.

**Re-audited 2026-10-14** (read-only) against commit `ee2c801` plus the working
tree. Previous audit: 2026-07-23 at commit `d384ba3`. Step numbers refer to
`docs/PROJECT_SPEC.md` (final, 2026-10-14); "Q" refers to the executive questions in
its §1.1.

Status values: `Planned`, `In progress`, `Implemented`, `Validated`, `Deployed`.

## What the audit found in the repo

| Source file in `data/raw/` | Data rows | Columns confirmed |
|---|---|---|
| `aiml-devices-csv.csv` | 1,524 | Date of Final Decision, Submission Number, Device, Company, Panel (Lead), Primary Product Code |
| `adverse_events_QIH_20180101_20261231.csv` | 9 | mdr_report_key, report_number, date_received, date_of_event, event_type, report_source_code, product_code, brand_name, generic_name, manufacturer_name, model_number, device_operator |
| `recalls_QIH.csv` | 1 | includes cfres_id, product_res_number, res_event_number, event_date_initiated, recall_status, product_code, k_numbers, recalling_firm, reason_for_recall, root_cause_description, openfda.device_class |
| `classification_QIH.csv` | 1 | includes product_code, review_panel, medical_specialty, device_class, regulation_number, submission_type_id |

dbt: only dbt's example models exist; no AIMSight models yet. `aimsight_dbt/` is not committed. No `pipeline_run` table.

## KPI table

| # | KPI | Question | Status | Required source(s) | Required fields — confirmed present? | Missing dependency | Earliest step |
|---|-----|----------|--------|--------------------|----------------------------------------|---------------------|---------------|
| 1 | Total Authorized AI Devices | Q1a | Planned (pandas sanity check possible today) | `aiml-devices-csv.csv` (cleaned) | ✅ `submission_number` — present, standardized in Step 7 | Snowflake load + `fct_authorization` + mart (Step 19) | SQL: Step 21 · Dashboard: Step 22 |
| 2 | YoY Authorization Growth | Q1a | Planned | same as #1 | ✅ `date_of_final_decision` — **parsed to a real date in Step 8, zero failures** (changed since last audit) | Same as #1 + `dim_date` (Step 19) | SQL: Step 21 · Dashboard: Step 22 |
| 3 | Total Manufacturers | Q1b | Planned | `dim_manufacturer` (MDM output) | ⚠️ raw `Company` present; no normalization | Entity resolution / MDM (Step 23) | Step 26 |
| 4 | Top-Five Manufacturer Share | Q1b | Planned | same as #3 | same as #3 | Same as #3 | Step 26 |
| 5 | Median Observed Review Duration | Q2 | Planned | 510(k)/PMA records with received + decision dates | ❌ AI-device CSV has only the decision date | Extraction of submission records with received dates (Step 16); confirm De Novo coverage | Step 26 |
| 6 | Unique MDR Reports | Q3 | Planned | openFDA adverse events, all AI product codes | ✅ `mdr_report_key` — **confirmed** in the QIH extract (changed since last audit); ⚠️ only 9 rows, one product code | Full extraction (Step 16) + `fct_adverse_event_report` (Step 24) | Step 26 |
| 7 | Follow-Up Report Percentage | Q3 | Planned | same as #6 | ❌ **No follow-up / report-type field in the current extract** | Step 16 must pull the report-type field; follow-up logic in `fct_adverse_event_report` (Step 24) | Step 26 |
| 8 | Unique Recall Count | Q3 | Planned | openFDA recalls, all AI product codes | ⚠️ No `recall_number` field (as the old table assumed). Available keys: `res_event_number` (recall event), `product_res_number` (recalled product), `cfres_id`. `k_numbers` enables direct linkage to 510(k) submission numbers | Grain decision (event vs. product) + full extraction (Step 16) + `fct_recall` (Step 24) | Step 26 |
| 9 | High-Confidence Match Percentage | Q4 | Planned | Entity-matching framework | ❌ Nothing built | MDM implemented **and** manually validated (Step 23) — hard blocker; do not show before then | Step 26 |
| 10 | Last Successful Data Refresh | Q4 | Planned | `pipeline_run` operational table | ❌ Table doesn't exist | Interim: export timestamp from the mart export (Step 22), labeled as "last export". Real: Airflow writing `pipeline_run` (Step 25) | Interim: Step 22 · Real: Step 25 |

## Honest summary

None of the 10 KPIs are implemented in SQL yet, which is expected: no AIMSight
dbt models exist so far. KPIs 1 and 2 are the closest — every field they need is
present and cleaned, so they only wait on the Snowflake load and the first
models. That is why the thin slice (Steps 19–22) uses them to answer Q1a.

Two assumptions in the 2026-07-23 table were wrong and are corrected above:
recalls have no `recall_number` field, and the adverse-event extract has no
field for detecting follow-up reports. Both are now explicit requirements for
the Step 16 extraction.

## Changes vs. the 2026-07-23 audit

- Replaced Postgres warehouse and "Week N" references with Snowflake and step numbers.
- Added a "Question" column linking each KPI to Q1–Q4.
- KPI 2: date parsing done (Step 8).
- KPI 6: `mdr_report_key` confirmed present.
- KPI 7: missing follow-up field identified.
- KPI 8: recall key corrected; grain decision and `k_numbers` linkage added.
- KPI 10: interim freshness indicator from the export step.
- Added the data-file inventory (including `classification_QIH.csv`, not mentioned before).
