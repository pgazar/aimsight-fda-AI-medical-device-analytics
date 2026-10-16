-- =============================================================
-- AIMSight — Snowflake account setup (infrastructure as code)
-- =============================================================
-- PURPOSE
--   Recreate every Snowflake object this project depends on, in one
--   run, against a brand-new trial account. Snowflake trials last
--   30 days with no permanent free tier (see docs/decision_log.md,
--   "Snowflake: let trials lapse and rebuild from code"), so this
--   script is what makes a lapsed trial a quick rebuild instead of
--   redoing all the manual setup and debugging from Steps 9-10.
--
-- HOW TO USE (also see docs/runbook_snowflake_rebuild.md once it
-- exists — Step 14(c)):
--   1. Sign up for a new Snowflake trial using the PLAIN EMAIL form,
--      not a Google/Microsoft SSO button. An SSO shortcut silently
--      skips the cloud/edition/region picker and can land the
--      account on the wrong cloud provider (this happened once —
--      see docs/decision_log.md, 2026-09-30 entry).
--   2. On the configuration screen: Edition = Standard,
--      Cloud = Microsoft Azure, Region = West US 2 (Washington).
--   3. Log into Snowsight as the default admin (ACCOUNTADMIN) the
--      trial creates, open a worksheet, and run this entire file.
--   4. Update ~/.dbt/profiles.yml's `account:` value to match the
--      NEW account's identifier (Admin -> Accounts -> look for the
--      "Account Identifier" column — NOT the account locator, see
--      docs/decision_log.md, 2026-09-30 dbt-connection entry for
--      why that distinction matters).
--   5. Nothing else in profiles.yml needs to change. The SAME local
--      key pair (~/.snowflake/rsa_key.p8 / rsa_key.pub) is reused
--      across rebuilds — only the account identifier changes.
--   6. Run `dbt debug` to confirm the new account connects.
--
-- This script is idempotent everywhere Snowflake's syntax allows it
-- (IF NOT EXISTS), so re-running it against an account that already
-- has these objects is safe and won't error.
-- =============================================================

USE ROLE ACCOUNTADMIN;

-- -------------------------------------------------------------
-- 1. Compute: a small, cheap warehouse that auto-suspends when
--    idle, so trial credits aren't burned while nobody's querying.
-- -------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS aimsight_wh
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- -------------------------------------------------------------
-- 2. Storage: the database and its first schema. STAGING and
--    MARTS schemas get added later (Step 19+), once the dbt
--    models that need them exist — no point creating empty
--    schemas ahead of the code that will populate them.
-- -------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS aimsight;
CREATE SCHEMA IF NOT EXISTS aimsight.raw;

-- -------------------------------------------------------------
-- 3. A dedicated, least-privilege role for this project. Daily
--    project work (dbt, scripts) should never run as ACCOUNTADMIN.
-- -------------------------------------------------------------
CREATE ROLE IF NOT EXISTS aimsight_role;
GRANT USAGE ON WAREHOUSE aimsight_wh TO ROLE aimsight_role;
GRANT USAGE, CREATE SCHEMA ON DATABASE aimsight TO ROLE aimsight_role;
GRANT ALL ON SCHEMA aimsight.raw TO ROLE aimsight_role;

-- -------------------------------------------------------------
-- 4. The service user dbt connects as.
--
--    Built directly as TYPE = SERVICE with key-pair auth from the
--    very start — no password, no MUST_CHANGE_PASSWORD, none of
--    the password problems logged in docs/decision_log.md
--    (2026-09-30 entry). That's the lesson from the first manual
--    setup, applied here so a rebuild never has to relearn it.
--
--    The value below is the PUBLIC half of the key pair that
--    lives at ~/.snowflake/rsa_key.p8 (private) / rsa_key.pub
--    (public) on the developer's machine. Public keys are meant
--    to be shared — safe to commit to a public repo. The PRIVATE
--    key is never in this file and never will be.
-- -------------------------------------------------------------
CREATE USER IF NOT EXISTS aimsight_dev
  TYPE = SERVICE
  RSA_PUBLIC_KEY = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkWNNqLVqKuOrUdzknZIUxyPXZSCCT/3EI7ybDlxIWGPxCtbWlEzueJKD2LiOqpmFV5TAXK6Ln9rKVX4ZLfbdA63CjPvB+yrOUv16es9VuCPMpMCnYU601hizKxRHswtWFEyBSdzF0bVUUwyclknK9PsNRiIopaX9ESRcI3pWe0z3QG9sxMoAIwPS/BUJwxjVMvBr+yiHg6AynUWoKytEe2rm3C0Rf9DJeyjUEoxYXbvQA7a/AAhFAxhrkpDswTuzw4Zv8JIkP6up6rKVLS0wlmggEI1LZ2ZKhXCv8ev1jGlvIN/xwkqGZIWy9uuIcjuzpuqJPoVNryd8BYh37RkJuwIDAQAB'
  DEFAULT_ROLE = aimsight_role
  DEFAULT_WAREHOUSE = aimsight_wh
  COMMENT = 'dbt connection for the AIMSight project — key-pair auth only, no password';

GRANT ROLE aimsight_role TO USER aimsight_dev;

-- -------------------------------------------------------------
-- 5. Sanity check — after running this script, log into Snowsight
--    AS aimsight_dev (not admin) and run the line below by itself
--    to confirm the new account is wired together correctly:
--
--      SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
--
--    Expect: AIMSIGHT_DEV, AIMSIGHT_ROLE, AIMSIGHT_WH
-- -------------------------------------------------------------
