#!/usr/bin/env bash
# P4 Act C one-shot launcher (RD decision 2026-10-22). NOT part of the frozen protocol, probe or
# wrapper; it adds a single-execution gate in front of the frozen wrapper and changes nothing in it.
#
#   Launch (only after a separate, explicit RD authorization of Act C):
#     read -rs GITHUB_TOKEN && export GITHUB_TOKEN          # fine-grained PAT, public read-only, no permissions
#     P4_ACT_C_RD_AUTH="Act C one-shot approved f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d" \
#       bash p4/probe/act_c_once.sh
#   Status (read-only, any time):  bash p4/probe/act_c_once.sh --status
#
# Guarantees (for runs that go through this launcher):
#   * every read-only gate passes BEFORE anything is claimed; the one-shot marker is claimed with an
#     atomic mkdir BEFORE the wrapper (the only component that can make a live request) is started;
#   * any previous probe output, log, preserved copy, archive, checksum or marker -> STOP;
#   * the frozen wrapper is started at most once, detached (setsid nohup), with its PID, session and
#     console log recorded in the marker; the marker is never deleted or reset by this script;
#   * the token is taken only from GITHUB_TOKEN (fine-grained prefix required), is never printed or
#     written, and the census client therefore never falls back to `gh auth token`;
#   * the frozen request/time caps (200 requests, 4.5 h) are enforced by the unchanged probe.
# Limitation: the marker only binds runs that use this launcher. The frozen wrapper and probe can
# still be invoked directly by anyone who sets their documented authorization strings; see
# p4/P4_ACT_C_EXECUTION_RECORD.md section 3.
set -uo pipefail
umask 077
export GIT_PAGER=cat PAGER=cat GIT_TERMINAL_PROMPT=0

REPO=/mnt/e/Projects/OpenSourceLab/repos/Velith-research
HOME_EXPECT=/home/manish_raj
USER_EXPECT=manish_raj
ARCH=/mnt/e/Projects/OpenSourceLab/p4census-archive
WRAPPER="$REPO/p4/probe/run_live_probe.sh"
WRAPPER_SHA=904692c2474aefabdd8e0a73ad990d319920181b8d2817db4e733232effb428d
BCHECK=(python3 -I -B "$REPO/p4/probe/sizing_probe.py" baseline-check --baseline)
PROTO_COMMIT=f57c0c2b8eb38f5b5ed9b916793e2760fced1030
BLOCK=f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d
RD_AUTH_EXPECT="Act C one-shot approved $BLOCK"

P4C="$HOME_EXPECT/p4census"
BASE="$P4C/run1.preserved-20261016T063538Z"
RUN1="$P4C/run1"
MARKER="$P4C/ACT_C_PR2.once"
SELF_REL=p4/probe/act_c_once.sh
DOC_PATHS=(RESEARCH_STATUS.md p4/P4_ACT_C_EXECUTION_RECORD.md "$SELF_REL")
fail() { echo "STOP (nothing launched): $*"; exit 1; }
in_list() { local x="$1"; shift; local y; for y in "$@"; do [ "$x" = "$y" ] && return 0; done; return 1; }  # no pipes (pipefail-safe)
sha() { sha256sum "$1" | cut -d' ' -f1; }

# ---------------------------------------------------------------- read-only status mode
if [ "${1:-}" = "--status" ]; then
  echo "marker: $MARKER"
  if [ -d "$MARKER" ]; then
    for f in "$MARKER"/claim.txt "$MARKER"/launch.txt; do [ -f "$f" ] && { echo "--- $(basename "$f")"; cat "$f"; }; done
    pid="$(sed -n 's/^wrapper_pid=//p' "$MARKER/launch.txt" 2>/dev/null)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then echo "wrapper process $pid: RUNNING"; ps -o pid,pgid,sid,etime,cmd -p "$pid"
    elif [ -n "$pid" ]; then echo "wrapper process $pid: not running"; fi
    [ -f "$MARKER/wrapper_console.log" ] && { echo "--- last 25 console lines"; tail -n 25 "$MARKER/wrapper_console.log"; }
  else
    echo "no marker: Act C has not been launched through this launcher"
  fi
  echo "--- probe outputs"; ls -d "$P4C"/probe1-* "$ARCH"/p4probe1-* 2>/dev/null || echo "(none)"
  exit 0
fi
[ "$#" -eq 0 ] || fail "unexpected arguments: $*"

