#!/usr/bin/env bash
# P1 Stage-0/1 admission for T2..T5 (one task at a time, stops at the first failure).
# Per task: space gate -> pull by pinned linux/amd64 digest -> identity check -> OD-5 spec via the
# frozen probe -> Case A (gold patch) -> evidence manifest. Nothing in Velith main is modified;
# no existing image/container/volume/network is touched. Run from WSL:
#   bash /mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env/p1_admit.sh [T2 T3 T4 T5]
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R="$HERE/results"
PROBE=/mnt/e/Projects/OpenSourceLab/repos/Velith/experiments/m2_container_prototype/probe.py
EXPECT_PROBE=560834d559fbf1063c7ad33afa675abac59535e45469bc0d9da3e8254f138e1f

# id | instance | image repo | pinned amd64 digest | compressed bytes | Case-A timeout (OD-7)
TASKS="
T2|matplotlib__matplotlib-24570|swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-24570|sha256:5d93272292526ed727fdbf8fcad24e751965c5d62d66f91c64be7119339b323c|3137932335|900
T3|scikit-learn__scikit-learn-14629|swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14629|sha256:de0579911863656a0331adc8d2dd6080ccc2543d0a5fd2bd68d753c8df1ec7c8|1495941692|900
T4|astropy__astropy-7336|swebench/sweb.eval.x86_64.astropy_1776_astropy-7336|sha256:481ebd12ef496853db01765b1dd57d9aebdedd056c22656b9f483fc1c8379da9|1113006597|900
T5|pydata__xarray-6721|swebench/sweb.eval.x86_64.pydata_1776_xarray-6721|sha256:58c7f4ada7f3cbcfcde50e0b55157701100cf694faa87978c672e368c0531898|1925618712|1800
"
[ -f "$HERE/p1_extra_tasks.txt" ] && TASKS="$TASKS$(cat "$HERE/p1_extra_tasks.txt")
"   # OD-6 replacements (p1_lottery.py)
stop() { echo "STOP [$1]: $2"; exit 1; }

[ "$(sha256sum "$PROBE" | cut -d' ' -f1)" = "$EXPECT_PROBE" ] || stop all "probe hash mismatch"
WANT="${*:-T2 T3 T4 T5}"

for id in $WANT; do
  line="$(echo "$TASKS" | grep "^$id|")" || stop "$id" "unknown task id"
  IFS='|' read -r tid inst img dig bytes tmo <<<"$line"
  ref="$img@$dig"; out="$R/admission-$tid"; mkdir -p "$out"
  echo "================ $tid  $inst"

  need=$(python3 -c "print(int(2.5*$bytes+10_000_000_000))")
  avail=$(df -B1 --output=avail /mnt/c | tail -1)
  echo "space: C: free $avail, need $need" | tee "$out/00_space.txt"
  [ "$avail" -ge "$need" ] || stop "$tid" "insufficient C: space"

  docker pull --platform linux/amd64 "$ref" >"$out/01_pull.txt" 2>&1 || stop "$tid" "pull failed (see 01_pull.txt)"
  docker image inspect "$ref" --format '{{json .RepoDigests}}|{{.Os}}/{{.Architecture}}|{{.Id}}' | tee "$out/02_inspect.txt"
  grep -q "$ref" "$out/02_inspect.txt" && grep -q '|linux/amd64|' "$out/02_inspect.txt" || stop "$tid" "identity mismatch"
  echo "identity: PASS"

  spec="$out/$tid.spec.json"
  if [ ! -f "$spec" ]; then
    python3 "$HERE/p1_spec.py" "$inst" "$img" "$dig" "$spec" 2>&1 | tee "$out/03_spec.txt"
    [ -f "$spec" ] || stop "$tid" "spec not created (see 03_spec.txt)"
  fi

  python3 "$PROBE" run --spec "$spec" --case A --out-dir "$out" --run-label A --timeout "$tmo" 2>&1 | tee "$out/04_caseA.txt"
  grep -q '"classification": "PASSED"' "$out/04_caseA.txt" || stop "$tid" "Case A not PASSED: inadmissible -> OD-6 replacement decision (see 04_caseA.txt)"

  df -B1 --output=avail /mnt/c | tail -1 >"$out/05_c_free_after.txt"
  (cd "$out" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256)
  echo "ADMITTED $tid: $(grep -o '"detail": "[^"]*"' "$out/04_caseA.txt")  manifest $(sha256sum "$out/MANIFEST.sha256" | cut -c1-16)"
done
echo "ALL REQUESTED TASKS ADMITTED: $WANT"
