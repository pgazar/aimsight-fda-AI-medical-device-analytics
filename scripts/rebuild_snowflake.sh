#!/usr/bin/env bash
#
# rebuild_snowflake.sh — update profiles.yml with a new Snowflake account
# identifier after a trial rebuild, then re-verify the dbt connection.
#
# WHAT THIS DOES NOT DO (still manual — see docs/runbook_snowflake_rebuild.md):
#   - Sign up for the new trial
#   - Choose Azure / West US 2 on the signup form
#   - Run snowflake/setup.sql in the new account's Snowsight worksheet
#
# USAGE:
#   bash scripts/rebuild_snowflake.sh vycnywb-newaccountname
#
# If you don't pass the identifier as an argument, the script will ask
# for it interactively instead.

# "set -euo pipefail" — a standard safety habit for scripts:
#   -e : stop immediately if any command fails, instead of plowing on
#   -u : treat using an unset variable as an error, instead of silently
#        treating it as empty
#   -o pipefail : if any command in a pipeline fails, the whole pipeline
#        counts as failed (not just the last command in it)
set -euo pipefail

PROFILES_FILE="$HOME/.dbt/profiles.yml"

# Take the account identifier from the first argument, or ask for it.
# "${1:-}" means: use $1 if it was given, otherwise use an empty string
# (this avoids an error from "set -u" when no argument was passed).
NEW_ACCOUNT="${1:-}"

if [[ -z "$NEW_ACCOUNT" ]]; then
  read -rp "Enter the new Snowflake account identifier (e.g. orgname-accountname): " NEW_ACCOUNT
fi

if [[ -z "$NEW_ACCOUNT" ]]; then
  echo "No account identifier given. Aborting — nothing was changed."
  exit 1
fi

if [[ ! -f "$PROFILES_FILE" ]]; then
  echo "Error: $PROFILES_FILE doesn't exist yet."
  echo "Run the Step 10/14 setup first (see docs/PROJECT_SPEC.md) before using this script."
  exit 1
fi

echo "Updating account identifier in $PROFILES_FILE ..."

# sed -i '' means "edit this file in place" — the empty '' after -i is
# required on macOS specifically (GNU sed on Linux uses just -i with no
# argument; macOS's built-in sed is a different, older version that needs
# this extra empty string, or it misinterprets the next argument as a
# backup-file suffix instead).
#
# The pattern "s/account: .*/account: $NEW_ACCOUNT/" means:
#   s/   ... /   ...  /   = "substitute this pattern with this replacement"
#   account: .*          = matches the whole existing "account: ..." line
#   account: $NEW_ACCOUNT = replaces it with the new value
sed -i '' "s/account: .*/account: $NEW_ACCOUNT/" "$PROFILES_FILE"

echo "Done. New account line:"
grep "account:" "$PROFILES_FILE"

echo ""
echo "Now testing the connection with dbt debug ..."
echo ""

# Move into the dbt project directory relative to this script's location,
# so this works regardless of which directory you ran the script from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../aimsight_dbt"

dbt debug
