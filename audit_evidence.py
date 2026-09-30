"""READ-ONLY audit of M2 prototype evidence. Opens files for reading only; writes nothing."""

import hashlib
import json
import os
import sys
from pathlib import Path
from xml.etree import ElementTree

R = Path(os.path.expanduser(sys.argv[1]))
S = Path(os.path.expanduser(sys.argv[2]))
PROBE = Path(sys.argv[3])
HEAD, BASE = "966bb873e3a1e42d857362a17f5af2533dfd8f46", "7ee9ceb71e868944a46e1ff00b506772a53a4f1d"
DIGEST = "sha256:eaf597005c159361cb8ee26018fb3741b320f331065f0c95726d83ccf2f1fba4"
VELITH = "e04d7f90a742a3c6278a2fd937803abdd1567ac8"
fails = []


def check(label, ok, info=""):
    print(f"  [{'OK ' if ok else 'BAD'}] {label}" + (f"  ({info})" if info else ""))
    if not ok:
        fails.append(label)


spec = json.loads(S.read_text())
f2p, p2p = spec["fail_to_pass"], spec["pass_to_pass"]
req = [*f2p, *p2p]
probe_sha = hashlib.sha256(PROBE.read_bytes()).hexdigest()
print(f"spec: {len(f2p)} F2P + {len(p2p)} P2P, sha256={hashlib.sha256(S.read_bytes()).hexdigest()}")
print(f"spec protected={spec['protected_paths']} test_files={spec['test_files']}")
check("required ids unique", len(set(req)) == len(req))
check("all required ids in test_files", all(t.split("::")[0] in spec["test_files"] for t in req))
print(f"probe on disk sha256={probe_sha}")
print(f"run dirs: {sorted(p.name for p in R.iterdir())}")

ev = {}
for name in ("A", "B", "C", "D", "D0", "E", "F1", "F2"):
    ev[name] = json.loads((R / name / "evidence.json").read_text())
    print(f"  files in {name}: {sorted(str(p.relative_to(R / name)) for p in (R / name).rglob('*') if p.is_file())}")


def counts(outcomes):
    out = {}
    for v in (outcomes or {}).values():
        out[v] = out.get(v, 0) + 1
    return out


def not_passed(outcomes):
    return sorted(k for k, v in (outcomes or {}).items() if v != "passed")


