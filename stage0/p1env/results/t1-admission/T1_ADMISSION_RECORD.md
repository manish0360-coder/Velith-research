# P1 Stage-0/1: T1 admission record (`pallets__flask-5014`). ADMITTED

**Date:** 2026-10-01, RD-executed from WSL. **Velith main:** `6ca531f` (read-only). **Probe:** `probe.py`, SHA-256 `560834d5…8e1f` (the frozen M2 probe).

| Check | Result |
|---|---|
| Pre-pull space | C: free 32,299,384,832 B ≥ rule 12,863,845,777 B (2.5 × 1.146 GB + 10 GB): PASS |
| Pull by pinned digest | `swebench/sweb.eval.x86_64.pallets_1776_flask-5014@sha256:eaf597005c159361cb8ee26018fb3741b320f331065f0c95726d83ccf2f1fba4`, `--platform linux/amd64` |
| Identity | RepoDigests contains the pinned ref; linux/amd64; image ID `sha256:eaf59700…f1fba4`: PASS |
| Inventory | exactly one image added (T1); containers and volumes unchanged vs `phase0-wsl-20260930T111607Z`. C: free after the pull: 32,337,928,192 B |
| Spec | `~/velith-prototype/flask-5014.json` matches the M2 evidence manifest (`OK`) |
| Case A (gold) | **PASSED / ALL_REQUIRED_PASSED / 60/60.** Baseline and candidate both `RAN`, exit 0, `network_mode=none` |
| Continuity vs M2 | `probe compare` against M2 `runs/A`: only `velith_commit` differs (`e04d7f9` → `6ca531f`). All other deterministic evidence is identical |

**Evidence files:** `01_pull.txt` … `06_compare_vs_M2.txt` and `A-20261001/` (evidence.json, baseline/candidate stdout + JUnit). `MANIFEST.sha256` has SHA-256 `06c7ef93c0829c51543f52dcd36fc6de1cb676a93b44cd17675a115ce0c81863`.

**Scope:** probe-level admission evidence only. It is not a production-verifier verdict (P1 design §4, §17). T2–T5 were not pulled.
