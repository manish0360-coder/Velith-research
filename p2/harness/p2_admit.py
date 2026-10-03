#!/usr/bin/env python3
"""P2 FG-4 Phase-A admission machinery (P2_SPEC.md §9, §10, §12, §13, §14; FG-4).

Walks the frozen FG-3 order (54 candidates) with the frozen `p2_lottery.walk`:
- at most 4 admitted per repository;
- continue past an inadmissible candidate;
- no backfill;
- target 20 (the observed ceiling is 16).

Each candidate goes through the frozen admission steps:
1. identity — resolve the digest, pass the storage gate, pull by digest (one retry), check identity;
2. spec_built — the OD-5 spec via the frozen P1 `p1_spec.py`;
3. case_a_passed — Case A (gold) through the frozen probe;
4. h_base_equals_worktree — gold blobs at base equal the working-tree files (G-8);
5. f_budget_and_audit — U and S prompts within B_PROMPT, both leakage audits PASS.

The G-10 self-check is DIAGNOSTIC ONLY. It runs after the admission decision is fixed and
recorded, and only for admitted tasks.

The image is deleted only after its provenance has been written (D7). A storage-gate failure,
a dataset-row drift and an A-1 alarm are pilot-level STOPs, never inadmissibility and never a
substitution.

All Docker, probe and model access goes through `Ops`. Tests use a fake. Nothing here
generates text, and there is no third arm and no PILOT_SET.

Usage (WSL; FG-4 execution requires separate RD authorization):
    python3 -B p2/harness/p2_admit.py run
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_edits as E  # noqa: E402
import p2_harness as H  # noqa: E402
import p2_lottery as L  # noqa: E402

EVIDENCE = H.RESEARCH / "p2" / "evidence"
LOTTERY = EVIDENCE / "_lottery"
ADMISSION = EVIDENCE / "_admission"
ADMISSION_LOG = LOTTERY / "admission_log.json"
FG3_SHA256 = {"pool.json": "8c870348ed2a4d0a127c135701095cafd7db76b63e00ac6c20a0ca86fd2ed001",
              "order.json": "d9199f2c9c474f354c21535d699733081a69bc58e1c131219c1c8b5cd4710708",
              "MANIFEST.sha256": "de977b69e487f8c9423e108d521a48a96933740bc1386f346594ac1a9655a098"}
P1_SPEC_SCRIPT = H.RESEARCH / "stage0" / "p1env" / "p1_spec.py"
P1_SPEC_SHA256 = "1fe25a95a1731ae446f2592689080abdbac6cb97e6782bd86afd25a0ff3bf0b1"
PLATFORM = "linux/amd64"
REPO_DIR = "/testbed"
ADMISSION_CASE_A_TIMEOUT = 1800.0  # SRC ruling + RD 2026-10-03 (p2/FG4_GOVERNANCE_RECORD.md)
TIMEOUT_THRESHOLD_S, TIMEOUT_SHORT, TIMEOUT_LONG = 300.0, 900.0, 1800.0  # G-4
B_PROMPT = 15232


class AdmissionStop(Exception):
    """Pilot-level stop (§17): storage gate, data drift, harness integrity (A-1). Not a task
    outcome; it never causes inadmissibility or substitution."""


@dataclass(frozen=True)
class Candidate:
    rank: int
    instance_id: str
    repo: str
    row_sha256: str


class Ops(Protocol):
    def free_bytes(self) -> int: ...
    def resolve(self, image: str) -> tuple[str, int]: ...
    def pull(self, ref: str) -> bool: ...
    def inspect(self, ref: str) -> tuple[list[str], str, str] | None: ...
    def remove(self, ref: str) -> bool: ...
    def build_spec(self, iid: str, image: str, digest: str, out: Path) -> dict[str, Any] | None: ...
    def case_a(self, spec_path: Path, out_dir: Path, timeout: float) -> dict[str, Any] | None: ...
    def blob_vs_worktree(self, ref: str, base: str, paths: Sequence[str]
                         ) -> dict[str, dict[str, str]]: ...
    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]: ...
    def fetch_row(self, iid: str) -> dict[str, Any]: ...
    def count_tokens(self, prompt: str) -> int: ...
    def synthesize(self, ref: str, edited: Mapping[str, E.BaseFile]) -> str: ...
    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float
             ) -> dict[str, Any]: ...


# ---- pure helpers -----------------------------------------------------------------------------
def image_name(iid: str) -> str:
    return "swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_")


def storage_need(compressed_bytes: int) -> int:
    """Frozen P1 per-pull rule: 2.5 x compressed size + 10 GB."""
    return int(2.5 * compressed_bytes + 10_000_000_000)


def derive_timeout(case_a_candidate_seconds: float) -> float:
    """G-4: 900 s if the Case-A candidate container took <= 300 s, otherwise 1800 s."""
    return TIMEOUT_SHORT if case_a_candidate_seconds <= TIMEOUT_THRESHOLD_S else TIMEOUT_LONG


def dump(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dump(obj))


def load_candidates(lottery_dir: Path = LOTTERY) -> list[Candidate]:
    """The frozen FG-3 order joined with pool row hashes; refuses if any FG-3 artifact changed."""
    for name, sha in FG3_SHA256.items():
        if H.sha256_bytes((lottery_dir / name).read_bytes()) != sha:
            raise AdmissionStop(f"FG-3 artifact {name} differs from its committed SHA-256")
    pool = json.loads((lottery_dir / "pool.json").read_text(encoding="utf-8"))
    order = json.loads((lottery_dir / "order.json").read_text(encoding="utf-8"))
    rows = {e["instance_id"]: e["row_sha256"] for e in pool["eligible"]}
    cands = [Candidate(x["rank"], x["instance_id"], x["repo"], rows[x["instance_id"]])
             for x in order["order"]]
    if [c.rank for c in cands] != list(range(1, len(cands) + 1)) or len(rows) != len(cands):
        raise AdmissionStop("FG-3 order/pool are not a single consistent population")
    return cands


# ---- one candidate ----------------------------------------------------------------------------
def admit_candidate(c: Candidate, ops: Ops, work: Path) -> dict[str, Any]:
    """Run steps 1–5, fix and record the decision, then (admitted only) the diagnostic
    self-check, then write provenance, then delete the image."""
    steps = dict.fromkeys(H.ADMISSION_STEPS, False)
    rec: dict[str, Any] = {"rank": c.rank, "instance_id": c.instance_id, "repo": c.repo,
                           "steps": steps, "reason": None, "events": []}
    ev: list[str] = rec["events"]
    image = image_name(c.instance_id)
    digest, size = ops.resolve(image)
    ref = f"{image}@{digest}"
    rec.update(image=image, digest=digest, compressed_bytes=size, ref=ref)
    ev.append("resolve")
    need, free = storage_need(size), ops.free_bytes()
    rec.update(storage_need=need, storage_free=free)
    if free < need:
        rec["reason"] = "STOP_STORAGE_GATE"
        write(work / "record.json", rec)
        raise AdmissionStop(f"storage gate: free {free} < need {need} before {c.instance_id}")
    ev.append("storage_ok")
    pulled = ops.pull(ref)
    ev.append("pull")
    if not pulled:
        pulled = ops.pull(ref)  # §14: one retry of a failed pull
        ev.append("pull_retry")
    stop: AdmissionStop | None = None
    try:
        if not pulled:
            rec["reason"] = "PULL_FAILED"
        else:
            insp = ops.inspect(ref)
            ev.append("inspect")
            if insp is None or ref not in insp[0] or insp[1] != PLATFORM:
                rec["reason"] = "IDENTITY_MISMATCH"
                rec["inspect"] = insp
            else:
                rec["image_id"] = insp[2]
                steps["identity"] = True
        spec: dict[str, Any] | None = None
        if steps["identity"]:
            spec = ops.build_spec(c.instance_id, image, digest, work / "A" / "spec.json")
            ev.append("spec")
            if spec is None or spec.get("instance_id") != c.instance_id or \
                    spec.get("digest") != digest:
                rec["reason"] = "SPEC_FAILED"
            else:
                steps["spec_built"] = True
        if steps["spec_built"] and spec is not None:
            evid = ops.case_a(work / "A" / "spec.json", work / "A" / "run",
                              ADMISSION_CASE_A_TIMEOUT)
            ev.append("case_a")
            det = (evid or {}).get("deterministic", {})
            rec["case_a"] = {k: det.get(k) for k in ("classification", "reason", "detail")}
            if det.get("classification") == "PASSED":
                dur = float(evid["diagnostics"]["candidate"]["duration_seconds"])  # type: ignore[index]
                rec["case_a_candidate_seconds"] = dur
                rec["stage_x_timeout_s"] = derive_timeout(dur)
                steps["case_a_passed"] = True
            else:
                rec["reason"] = "CASE_A_NOT_PASSED"
        gold_paths: list[str] = []
        if steps["case_a_passed"] and spec is not None:
            gold_paths = sorted(H.p1().probe().patch_files(spec["patch"]))
            hashes = ops.blob_vs_worktree(ref, spec["base_commit"], gold_paths)
            ev.append("h_check")
            rec["h_check"] = hashes
            if gold_paths and all(hashes.get(p, {}).get("base_sha") is not None and
                                  hashes[p]["base_sha"] == hashes[p].get("worktree_sha")
                                  for p in gold_paths):
                steps["h_base_equals_worktree"] = True
            else:
                rec["reason"] = "H_BASE_WORKTREE_MISMATCH"
        base: dict[str, E.BaseFile] = {}
        if steps["h_base_equals_worktree"] and spec is not None:
            ok, info, base = stage_p(c, ops, spec, gold_paths, ref, work / "P")
            ev.append("stage_p")
            rec["stage_p"] = info
            if ok:
                steps["f_budget_and_audit"] = True
            else:
                rec["reason"] = info["failure"]
        rec["admitted"] = H.admission_decision(steps)  # FIXED here, before any self-check
        ev.append("decision")
        write(work / "record.json", rec)
        if rec["admitted"] and spec is not None:
            def synth(ed: Mapping[str, E.BaseFile]) -> str:
                return ops.synthesize(ref, ed)

            def gate(diff: str) -> dict[str, Any]:
                return ops.gate(spec, diff, work / "SELF-S" / "run", rec["stage_x_timeout_s"])
            sc = H.self_check(spec["patch"], base, synth, gate)
            ev.append("self_check")
            write(work / "SELF-S" / "self_check.json", sc)
            rec["self_check_diagnostic"] = sc
            if sc["harness_integrity_alarm"]:
                stop = AdmissionStop(f"A-1 harness-integrity alarm on {c.instance_id}")
    finally:
        rec["provenance"] = {k: rec.get(k) for k in ("image", "digest", "ref", "image_id",
                                                     "compressed_bytes")}
        ev.append("provenance_written")
        write(work / "record.json", rec)
        if pulled:
            removed = ops.remove(ref)
            ev.append("remove" if removed else "remove_failed")
            write(work / "record.json", rec)
            if not removed and stop is None:
                stop = AdmissionStop(f"image delete failed for {ref}")
    if stop is not None:
        raise stop
    return rec


def stage_p(c: Candidate, ops: Ops, spec: dict[str, Any], gold_paths: list[str], ref: str,
            out: Path) -> tuple[bool, dict[str, Any], dict[str, E.BaseFile]]:
    """(f): both prompts within B_PROMPT and both leakage audits PASS. A dataset row that differs
    from the FG-3 row identity is a STOP (data drift), not inadmissibility."""
    row = ops.fetch_row(c.instance_id)
    if H.sha256_bytes(L.canon(row)) != c.row_sha256:
        raise AdmissionStop(f"dataset row for {c.instance_id} differs from FG-3 (drift)")
    for k in ("base_commit", "patch", "test_patch", "repo"):
        if str(row[k]) != spec[k]:
            raise AdmissionStop(f"{c.instance_id}: dataset {k} differs from the built spec")
    base = ops.read_base(ref, spec["base_commit"], gold_paths)
    info: dict[str, Any] = {"failure": None, "gold_paths": gold_paths}
    try:
        files = [(p, base[p].content.decode("utf-8")) for p in gold_paths]
    except (KeyError, UnicodeDecodeError):
        info["failure"] = "F_GOLD_FILE_UNREADABLE"
        return False, info, base
    pr = H.build_prompts(spec["repo"], str(row["problem_statement"]), files)
    _full, spans = H.p1().render(spec["repo"], str(row["problem_statement"]), files)
    tokens = {"U": ops.count_tokens(pr.prompt_u), "S": ops.count_tokens(pr.prompt_s)}
    audits = {arm: H.p1().leakage_audit(prompt, spans, spec, row, set(gold_paths), gold_paths)
              for arm, prompt in (("U", pr.prompt_u), ("S", pr.prompt_s))}
    out.mkdir(parents=True, exist_ok=True)
    (out / "common.txt").write_bytes(pr.common.encode("utf-8"))
    (out / "prompt_U.txt").write_bytes(pr.prompt_u.encode("utf-8"))
    (out / "prompt_S.txt").write_bytes(pr.prompt_s.encode("utf-8"))
    write(out / "leakage_audit.json", audits)
    info.update(common_identity=pr.common_identity, identity_u=pr.identity_u,
                identity_s=pr.identity_s, seed=pr.seed, tokens=tokens,
                audit={arm: a["verdict"] for arm, a in audits.items()})
    write(out / "preflight.json", info)
    if max(tokens.values()) > B_PROMPT:
        info["failure"] = "F_OVER_BUDGET"
    elif any(a["verdict"] != "PASS" for a in audits.values()):
        info["failure"] = "F_LEAKAGE_AUDIT_FAIL"
    return info["failure"] is None, info, base


# ---- the walk ---------------------------------------------------------------------------------
def run_phase_a(cands: Sequence[Candidate], ops: Ops, root: Path = EVIDENCE) -> dict[str, Any]:
    """Frozen §10 walk via `p2_lottery.walk`. Resumable: an existing decided record is reused,
    never re-run. Admitted work directories become P2-NN in admission order."""
    if (root / "_lottery" / "admission_log.json").exists():
        raise AdmissionStop("Phase A already completed (admission_log.json exists)")
    by_id = {c.instance_id: c for c in cands}

    def admit(iid: str) -> bool:
        c = by_id[iid]
        work = root / "_admission" / f"{c.rank:02d}-{iid}"
        done = work / "record.json"
        if done.exists():  # resume: a decided, provenance-complete record is final
            rec = json.loads(done.read_text(encoding="utf-8"))
            if "admitted" in rec and "provenance_written" in rec["events"]:
                return bool(rec["admitted"])
        work.mkdir(parents=True, exist_ok=True)
        return bool(admit_candidate(c, ops, work)["admitted"])

    admitted, log = L.walk([(c.instance_id, c.repo) for c in cands], admit)
    slots = {f"P2-{i:02d}": iid for i, iid in enumerate(admitted, start=1)}
    n = len(admitted)
    summary = {"n_admitted": n, "status": "OK" if n >= H.N_MIN else "VOID",
               "n_min": H.N_MIN, "cap": L.CAP, "target": L.N_TARGET, "slots": slots,
               "per_repo": {r: sum(1 for i in admitted if by_id[i].repo == r) for r in L.REPOS},
               "walk_log": log}
    for slot, iid in slots.items():  # §16 layout: admitted evidence under P2-NN
        src = root / "_admission" / f"{by_id[iid].rank:02d}-{iid}"
        dst = root / slot
        if src.exists() and not dst.exists():
            src.rename(dst)
    write(root / "_lottery" / "admission_log.json", summary)
    return summary


# ---- real operations (FG-4 execution only; never called by the tests) -------------------------
class DockerOps:  # pragma: no cover
    def __init__(self) -> None:
        if H.sha256_bytes(P1_SPEC_SCRIPT.read_bytes()) != P1_SPEC_SHA256:
            raise AdmissionStop("stage0/p1env/p1_spec.py differs from its frozen SHA-256")
        self._count: Callable[[str], int] | None = None

    @staticmethod
    def _run(args: list[str], stdin: bytes | None = None, timeout: float = 3600.0
             ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(args, input=stdin, capture_output=True, timeout=timeout,
                              check=False)

    def free_bytes(self) -> int:
        out = self._run(["df", "-B1", "--output=avail", "/mnt/c"]).stdout.decode().split()
        return int(out[-1])

    def resolve(self, image: str) -> tuple[str, int]:
        raw = self._run(["docker", "manifest", "inspect", "-v", f"{image}:latest"]).stdout
        entries = json.loads(raw)
        entries = entries if isinstance(entries, list) else [entries]
        e = next(x for x in entries
                 if (x["Descriptor"].get("platform") or {}).get("architecture") == "amd64")
        man = e.get("SchemaV2Manifest") or e.get("OCIManifest")
        return str(e["Descriptor"]["digest"]), sum(int(lay["size"]) for lay in man["layers"])

    def pull(self, ref: str) -> bool:
        return self._run(["docker", "pull", "--platform", PLATFORM, ref]).returncode == 0

    def inspect(self, ref: str) -> tuple[list[str], str, str] | None:
        p = self._run(["docker", "image", "inspect", ref, "--format",
                       "{{json .RepoDigests}}|{{.Os}}/{{.Architecture}}|{{.Id}}"])
        if p.returncode != 0:
            return None
        digests, plat, iid = p.stdout.decode().strip().split("|")
        return list(json.loads(digests)), plat, iid

    def remove(self, ref: str) -> bool:
        return self._run(["docker", "image", "rm", ref]).returncode == 0

    def build_spec(self, iid: str, image: str, digest: str, out: Path) -> dict[str, Any] | None:
        out.parent.mkdir(parents=True, exist_ok=True)
        p = self._run([sys.executable, "-B", str(P1_SPEC_SCRIPT), iid, image, digest, str(out)])
        (out.parent / "spec_stdout.txt").write_bytes(p.stdout + p.stderr)
        return json.loads(out.read_text(encoding="utf-8")) if p.returncode == 0 and \
            out.exists() else None

    def case_a(self, spec_path: Path, out_dir: Path, timeout: float) -> dict[str, Any] | None:
        probe = H.p1().PROBE_PATH
        p = self._run([sys.executable, "-B", str(probe), "run", "--spec", str(spec_path),
                       "--case", "A", "--out-dir", str(out_dir), "--run-label", "A",
                       "--timeout", str(timeout)], timeout=timeout + 600)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "case_a_stdout.txt").write_bytes(p.stdout + p.stderr)
        evf = out_dir / "A" / "evidence.json"
        return json.loads(evf.read_text(encoding="utf-8")) if evf.exists() else None

    def blob_vs_worktree(self, ref: str, base: str, paths: Sequence[str]
                         ) -> dict[str, dict[str, str]]:
        script = f"cd {REPO_DIR} && " + " && ".join(
            f"echo \"B {p} $(git cat-file blob {base}:{p} | sha256sum | cut -c1-64)\" && "
            f"echo \"W {p} $(sha256sum {p} | cut -c1-64)\"" for p in paths)
        out = self._run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "bash",
                         ref, "-c", script]).stdout.decode()
        res: dict[str, dict[str, str]] = {p: {} for p in paths}
        for line in out.splitlines():
            kind, path, sha = line.split(" ", 2)
            res[path]["base_sha" if kind == "B" else "worktree_sha"] = sha
        return res

    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]:
        p1 = H.p1()
        listed = self._run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "bash",
                            ref, "-c", f"cd {REPO_DIR} && git ls-tree -l -z {base} -- "
                            + " ".join(paths)]).stdout
        entries = {e[3]: e for e in p1.parse_ls_tree(listed)}
        blobs = p1.parse_cat_file_batch(self._run(
            ["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint", "bash", ref,
             "-c", f"cd {REPO_DIR} && git cat-file --batch"],
            stdin=b"".join(entries[p][2].encode() + b"\n" for p in paths)).stdout)
        return {p: E.BaseFile(entries[p][0], blobs[entries[p][2]]) for p in paths}

    def fetch_row(self, iid: str) -> dict[str, Any]:
        lot = L.p1_lottery()
        if lot.dataset_revision() != L.REVISION:
            raise AdmissionStop("dataset revision changed before row fetch")
        row = dict(H.p1().probe().fetch_row(L.DATASET, iid))
        if lot.dataset_revision() != L.REVISION:
            raise AdmissionStop("dataset revision changed after row fetch")
        return row

    def count_tokens(self, prompt: str) -> int:
        if self._count is None:
            self._count = H.p1().TokenCounter(None)
        return int(self._count(prompt))

    def synthesize(self, ref: str, edited: Mapping[str, E.BaseFile]) -> str:
        return H.synthesize_diff(ref, REPO_DIR, edited)

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float
             ) -> dict[str, Any]:
        return H.stage_x_gate(spec, patch, run_dir, timeout, "S")


def main(argv: list[str]) -> int:  # pragma: no cover
    if argv[1:] != ["run"]:
        print(__doc__)
        return 2
    try:
        H.check_spec()
        summary = run_phase_a(load_candidates(), DockerOps())
    except (AdmissionStop, H.HarnessStop, L.LotteryStop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: summary[k] for k in ("n_admitted", "status", "per_repo", "slots")},
                     indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