for name, e in ev.items():
    d = e["deterministic"]
    print(f"\n== {name}: {d['classification']} / {d['reason']} / {d['detail']}")
    check("digest pinned", d["digest"] == DIGEST)
    check("velith commit", d["velith_commit"] == VELITH, d["velith_commit"][:10])
    check("probe sha matches file on disk", d["probe_sha256"] == probe_sha)
    check("deterministic env", d["deterministic_env"] == {"PYTHONHASHSEED": "0", "TZ": "UTC", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"})
    for role in ("baseline", "candidate"):
        r = d[role]
        diag = e["diagnostics"][role] or {}
        print(f"  {role}: status={r['status']} exit={r.get('exit_code')} oom={r.get('oom_killed')} "
              f"net={r.get('network_mode')}/{r.get('net_probe')} pytest_exit={r.get('pytest_exit')} "
              f"mapped={r.get('mapped_required')} coll_fail={r.get('collection_failures')} "
              f"removed={r.get('removed')} tampered={r.get('tampered')} counts={counts(r.get('outcomes'))} "
              f"dur={diag.get('duration_seconds')}")
        check(f"{role} image HEAD/parent", r.get("head") == HEAD and r.get("parent") == BASE)
        check(f"{role} network none + blocked", r.get("network_mode") == "none" and str(r.get("net_probe", "")).startswith("blocked"))
        check(f"{role} not OOM", r.get("oom_killed") is False)
    b, c = d["baseline"], d["candidate"]
    if name != "C":
        check("baseline healthy: all P2P passed", all(b["outcomes"][t] == "passed" for t in p2p))
        check("baseline: F2P failed (present, not missing)", all(b["outcomes"][t] in ("failed", "error") for t in f2p), str([b["outcomes"][t] for t in f2p]))
        check("baseline: all required mapped", b["mapped_required"] == len(req))
        check("baseline: removed nothing", b["removed"] == [])
        check("candidate: all required mapped", c["mapped_required"] == len(req))
        check("baseline surface == candidate surface", b["surface"] == c["surface"])
        print(f"  candidate not-passed: {not_passed(c['outcomes'])}")

a = ev["A"]["deterministic"]
print("\n== cross-case")
check("A candidate removed nothing (sealed env untouched)", a["candidate"]["removed"] == [])
for n in ("D", "D0"):
    cd = ev[n]["deterministic"]["candidate"]
    check(f"{n} tamper happened", cd["tampered"] is True)
    check(f"{n} untracked configs removed", cd["removed"] == ["conftest.py", "pytest.ini"], str(cd["removed"]))
    check(f"{n} protected surface == A", cd["surface"] == a["candidate"]["surface"])
check("D outcomes == A outcomes", ev["D"]["deterministic"]["candidate"]["outcomes"] == a["candidate"]["outcomes"])
check("B fails exactly F2P", not_passed(ev["B"]["deterministic"]["candidate"]["outcomes"]) == sorted(f2p))
check("D0 fails exactly F2P", not_passed(ev["D0"]["deterministic"]["candidate"]["outcomes"]) == sorted(f2p))
check("D0 candidate outcomes == baseline outcomes", ev["D0"]["deterministic"]["candidate"]["outcomes"] == ev["D0"]["deterministic"]["baseline"]["outcomes"])
check("B candidate patch != gold", ev["B"]["deterministic"]["candidate_patch_sha256"] != a["candidate_patch_sha256"])
check("D0 candidate patch empty", ev["D0"]["deterministic"]["candidate_patch_sha256"] == hashlib.sha256(b"").hexdigest())
cc = ev["C"]["deterministic"]
check("C fault_cmd recorded", bool(cc["fault_cmd"]), cc["fault_cmd"])
for role in ("baseline", "candidate"):
    out = (R / "C" / role / "stdout.txt").read_text(errors="replace")
    hit = [ln.strip() for ln in out.splitlines() if "werkzeug" in ln.lower() or "Error" in ln][:4]
    print(f"  C {role} stdout evidence: {hit}")
    check(f"C {role} junit absent", not (R / "C" / role / "junit.xml").exists())
for n in ("A", "F1", "F2"):
    junit = R / n / "baseline" / "junit.xml"
    root = ElementTree.parse(junit).getroot()
    collected = {(t.get("classname"), t.get("name")) for t in root.iter("testcase")}
    print(f"  {n} baseline junit testcases collected={len(collected)}")
root = ElementTree.parse(R / "A" / "baseline" / "junit.xml").getroot()
names = sorted(f"{t.get('classname')}::{t.get('name')}" for t in root.iter("testcase"))
req_keys = {f"tests.test_blueprints::{t.split('::', 1)[1]}" for t in req}
print(f"  collected-but-not-required (excluded by dataset): {[n for n in names if n not in req_keys]}")
check("every required id collected in A baseline", req_keys <= set(names))


def strip(dd):
    return {k: v for k, v in dd.items() if k != "case"}


for x, y in (("A", "F1"), ("A", "F2"), ("F1", "F2"), ("A", "E")):
    diff = sorted(k for k in strip(ev[x]["deterministic"]).keys() | strip(ev[y]["deterministic"]).keys()
                  if strip(ev[x]["deterministic"]).get(k) != strip(ev[y]["deterministic"]).get(k))
    check(f"determinism {x} vs {y} (excluding case label)", not diff, str(diff))

print(f"\nRESULT: {'ALL CHECKS OK' if not fails else 'FAILURES: ' + str(fails)}")
