# EPG-14 M-H0 — Execution Harness (synthetic stages only)

| Field | Value |
|---|---|
| Milestone | M-H0, harness only (RD decision 2026-10-22) |
| Scope | Stage-scoped execution, aggregate CPU enforcement, termination evidence, outcome classification |
| Not in scope | Any statistical engine; V0–V5 (refused by `run_stage.sh`); contract freeze; R-AUTH |
| Governance | R-MD pending except V0-specific details the RD adjudicates; MD-1, MD-2, MD-5 remain blockers for their later stages; V0-7d and P2 (c) NOT PERFORMED; R-V5 provisional |
| Status | Implemented. **WSL + Docker acceptance passed:** run `mh0-20261022T081840Z`, 16/16 cases as expected, criteria 1–8 MET (RD decision 2026-10-22). Harness code identity = `code_sha256` in that run's `wrapper_status.json` records. Software-mechanics harness only; no protection against arbitrary malicious stage code (§4 item 1). |

## 1. Layers (wrapper evidence overrides the driver)

| Layer | Where | Mechanism | Role |
|---|---|---|---|
| Host aggregate CPU monitor | `hostmon.py monitor` (WSL host) | Docker Engine API `/containers/{id}/stats?one-shot=true` → `cpu_stats.cpu_usage.total_usage` (cgroup aggregate over **all** container processes); poll 0.25 s; SIGKILL at ≥ cap | **Primary** budget enforcement → STOP-8 (BACKSTOP) |
| Host process monitor | `hostmon.py monitor` | `/containers/{id}/top`; > 1 process → SIGKILL | STOP-2 (BACKSTOP) |
| Host wall-clock limit | `hostmon.py monitor` | 60 s → SIGKILL | Hang guard; no contract STOP → UNCLASSIFIED |
| Monitor fault | `hostmon.py monitor` | 3 consecutive API faults while running → SIGKILL | Fail closed → UNCLASSIFIED |
| Kernel per-process limit | Docker `--ulimit cpu=5:5` | RLIMIT_CPU soft = hard (PID 1 ignores default SIGXCPU, so soft = hard is required) | Defence in depth; attributed to STOP-8 only with CPU evidence |
| In-process monitor | `egrid/driver.py` | `ITIMER_PROF` handler: STOP-8 (IN-PROCESS) at cap − reserve; STOP-2 on any live/reaped child | Defence in depth; lets the stage write partial artifacts |
| Static policy | `harness_tests/test_policy.py` | AST deny-list over `egrid/` (§12.3 list + process-creation paths) | Defence in depth (extension pending RD class-(b)) |
| Resource checks | `hostmon.py verify-config` (before start) and `driver.preflight` (in container) | Inspect HostConfig/Config vs required values; observe cgroup, rlimits, network, uid, rootfs, env | Criterion 8 |

## 2. Fixed synthetic parameters

| Parameter | Value | Note |
|---|---|---|
| Aggregate CPU budget (`CAP_S`) | 5 s | equals per-process RLIMIT_CPU |
| Test reserve (`RESERVE_S`) | 1 s | driver stops at 4 s process CPU |
| Driver check interval | 0.05 s process CPU | `ITIMER_PROF` |
| Host poll interval | 0.25 s wall | recorded `max_poll_gap_s` per run |
| Wall-clock limit | 60 s | harness guard only |
| Acceptance window, wrapper kill | aggregate CPU ∈ [5.0, 6.0] s | `acceptance.py BURN_TOLERANCE_S` |
| Kernel-kill attribution tolerance | 2 × max(poll, max gap) + 0.1 s | `classify._attribution_tolerance_s` |
| Memory | 2 GiB (`--test-memory 268435456` only for SYN-OOM) | non-default settings recorded in `test_settings` |

## 3. Records and classification

`runs/<run_id>/<stage>/stage/` (mounted rw at `/out`; driver artifacts and `stage_status.json`, written last, atomically), `wrapper/` (host only: inspections, `config_check.json`, `monitor.json`, `wrapper_status.json`, logs, `container_removed`), `outcome/stage_outcome.json` (classifier). Classification rules R0–R10 are in `egrid/classify.py`; PASS requires a valid driver PASS, a consistent exit code, no wrapper termination, no OOM, and a COMPLETE stage directory (every declared artifact present with matching SHA-256, every required artifact declared, no temp or undeclared files). Exit 137 alone never establishes a cause. Driver exit codes: 0 PASS, 64 + n STOP-n, 80 UNCLASSIFIED.

## 4. Known limits (stated, not hidden)

1. A stage that writes a fully self-consistent forged PASS and exits 0 within budget cannot be detected; stage code is trusted. The harness protects limits and classification, not against malicious stage code.
2. Host monitoring is sampled (0.25 s); overshoot past the cap is bounded by the poll gap × 1 CPU plus kill latency and is reported, not hidden.
3. Classification and monitoring run on the host's `python3` (version recorded in `wrapper_status.host`), not in the pinned image; the classifier is stdlib-only and unit-tested inside the pinned image (SYN-TESTS).
4. Requires a `unix://` Docker endpoint (Docker Engine API). Other endpoints are refused.
5. `env/README_ENV.md` §4 run commands (all six stages chained, `--rm`) are superseded by `run_stage.sh`; the evidence file itself is not edited.
6. The added AST deny-list entries are stricter than contract §12.3 and await RD class-(b) acceptance.

## 5. Target-venue commands

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research
docker image inspect --format '{{.Id}}' "$(sed -n 's/^image_id=//p' stats/egrid/env/out/env.lock)"
docker context inspect --format '{{.Endpoints.docker.Host}}'; python3 --version
bash stats/egrid/harness_tests/run_mh0_acceptance.sh 2>&1 | tee /tmp/mh0_acceptance.txt
```

Acceptance: `M-H0 ACCEPTANCE: ALL CRITERIA MET`, with every case `OK`. Any `MISMATCH` is reported as a specific failure and fixed in isolation.