echo "================ Act C one-shot launcher: read-only gates ================"
# G1 environment and authorization
[ "$(id -u)" -ne 0 ] || fail "running as root"
[ "$(id -un)" = "$USER_EXPECT" ] || fail "unexpected user $(id -un)"
[ "${HOME:-}" = "$HOME_EXPECT" ] || fail "unexpected HOME"
[ "${P4_ACT_C_RD_AUTH:-}" = "$RD_AUTH_EXPECT" ] || fail "P4_ACT_C_RD_AUTH missing or wrong (explicit RD Act C authorization required)"
[ -z "${P4_PROBE_PR2+x}" ] || fail "P4_PROBE_PR2 must not be set in the caller's environment"
[ -z "${P4_PROBE_RD_AUTH+x}" ] || fail "P4_PROBE_RD_AUTH must not be preset; the launcher supplies it"
[ -n "${GITHUB_TOKEN:-}" ] || fail "GITHUB_TOKEN not supplied (no fallback to a gh credential)"
case "$GITHUB_TOKEN" in
  github_pat_*) ;;
  *) fail "GITHUB_TOKEN is not a fine-grained token (github_pat_ prefix required; value not shown)" ;;
esac
[[ "$GITHUB_TOKEN" =~ ^[A-Za-z0-9_]+$ ]] || fail "GITHUB_TOKEN has unexpected characters (value not shown)"
for t in git python3 sha256sum setsid nohup tar ps; do command -v "$t" >/dev/null || fail "missing tool: $t"; done
echo "G1 environment, RD authorization string, token presence/format, tools: PASS"

# G2 repository pin and working-tree state
cd "$REPO" || fail "cannot enter $REPO"
[ "$(git rev-parse --abbrev-ref HEAD)" = main ] || fail "branch is not main"
git merge-base --is-ancestor "$PROTO_COMMIT" HEAD || fail "HEAD does not contain the protocol commit $PROTO_COMMIT"
while IFS= read -r p; do
  [ -z "$p" ] && continue
  in_list "$p" "${DOC_PATHS[@]}" || fail "HEAD changes $p after $PROTO_COMMIT (only status documents and this launcher may differ)"
done < <(git diff --name-only "$PROTO_COMMIT" HEAD)
[ ! -e .git/index.lock ] || fail ".git/index.lock exists"
[ -z "$(git diff --cached --name-only)" ] || fail "staged changes present"
ALLOWED=(" M CI_113_GEE_SINGULARITY_DIAGNOSIS.md" " M stage0/logs_99522463703.zip")
for p in "${DOC_PATHS[@]}"; do ALLOWED+=("?? $p" " M $p"); done
while IFS= read -r line; do
  [ -z "$line" ] && continue
  in_list "$line" "${ALLOWED[@]}" || fail "unexpected working-tree entry: $line"
done < <(git status --porcelain)
sha256sum -c --quiet - <<'SUMS' || fail "unrelated modified files changed"
94ab886f6a838c77f84d0f882d91fd189b206b4a23ceede74e6461df66868136  CI_113_GEE_SINGULARITY_DIAGNOSIS.md
7fa52fb139e9a00b3ae3b95a954a1328d2b1389ec6d62ae08c73e5f0e497f74f  stage0/logs_99522463703.zip
SUMS
echo "G2 HEAD contains $PROTO_COMMIT, later changes limited to status documents/launcher; working tree as expected: PASS"

# G3 frozen artifacts and probe identity
git diff --quiet "$PROTO_COMMIT" -- p4 ':(exclude)p4/P4_ACT_C_EXECUTION_RECORD.md' ":(exclude)$SELF_REL" \
  || fail "p4/ differs from the protocol commit"
sha256sum -c --quiet - <<'SUMS' || fail "frozen artifact hash mismatch"
2c4acbcc0fc7bade265475abe1b5db9821bff1b7efd935fa20acd98b008f2494  p4/probe/sizing_probe.py
e9c97275c262b55cfb6f8d92ee49485c5aa7e8ac29e09c64fa797613ce3f3f08  p4/probe/test_sizing_probe.py
a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4  p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md
23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d  p4/census/supply_census.py
68b6f301a943c6d73027a0dad410be74cacd30df2db9500a4c0fca1690c23050  p4/P4_SIZING_PROBE_FREEZE_RECORD_ACT_A.md
SUMS
[ "$(sha "$WRAPPER")" = "$WRAPPER_SHA" ] || fail "wrapper hash mismatch"
ID="$(cd /tmp && env -u P4_PROBE_PR2 python3 -I -B "$REPO/p4/probe/sizing_probe.py" identity 2>&1)"
[ "$ID" = "protocol_block_sha $BLOCK"$'\n'"census_code_ok True"$'\n'"frozen_protocol_sha $BLOCK" ] || fail "probe identity check failed"
echo "G3 frozen hashes (probe, tests, protocol, census, Act-A record, wrapper) and identity: PASS"

