#!/usr/bin/env bash
# EPG-14 M-H0 acceptance on the target venue (WSL + Docker). Synthetic stages only; no V0-V5.
#
#   bash stats/egrid/harness_tests/run_mh0_acceptance.sh [RUN_ID]
#
# Runs every synthetic case through run_stage.sh (one stage per invocation), then evaluates the
# records with acceptance.py. Individual cases are EXPECTED to FAIL; the verdict is whether each
# failure is classified exactly as required. Outputs: stats/egrid/runs/<RUN_ID>[...] (gitignored).
set -uo pipefail
EG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
RUN_ID="${1:-mh0-$(date -u +%Y%m%dT%H%M%SZ)}"
RS="$EG/run_stage.sh"

run() {
  local stage="$1"; shift
  echo ">>> $stage $*"
  bash "$RS" "$stage" --run-id "$RUN_ID" "$@"
  echo "    run_stage exit $?"
}

run SYN-PASS
run SYN-TESTS
run SYN-TESTS-SKIP
run SYN-BURN-INPROC
run SYN-RAW-BURN2 --test-no-proc-check
run SYN-RAW-BURN
run SYN-CHILD
run SYN-RAW-CHILD
run SYN-RAISE
run SYN-RAW-EXIT3
run SYN-OOM --test-memory 268435456
run SYN-ASLIMIT
run SYN-RAW-FORGE-KILLED
run SYN-RAW-FORGE-PARTIAL
run SYN-RAW-FORGE-MISMATCH

# Image-identity negative case: a temporary lock naming an absent image (env/out/env.lock untouched).
FAKE_LOCK="$(mktemp)"
printf 'image_id=sha256:%064d\n' 0 > "$FAKE_LOCK"
echo ">>> SYN-PASS --env-lock <absent image>"
bash "$RS" SYN-PASS --run-id "$RUN_ID-imgneg" --env-lock "$FAKE_LOCK"
echo "    run_stage exit $?"
rm -f "$FAKE_LOCK"

echo
python3 -I "$EG/harness_tests/acceptance.py" "$EG/runs" "$RUN_ID"
