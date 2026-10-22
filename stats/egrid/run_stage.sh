#!/usr/bin/env bash
# EPG-14 M-H0 host wrapper: run exactly ONE stage per invocation in the pinned image.
#
# M-H0 scope: synthetic SYN-* stages only. V0-V5 are NOT authorized and are refused.
#
#   stats/egrid/run_stage.sh SYN-<NAME> [--run-id ID] [--test-memory BYTES]
#                                        [--test-no-proc-check] [--env-lock PATH]
#
# Flow: pinned image check (env.lock image_id == local image Id) -> docker create (named, no --rm)
# -> inspect + verify isolation/limits BEFORE start -> start -> host monitor (aggregate cgroup CPU,
# process count, wall clock; SIGKILL on violation) -> wait -> inspect final state (ExitCode,
# OOMKilled) -> logs -> wrapper_status.json -> docker rm -> classify -> stage_outcome.json.
#
# Layout: runs/<run_id>/<stage>/stage/   (mounted rw into the container at /out; driver output)
#         runs/<run_id>/<stage>/wrapper/ (host only; the stage cannot write here)
#         runs/<run_id>/<stage>/outcome/stage_outcome.json
# Exit: 0 only if the classified outcome is PASS; 1 otherwise; 2 usage/refusal.
set -euo pipefail
umask 022

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
die() { echo "run_stage: $2" >&2; exit "$1"; }

STAGE="${1:-}"
[[ -n "$STAGE" ]] || die 2 "usage: run_stage.sh SYN-<NAME> [--run-id ID] [--test-memory BYTES] [--test-no-proc-check] [--env-lock PATH]"
shift
[[ "$STAGE" =~ ^SYN-[A-Z0-9-]+$ ]] || die 2 "refused: only synthetic SYN-* stages are permitted in M-H0; V0-V5 are not authorized"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ENV_LOCK="$ROOT/env/out/env.lock"
MEM_DEFAULT=2147483648
MEM="$MEM_DEFAULT"
PROC_CHECK=on
declare -a TS=()   # non-default test settings (recorded; SYN-* only)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="${2:?}"; shift 2 ;;
    --test-memory) MEM="${2:?}"; [[ "$MEM" =~ ^[0-9]+$ ]] || die 2 "--test-memory needs bytes"; TS+=("\"memory\":$MEM"); shift 2 ;;
    --test-no-proc-check) PROC_CHECK=off; TS+=("\"proc_check\":\"off\""); shift ;;
    --env-lock) ENV_LOCK="${2:?}"; TS+=("\"env_lock\":\"$(basename "$2")\""); shift 2 ;;
    *) die 2 "unknown option $1" ;;
  esac