# G4 baseline integrity, protected paths, archive, no previous run
[ -d "$BASE/cache" ] || fail "baseline copy missing: $BASE"
[ ! -w "$BASE" ] || fail "baseline copy is writable"
[ -s "$BASE/MANIFEST.sha256" ] && (cd "$BASE" && sha256sum --quiet -c MANIFEST.sha256 >/dev/null 2>&1) || fail "baseline manifest missing or does not verify"
env -u GITHUB_TOKEN -u P4_PROBE_PR2 "${BCHECK[@]}" "$BASE" >/dev/null 2>&1 || fail "baseline-check failed"
[ -d "$RUN1" ] || fail "protected root missing: $RUN1"
[ -d "$ARCH" ] && [ -w "$ARCH" ] || fail "archive directory missing or not writable: $ARCH"
[ -d "$P4C" ] && [ -w "$P4C" ] || fail "$P4C missing or not writable"
rp() { python3 -I -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"; }
inside() { case "$1/" in "$2"/*) return 0 ;; *) return 1 ;; esac; }
for root in "$BASE" "$RUN1" "$ARCH"; do
  inside "$(rp "$P4C")" "$(rp "$root")" && fail "output root $P4C lies inside protected root $root"
done
for root in "$BASE" "$RUN1"; do inside "$(rp "$ARCH")" "$(rp "$root")" && fail "archive lies inside protected root $root"; done
prior() { ls -d "$P4C"/probe1-* "$ARCH"/p4probe1-* 2>/dev/null; }
[ -z "$(prior)" ] || { prior; fail "a previous probe output/log/copy/archive/checksum exists"; }
[ ! -e "$MARKER" ] || fail "one-shot marker already exists ($MARKER): any retry needs a new RD decision"
echo "G4 baseline (exists, manifest, baseline-check, read-only), protected paths, archive, no previous run: PASS"

# ---------------------------------------------------------------- claim (atomic) and launch once
mkdir "$MARKER" 2>/dev/null || fail "one-shot marker could not be claimed (already claimed by another attempt)"
SELF_SHA="$(sha "$REPO/$SELF_REL" 2>/dev/null || sha "$0")"
{
  echo "claimed_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "launcher_sha256=$SELF_SHA"
  echo "head=$(git rev-parse HEAD)"
  echo "protocol_commit=$PROTO_COMMIT"
  echo "wrapper=$WRAPPER"
  echo "wrapper_sha256=$WRAPPER_SHA"
  echo "protocol_block=$BLOCK"
  echo "user=$(id -un) host=$(uname -n) launcher_pid=$$"
  echo "token=supplied via GITHUB_TOKEN (fine-grained prefix); value not recorded"
  echo "note=this marker is never removed by the launcher; any retry requires a new RD decision"
} > "$MARKER/claim.txt"
[ -z "$(prior)" ] || fail "a probe output appeared after the claim; marker kept, wrapper NOT started"
echo "one-shot marker claimed: $MARKER"

setsid nohup env -u P4_PROBE_PR2 P4_PROBE_RD_AUTH="PR-2 approved $BLOCK" bash "$WRAPPER" \
  > "$MARKER/wrapper_console.log" 2>&1 < /dev/null &
WPID=$!
sleep 1
{
  echo "launched_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "wrapper_pid=$WPID"
  echo "console_log=$MARKER/wrapper_console.log"
  ps -o pid=,pgid=,sid=,lstart=,cmd= -p "$WPID" 2>/dev/null | sed 's/^/process=/' || echo "process=exited within 1 s (see console log)"
} > "$MARKER/launch.txt"
chmod 0400 "$MARKER/claim.txt" "$MARKER/launch.txt"
chmod 0500 "$MARKER"
echo "WRAPPER STARTED ONCE: pid $WPID (own session); console log $MARKER/wrapper_console.log"
echo "Follow:  tail -f '$MARKER/wrapper_console.log'      Status:  bash $REPO/$SELF_REL --status"
echo "The wrapper writes its own log ~/p4census/probe1-<STAMP>.log, evidence, read-only copy and archive."
