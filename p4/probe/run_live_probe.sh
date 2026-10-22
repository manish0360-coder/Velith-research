#!/usr/bin/env bash
# P4 sizing probe: live-run evidence wrapper. PR-2 ONLY. DO NOT RUN without a recorded RD freeze of
# protocol block f8a7e398... AND an explicit RD execution authorization.
# Network: GitHub `GET /search/repositories` only, via the probe (<= 200 requests, <= 4.5 h).
# Writes ONLY: $OUT (created by the probe), $OUT.preserved, $LOG, $TAR, $TAR.sha256 (all new; no overwrite).
# Reads only: the baseline copy, the frozen census code, the protocol document, the probe code.
set -euo pipefail

R=/mnt/e/Projects/OpenSourceLab/repos/Velith-research
PROBE="$R/p4/probe/sizing_probe.py"
PROTO="$R/p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md"
CENSUS="$R/p4/census/supply_census.py"
BASE=/home/manish_raj/p4census/run1.preserved-20261016T063538Z
ARCH=/mnt/e/Projects/OpenSourceLab/p4census-archive

EXP_BLOCK=f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d
EXP_DOC=a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4
EXP_CENSUS=23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d
EXP_PROBE_POST=2c4acbcc0fc7bade265475abe1b5db9821bff1b7efd935fa20acd98b008f2494  # after the one-line PR-2 edit

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/p4census/probe1-$STAMP"
LOG="$HOME/p4census/probe1-$STAMP.log"
COPY="$OUT.preserved"
TAR="$ARCH/p4probe1-$STAMP.tar.gz"
stop() { echo "STOP: $*"; exit 1; }

echo "== 0. authorization and environment"
[ "$(id -u)" -ne 0 ] || stop "running as root"
[ "$HOME" = /home/manish_raj ] || stop "unexpected HOME: $HOME"
[ "${P4_PROBE_RD_AUTH:-}" = "PR-2 approved $EXP_BLOCK" ] || stop "RD authorization string not set"
for p in "$OUT" "$LOG" "$COPY" "$TAR" "$TAR.sha256"; do [ ! -e "$p" ] || stop "already exists: $p"; done
[ -d "$ARCH" ] || stop "archive directory missing: $ARCH"
[ -d "$BASE/cache" ] || stop "baseline copy missing: $BASE"
[ ! -w "$BASE" ] || stop "baseline copy is writable (expected read-only)"
(cd "$BASE" && sha256sum --quiet -c MANIFEST.sha256) || stop "baseline copy fails its manifest"
echo "BASELINE_COPY_VERIFIES"

echo "== 1. frozen identities"
chk() { local g; g="$(sha256sum "$1" | cut -d' ' -f1)"; echo "$g  $1"; [ "$g" = "$2" ] || stop "hash mismatch: $1"; }
chk "$CENSUS" "$EXP_CENSUS"
chk "$PROTO" "$EXP_DOC"
chk "$PROBE" "$EXP_PROBE_POST"
ID="$(cd /tmp && PYTHONDONTWRITEBYTECODE=1 python3 -B "$PROBE" identity)"
echo "$ID"
grep -qx "protocol_block_sha $EXP_BLOCK" <<<"$ID" || stop "protocol block SHA mismatch"
grep -qx "frozen_protocol_sha $EXP_BLOCK" <<<"$ID" || stop "probe is not frozen to the approved block"
grep -qx "census_code_ok True" <<<"$ID" || stop "census code changed"
[ -n "${GITHUB_TOKEN:-}" ] || gh auth status >/dev/null 2>&1 || stop "no GitHub credential (never printed)"
echo "IDENTITIES_OK"

echo "== 2. LIVE PROBE (GitHub search only)"
set +e
(cd /tmp && P4_PROBE_PR2=AUTHORIZED PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$PROBE" run --out "$OUT" --baseline "$BASE") 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}
set -e
echo "probe_exit_code $RC"
[ -d "$OUT" ] || stop "probe created no evidence directory (refused before writing); see $LOG"

echo "== 3. evidence integrity (partial evidence is preserved too)"
if [ -f "$OUT/MANIFEST.sha256" ]; then
  if (cd "$OUT" && sha256sum --quiet -c MANIFEST.sha256); then echo "EVIDENCE_MANIFEST_OK"
  else echo "EVIDENCE_MANIFEST_MISMATCH (preserving as-is; report to RD)"; fi
else
  echo "NO_MANIFEST (probe did not finish normally; preserving as-is; report to RD)"
fi

echo "== 4. read-only copy + archive"
cp -a "$OUT" "$COPY"
diff -r "$OUT" "$COPY" >/dev/null || stop "copy differs from evidence"
chmod -R a-w "$OUT" "$COPY"
chmod a-w "$LOG"
tar -C "$HOME/p4census" -czf "$TAR" "probe1-$STAMP" "probe1-$STAMP.log"
(cd "$ARCH" && sha256sum "$(basename "$TAR")" > "$(basename "$TAR").sha256" \
  && sha256sum -c "$(basename "$TAR").sha256")
(cd "$BASE" && sha256sum --quiet -c MANIFEST.sha256) && echo "BASELINE_STILL_VERIFIES"

echo "== 5. summary (send the whole output and $LOG to the CSE)"
if [ -f "$OUT/probe_result.json" ]; then
  python3 -B -c 'import json,sys; r=json.load(open(sys.argv[1]));
print("OUTCOME", r.get("outcome"), "| M_v", r.get("M_v"), "| M_v_lower_bound", r.get("M_v_lower_bound"),
      "| decision", r.get("decision"), "| requests", r.get("calls"), "| reason", r.get("reason"))' \
    "$OUT/probe_result.json"
fi
echo "WRAPPER_DONE out=$OUT copy=$COPY archive=$TAR log=$LOG exit=$RC"