done
[[ "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]] || die 2 "invalid run id"
TEST_SETTINGS="{$(IFS=,; echo "${TS[*]:-}")}"

# Fixed M-H0 synthetic-stage parameters (documented in M_H0_HARNESS.md).
CAP_S=5            # aggregate CPU budget = per-process RLIMIT_CPU (soft = hard)
RESERVE_S=1        # driver in-process stop at CAP_S - RESERVE_S
CHECK_S=0.05       # driver ITIMER_PROF interval (process CPU seconds)
POLL_S=0.25        # host monitor poll interval (wall seconds)
WALL_S=60          # host wall-clock limit (no contract STOP; classified UNCLASSIFIED)
LIMITS="{\"cap_s\":$CAP_S,\"reserve_s\":$RESERVE_S,\"check_interval_s\":$CHECK_S,\"poll_s\":$POLL_S,\"wall_s\":$WALL_S,\"memory\":$MEM}"

BASE="$ROOT/runs/$RUN_ID/$STAGE"
[[ ! -e "$BASE" ]] || die 2 "refused: $BASE already exists"
mkdir -p "$BASE/stage" "$BASE/wrapper" "$BASE/outcome"
W="$BASE/wrapper"
command -v docker >/dev/null || die 2 "docker not found"
command -v python3 >/dev/null || die 2 "python3 not found on host"
python3 -I -c 'import sys; sys.exit(sys.version_info < (3, 8))' || die 2 "host python3 >= 3.8 required"
HM=(python3 -I "$ROOT/hostmon.py")

finalize() {  # finalize <preflight_problems_json> [extra finalize args...]
  local pp="$1"; shift
  "${HM[@]}" finalize --stage "$STAGE" --run-id "$RUN_ID" --image-id "${LOCK_ID:-unknown}" \
    --code-root "$ROOT" --out "$W/wrapper_status.json" --preflight-problems "$pp" \
    --limits "$LIMITS" --test-settings "$TEST_SETTINGS" "$@"
}
classify_and_exit() {
  "${HM[@]}" classify --wrapper "$W/wrapper_status.json" --stage-dir "$BASE/stage" \
    --out "$BASE/outcome/stage_outcome.json"
  local outcome
  outcome="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["outcome"])' \
    "$BASE/outcome/stage_outcome.json" 2>/dev/null || true)"
  echo "run_stage: $STAGE -> ${outcome:-NO_OUTCOME} ($BASE/outcome/stage_outcome.json)"
  [[ "$outcome" == "PASS" ]] && exit 0 || exit 1
}
preflight_fail() {
  echo "run_stage: preflight failed: $1" >&2
  local -a extra=()
  [[ -n "${2:-}" ]] && extra=(--config-check "$2")
  finalize "[\"$1\"]" "${extra[@]}"
  classify_and_exit
}

# 1. Pinned image identity.
LOCK_ID="$(sed -n 's/^image_id=//p' "$ENV_LOCK" 2>/dev/null | head -1 || true)"
[[ "$LOCK_ID" =~ ^sha256:[0-9a-f]{64}$ ]] || preflight_fail "env.lock image_id missing or malformed"
LOCAL_ID="$(docker image inspect --format '{{.Id}}' "$LOCK_ID" 2>/dev/null || true)"
[[ "$LOCAL_ID" == "$LOCK_ID" ]] || preflight_fail "pinned image $LOCK_ID not present locally or Id mismatch"

# 2. Create (not start) the named container with the fixed isolation and limits.
NAME="egrid-$(printf '%s' "$RUN_ID-$STAGE" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9-' '-')"
CID="$(docker create --name "$NAME" \
  --network none --cpus=1 --memory="$MEM" --memory-swap="$MEM" --pids-limit=64 \
  --read-only --tmpfs /tmp:rw,size=64m --cap-drop=ALL --security-opt=no-new-privileges \
  --user 1000:1000 --ulimit cpu="$CAP_S:$CAP_S" -w /egrid \
  -v "$ROOT:/egrid:ro" -v "$BASE/stage:/out" \
  "$LOCK_ID" python -m harness_tests.synth "$STAGE" --run-id "$RUN_ID" --out /out \
  --cap-s "$CAP_S" --reserve-s "$RESERVE_S" --check-interval-s "$CHECK_S" --memory-max "$MEM")"
echo "$CID" > "$W/container_id"
docker inspect "$CID" > "$W/inspect_created.json"
if ! "${HM[@]}" verify-config --inspect "$W/inspect_created.json" --image-id "$LOCK_ID" \
     --cap-s "$CAP_S" --memory "$MEM" --code-root "$ROOT" --stage-dir "$BASE/stage" \
     --out "$W/config_check.json"; then
  docker rm "$CID" >/dev/null
  preflight_fail "container configuration does not match the required isolation/limits" "$W/config_check.json"
fi

# 3. Start, monitor, wait. An interrupted wrapper kills the container and leaves no outcome.
trap 'docker kill "$CID" >/dev/null 2>&1 || true; echo ABORTED > "$W/ABORTED"; echo "run_stage: aborted; container $NAME kept for inspection" >&2; exit 130' INT TERM
docker start "$CID" >/dev/null
MON_RC=0
"${HM[@]}" monitor --container "$CID" --cap-s "$CAP_S" --poll-s "$POLL_S" --wall-s "$WALL_S" \
  --proc-check "$PROC_CHECK" --out "$W/monitor.json" || MON_RC=$?
# The monitor returns only after the container exited or after it decided to kill it. Kill again
# via the CLI unconditionally (harmless if already exited) so a failed API kill or a monitor crash
# can never leave an unmonitored stage running.
docker kill "$CID" >/dev/null 2>&1 || true
docker wait "$CID" > "$W/docker_wait_exit_code"
docker inspect "$CID" > "$W/inspect_final.json"
docker logs "$CID" > "$W/stdout.txt" 2> "$W/stderr.txt" || true
finalize "[]" --config-check "$W/config_check.json" --monitor "$W/monitor.json" \
  --monitor-exit-code "$MON_RC" --final-inspect "$W/inspect_final.json"
docker rm "$CID" >/dev/null && echo removed > "$W/container_removed"
trap - INT TERM

# 4. Classify from explicit wrapper and stage records.
classify_and_exit
