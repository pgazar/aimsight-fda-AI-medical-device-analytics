# Snowflake Trial Rebuild Runbook

**Why this exists:** Snowflake trials last 30 days with no permanent free
tier (see `docs/decision_log.md`, "Snowflake: let trials lapse and rebuild
from code"). This document is what turns "the trial expired" from a
multi-hour redo into a 15-minute checklist.

**What you do NOT need to redo:** the local RSA key pair at
`~/.snowflake/rsa_key.p8` / `rsa_key.pub`. It's independent of any one
Snowflake account — the same key pair gets reused across every rebuild.
Only the *account identifier* changes each time.

---

## Step 1 — Sign up for a new trial

Go to **signup.snowflake.com** and use the **plain email form** —
not a "Continue with Google/Microsoft" button. An SSO shortcut silently
skips the cloud/edition/region picker (this happened once already — see
`docs/decision_log.md`, 2026-09-30 entry — and landed the account on AWS
instead of Azure).

If this email has already been used for a trial, use a plus-alias
(e.g. `yourname+sf3@gmail.com`) — most inboxes still deliver it normally.

## Step 2 — Choose the right configuration

On the account-configuration screen:
- **Edition:** Standard
- **Cloud provider:** Microsoft Azure
- **Region:** West US 2 (Washington) — closest to San Jose, CA

(Note: the previous trial was provisioned as Enterprise edition despite
selecting Standard — Snowflake may do this for trial accounts regardless
of the choice made. Not a problem either way, just don't be surprised.)

## Step 3 — Verify the region landed correctly

Log into Snowsight as the new account's default admin, open a worksheet,
and run:

```sql
SELECT CURRENT_REGION();
```

Expect `AZURE_WESTUS2`. If it shows something else, the trial didn't land
where intended — consider redoing Step 1.

## Step 4 — Run the setup script

Open a new worksheet, paste the **entire contents** of
`snowflake/setup.sql` from this repo, and run it. This single script
recreates the warehouse, database, schema, role, and the `aimsight_dev`
service user — already configured with key-pair auth and `TYPE = SERVICE`
from the start, so there's no password step to go through at all this
time.

## Step 5 — Find the new account identifier

In Snowsight: profile icon (bottom-left) → **Account**, or
**Admin → Accounts**. Find the **Account Identifier** (sometimes shown as
`orgname-accountname`) — this is the value to copy.

**Important:** this is *not* the same as the account locator returned by
`SELECT CURRENT_ACCOUNT();` — that distinction caused a real debugging
session last time (see `docs/decision_log.md`, 2026-09-30 dbt-connection
entry). Copy the identifier shown in the UI directly rather than deriving
it.

## Step 6 — Update `profiles.yml` and verify

Run `scripts/rebuild_snowflake.sh` (see that file for what it does) with
the new account identifier, or follow its manual fallback instructions if
you'd rather not run a script. Either way, this step ends with:

```bash
dbt debug
```

showing `All checks passed!`.

## Step 7 — Reload data (once there's real data in later steps)

At this point in the project (Step 14), there's no real data loaded yet
beyond dbt's own scaffolded example models — so this step is a placeholder
for later: once Steps 19+ build real `stg_`/`fct_`/`dim_` models, a rebuild
will also need `dbt build` (or a re-run of the Airflow DAG once it exists)
to repopulate the warehouse from the raw data that always lives outside
Snowflake (local + Azure Blob).

## Step 8 — Record the rebuild

Note the date, how long the rebuild actually took, and anything that
tripped you up, in `docs/decision_log.md`. This is what Step 14(d) is
checking — not just "does the script exist" but "does it actually work
when you need it."

## What happens to the old, lapsed account

Nothing to clean up — Snowflake trials simply stop working after 30 days.
No data is lost, because raw FDA data always lives locally and in Azure
Blob Storage, never only in Snowflake.
