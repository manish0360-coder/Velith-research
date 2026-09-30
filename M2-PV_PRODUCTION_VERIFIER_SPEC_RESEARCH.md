# M2-PV — Production Verifier Specification (Research Report)

**Status:** DRAFT — specification research for Scientific Review. **Not frozen. Not an implementation authorization.**
**Repository baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3` (`HEAD == origin/main`, working tree clean at inspection).
**Inputs:** the repository (authoritative), the M2 feasibility freeze record (`experiments/m2_container_prototype/FREEZE_RECORD.md`), sandbox research experiments E0–E11 (Appendix A), and external sources (Appendix C).
**Author:** Chief Systems Engineer (same agent that wrote the M2 probe; see §0.3).
**Date:** 2026-09-25

---

## 0. How to read this document

### 0.1 Evidence classes (never blurred)

Every requirement carries exactly one class:

| Class | Meaning |
|---|---|
| **A** | Demonstrated by M2 real-container evidence (evidence manifest `30c59a45…6255f7`, probe `560834d5…138e1f`). |
| **B** | Supported by the existing frozen architecture (a cited file, spec section or DECISIONS entry). |
| **C** | New engineering/security requirement introduced here. |
| **D** | Requires empirical validation before it may be frozen. |
| **E** | Open research question; no known mechanism settles it. |

A requirement whose *threat* was shown in the sandbox experiments of Appendix A is still class **C** (the requirement is new). The sandbox reference `[S:E4]` records the evidence behind the threat. **Sandbox experiments are not M2 evidence.** They ran on the host sandbox (CPython 3.10.12, pytest 7.3.0, no Docker, no task image). They show properties of Python and pytest, not of the production container.

### 0.2 Identifier scheme

`PV-<AREA>-<NNN>`. Areas: `TRUST`, `EXEC`, `ENV`, `ADM` (task admission), `BASE`, `CAND`, `TEST`, `RUN` (runner), `RES` (result channel), `ISO`, `RSRC`, `NET`, `VERDICT`, `ATTR` (attribution), `PROV`, `DET`, `REPRO`, `SEC`, `SCI`. Every requirement states its verification method (**V:**).

### 0.3 Conflict of interest

The author wrote the M2 probe, its audit script, the mock controls, and the sandbox experiments in Appendix A. Findings that would be convenient for the prototype are flagged as such. The Scientific Review should confirm Appendix A independently.

### 0.4 Limitation numbering discrepancy (not silently resolved)

The M2-PV brief lists L7 as "self-reported evidence markers" and L12 as "provenance limitations". The frozen FREEZE_RECORD §7 lists **L7 = tampering control** and **L12 = self-reported evidence**. It has no "provenance limitations" item. This document uses the **frozen record's numbering** (it is frozen evidence). It treats "provenance limitations" as an additional item, **L13**, derived from the repository findings in §4.4 (F-11, F-12). See Appendix B.

---

## 1. Purpose

Specify the execution boundary a production verifier must satisfy so that real repository-level tasks can be verified **without candidate behavior, infrastructure faults, or test-harness manipulation silently contaminating scientific Verdicts**. The Verdicts feed three consumers:

1. A2's verified-signal write filter (`src/velith/arms/filters.py:85`). It admits every non-flaky `FAILED` as a *verified failure* (`:63`) and every non-flaky, uncontradicted `PASSED` as a verified success.
2. The M8 held-out evaluation sink (`src/velith/evaluation/record.py`).
3. The M9/M10 analysis endpoint. It scores `PASSED` = 1 and **every other verdict = 0** (`src/velith/analysis/encoding.py:39`; M9_SPEC §3.5.1).

A verifier error therefore contaminates learning (consumer 1) and measurement (consumers 2–3) differently, and both kinds of contamination must be controlled.

## 2. Scope

- The verification of one candidate patch against one task whose execution environment is a published, digest-pinned task image (the SWE-bench image family is the first instance).
- Trust model, execution model, environment identity, baseline and candidate execution, test and harness integrity, isolation, resource limits, network, verdict semantics, attribution of anomalies, provenance, determinism, reproducibility.
- The admission (certification) of tasks into a corpus, **insofar as the verifier's guarantees depend on it**.
- Compatibility with the frozen M0–M10 contracts.

## 3. Non-goals

- No implementation, code, or enum change is authorized by this document.
- No generic sandbox platform, no scheduler, no multi-host infrastructure (D14: "single-machine discipline").
- No proposer-side hardening. Proposer data-leakage vectors (e.g. future git history in task images, Appendix C [5][6]) are **out of scope here** and recorded as OQ-12 for the proposer boundary.
- No LLM-based judgment of any kind (D3, D14).
- No redesign of M8/M9/M10. Where the verifier's needs conflict with them, the conflict is **documented** (§24), not resolved.
- No claim that in-process result forgery can be prevented (see §10.4, PV-SCI-004).

---

## 4. Existing Architecture Boundary (forensic inventory)

### 4.1 The verifier seam as it exists

| Element | Location | Fact |
|---|---|---|
| Verifier protocol (M5) | `src/velith/batch/runner.py:45-50` | Structural `verify(self, task: Task, patch: str) -> Verdict`. |
| Verifier protocol (M8) | `src/velith/evaluation/attempt.py:62-67` | Identical shape, declared independently. |
| Implementation | `src/velith/harness/verifier_sandbox.py:140` | `VerifierSandbox`, the only implementation. |
| Verdict value | `verifier_sandbox.py:120-137` | `state, output, secondary_passed, flaky, duration_seconds`; `frozen=True, extra="forbid"`. |
| Verdict taxonomy | `src/velith/episodes/episode.py:39-52` | Closed: `PASSED, FAILED, PATCH_APPLY_FAILED, NO_PATCH, INFRA_ERROR` (D16.7, D17). |
| Infra channel | `verifier_sandbox.py:111-117` | `SandboxExecutionError` is "the only failure the verifier raises"; the orchestrator maps it to `INFRA_ERROR`. |
| Task | `src/velith/task.py:45-61` | `task_id, repo_path, prompt, hidden_test_command, secondary_test_command`; `frozen=True, extra="forbid"`. |
| Task adapter | `src/velith/batch/adapter.py:26-31` | `materialize(CorpusTask) -> Task`; only `FixtureTaskAdapter` exists. |
| Corpus task | `src/velith/corpus/loader.py:35-51` | `label, material (content-addressed identity), handle (opaque), partition`. |
| Episode hash boundary | `episode.py:60` / `:80` | `verdict_state`, `verdict_output`, `secondary_passed` inside; `flaky`, timings outside (D21). |
| M8 record | `src/velith/evaluation/record.py:35-49` | `verdict_state, secondary_passed, flaky` + identity + tokens; **no `output`, no verifier or environment identity**; `extra="forbid"`. |
| M8 evaluation identity | `src/velith/evaluation/provenance.py` | Checkpoint, manifest hash, arm, base model, eval seed, cost limits. **No verifier or environment component.** |
| Container config | `docker-compose.yml:21-33`, `docker/verifier.Dockerfile` | Single `verifier` service; bind mount `./data/episodes:/app/data/episodes`; `cap_add: SYS_ADMIN`; no `USER` directive (runs as root). |
| Pinned env | `verifier_sandbox.py:103-108` | `PYTHONHASHSEED=0, TZ=UTC, LC_ALL=C, PYTHONDONTWRITEBYTECODE=1`. |
| Existing verifier tests | `tests/unit/test_verifier_sandbox.py` | 20 test functions, incl. timeout→FAILED (`:91`), infra raises (`:116`), egress blocked (`:182`), secondary tamper-proof (`:246`). |
| M2 prototype | `experiments/m2_container_prototype/probe.py` | Host-driven, one container per run, baseline + candidate, JUnit mapping; frozen evidence only. |

### 4.2 Verdict flow through the frozen pipeline

```
Task ─► Verifier.verify(task, patch)
          ├─ returns Verdict(state ∈ {PASSED, FAILED, PATCH_APPLY_FAILED}, …)   [NO_PATCH is set by callers]
          └─ raises SandboxExecutionError   ──► M1 spike: exit non-zero (runner/spike.py:135)
                                             ──► M5 batch: propagates, sweep aborts (batch/runner.py:86; no handler)
                                             ──► M8 eval: propagates, run aborts (evaluation/runner.py:76; no handler)
                                                  ──► run incomplete ──► M9 §3.5.1: pre-registration VOID
Verdict ─► Episode (M5) ─► A1 admits all (filters.py:77); A2 admits non-flaky PASSED(uncontradicted)/FAILED (filters.py:85)
Verdict ─► EvaluationRecord (M8) ─► M9 encoding: PASSED=1, every other state=0 (encoding.py:39)
```

### 4.3 Consequences that constrain the production verifier

1. **A returned `INFRA_ERROR` would be scored 0 by M9** (not missing), biasing against whichever arm it hits. Raising is the only infra channel that doesn't bias measurement. Under the frozen M8 runner, raising means **the whole evaluation becomes VOID**.
2. **Any infrastructure fault misattributed as `FAILED` enters A2's memory as a verified failure**, which is exactly the poisoning the program exists to prevent.
3. **Any outcome the candidate can drive to "infra" is a denial-of-evaluation attack.** One adversarial candidate could VOID a pre-registered experiment. Attribution must therefore be symmetric (§14.4).
4. **M9 scores only `verdict_state`**; `secondary_passed` does not gate the endpoint. For measurement, the integrity of the *primary* verdict is everything.

### 4.4 Findings in the frozen boundary (read-only; nothing modified)

| ID | Finding | Evidence | Relevance |
|---|---|---|---|
| F-1 | The primary verdict is decided by the test process **exit code alone**. | `verifier_sandbox.py:275` | `os._exit(0)` in candidate code yields exit 0 and no report [S:E6], so PASSED under this rule. |
| F-2 | The **primary** hidden test is not re-materialized; only the secondary is. | `:294-302` vs `:210-221` | A patch editing the primary test file is not neutralized (fixture path). |
| F-3 | Timeout maps to `FAILED`. | `:270-272`; frozen by test `test_verifier_sandbox.py:91`, not by any DECISIONS entry | An infra-slow host becomes a "verified failure" in A2. |
| F-4 | The test process **inherits the whole orchestrator environment** (`{**os.environ, **_DETERMINISTIC_ENV}`). | `:268` | Environment identity is not controlled. Orchestrator configuration is visible to candidate code. |
| F-5 | Flake reruns and the secondary suite run in the **same workspace and interpreter environment**, after candidate code has already executed. | `:221`, `:235` | Candidate code can persist into later runs [S:E7], so reruns are not independent measurements. |
| F-6 | Candidate code runs as **root with `CAP_SYS_ADMIN`** in the **same container, user and mount namespace** as the orchestrator. That container has the **episodes bind mount**. `unshare -n` removes only the network. | `docker-compose.yml:21-33`; Dockerfile has no `USER`; `:257` | The trusted experience store is inside the untrusted code's reach. A detached candidate process can outlive the verdict [S:E10]. **This is a structural fact from configuration; exploitation was not attempted.** |
| F-7 | `SandboxExecutionError` is unhandled in M5 and M8. | `batch/runner.py:86`, `evaluation/runner.py:76` | Every infra fault aborts the sweep or evaluation. |
| F-8 | M9 endpoint ignores `secondary_passed`. | `encoding.py:39` | See §4.3(4). |
| F-9 | A2 admits every non-flaky `FAILED`. | `filters.py:63`, `:85-107` | See §4.3(2). |
| F-10 | `Task` cannot express image digest, base commit, test patch, required test IDs, or protected surface. | `task.py:45-61` (`extra="forbid"`) | The real-task contract is missing (the known open Task amendment). |
| F-11 | `EvaluationRecord` carries no verdict output, no verifier identity, no environment identity. | `record.py:35-49` | Held-out measurements have no verifier provenance (L13). |
| F-12 | `EvaluationProvenance.identity` excludes verifier and environment identity. | `evaluation/provenance.py` | Evaluations under different verifiers or images share an identity, so comparability is asserted without being guaranteed (L13). |
| F-13 | `docs/M8_SPEC.md:11` still reads "Status: DRAFT" although `m8-complete` is tagged. | `git tag` | Documentation inconsistency only; noted, not acted on. |

### 4.5 What M2 actually demonstrated (class A)

From the frozen record (§4, §5 of FREEZE_RECORD), for `pallets__flask-5014` only, with benign candidates and the listed tampering methods:

1. Sealed, digest-pinned, network-less execution of one real repository-level task.
2. The baseline control separates environment faults **built into the tested image** from candidate failure, for the tested cases.
3. Correct `PASSED`, `FAILED` and `INFRA_ERROR` outcomes for the exercised paths.
4. The listed file-level tampering methods are neutralized (`tests/test_blueprints.py`, `pyproject.toml`, `tox.ini`, `tests/conftest.py`, candidate-added `pytest.ini`/`.pytest.ini`/`setup.cfg`/`conftest.py`).
5. Repeated outcomes reproducible on one host (A, F1, F2 identical; A vs E identical excluding the label).

Nothing else is class A. In particular, **the M2 probe itself had open vectors** that the sandbox experiments later showed:

- `python -m pytest` import shadowing [S:E1a]
- test-directory module shadowing [S:E3]
- post-write JUnit rewrite [S:E5]
- in-process forgery [S:E4]

None of these was exercised in the real container. They do not contradict any M2 result, because M2 used only benign candidates. They do bound what M2 can be said to show.

---

## 5. Trust Model

### 5.1 Principals and assets

**Assets to protect:** (i) the episode store and every memory derived from it; (ii) the M8 evaluation sink, pre-registration and analysis inputs; (iii) the corpus and held-out partition; (iv) the correctness of each Verdict; (v) the host.

| Principal | Trust | Rationale |
|---|---|---|
| Verifier orchestrator (the process that launches runs, collects results, classifies) | **TRUSTED** | Velith code under review and CI. |
| Task specification (image digest, base commit, test patch, required IDs, protected surface, trusted runner config) | **TRUSTED once admitted** | Content-addressed and certified by the admission gate (§8.2). Before admission, dataset labels are **untrusted input** (L11). |
| Task image at a pinned digest | **TRUSTED as an environment, only before candidate code runs** | Published by a third party; verified by digest and by admission-time baseline behavior. Its *runtime state* stops being trusted once candidate code executes in it. |
| Trusted runner (launcher, pytest invocation, trusted config, canaries) | **TRUSTED as an artifact**; **UNTRUSTED as a running process** | The runner file is ours. Once it imports candidate code, the interpreter is shared with the candidate [S:E4]. |
| Test artifacts (test files at base commit + test patch) | **TRUSTED as artifacts**; their execution is not | Same reason. |
| Verdict collector (classification logic) | **TRUSTED** | Runs in the orchestrator, never in a container that ran candidate code. |
| Provenance recorder | **TRUSTED** | Same. |
| Candidate patch, repository state after apply, candidate-added files, candidate Python modules | **UNTRUSTED** | Model output; adversarial by assumption. |
| Any process in the candidate container after the first candidate-code execution | **UNTRUSTED** | Includes pytest itself, the JUnit writer and every subprocess [S:E4, E5, E10]. |
| Any file writable by the candidate container | **UNTRUSTED after the candidate phase begins** | Includes JUnit, stdout markers, `/tmp` and the environment's `site-packages` if writable [S:E7]. |

### 5.2 The time-of-trust rule

> **Trust in a container's state ends at the first instruction of candidate code.**

`git apply` executes no candidate code. So everything done by trusted scripts **after applying the candidate patch and before the first interpreter start that can import candidate code** is trustworthy. That covers restoring the test surface, hashing it and recording the tree. Everything produced after that point is *candidate-influenced*, including test reports, exit codes and stdout.

This is why the M2 "surface" hashes are trustworthy but the M2 JUnit results are only candidate-influenced evidence (L12). It rests on one assumption: that `git apply` and the restore script execute no repository-controlled code. That assumption needs checking (smudge/clean filters, hooks, symlinks) → PV-SEC-006, class **D**.

### 5.3 Channels

| Channel | Trust | Examples |
|---|---|---|
| **Runtime channel** (container runtime, observed from outside) | Trusted | `docker inspect` exit code, `OOMKilled`, network mode, image ID, start/stop status. |
| **Pre-execution channel** (trusted scripts before candidate code) | Trusted | Base-commit check, surface restoration and hashes, tree hash after apply. |
| **Baseline channel** (container that never received candidate code) | Trusted relative to the candidate (not to the image publisher) | Baseline JUnit, baseline stdout. |
| **Candidate channel** (anything produced after candidate code ran) | **Candidate-influenced** | Candidate JUnit, exit code, stdout, timing. |

**Boundary statement.** Candidate-influenced evidence may *lower* a verdict (towards `FAILED`) freely. It may *raise* a verdict to `PASSED` only when every consistency and integrity check in §10 passes. Even then, `PASSED` carries the residual risk stated in PV-SCI-004.

### 5.4 The unavoidable residual

Tests import and execute candidate code in the same interpreter. [S:E4] and [S:E11b] show that **four to ten lines added to the candidate's own source module**, with no config, conftest or file tampering and with a trusted launcher, can rewrite pytest's reports so that every test "passes" with exit code 0 and a clean JUnit. A naive audit hook did not observe it [S:E11]. On CPython 3.10, class attribute assignment raises no audit event (Appendix A, E11c).

**No execution-boundary design can prevent this.** It can be *detected* in its undifferentiated form (canaries, §10.4). Targeted forms are an **open research problem (class E)**. The same limit applies to the official SWE-bench harness, which grades by parsing stdout (Appendix C [1]).

---

## 6. Execution Model

### 6.1 Execution-placement alternatives

| ID | Placement | Feasible for real tasks | Security | Frozen compatibility | Evidence |
|---|---|---|---|---|---|
| AR-1 | Status quo: candidate runs as a subprocess inside the Velith container (`VerifierSandbox`) | **No.** Real tasks need their own image (Python version, deps); the Velith image cannot hold them all. | Weakest (F-6). | Fully compatible. | B |
| AR-2 | **Host-side orchestrator** launches one fresh task container per run via the Docker CLI (the M2 prototype model) | **Yes** (demonstrated for one task). | Candidate never sees the Docker socket; orchestrator is trusted. | **Conflicts** with D19 (single container; socket and sidecar rejected) and with M0 §6 / PROJECT_STATE:127 (host never the source of truth) → CX-1, CX-2. | A (feasibility), B (conflict) |
| AR-3 | Velith container gets the host Docker socket and launches **sibling** task containers | Yes (by construction; not demonstrated). | The socket is root-equivalent on the host. Any residual in-container candidate execution (AR-1 legacy path, F-6) becomes a **host compromise**. | Conflicts with D19 (socket dependency explicitly rejected) → CX-1. Preserves M0 "verdict inside the container". | B (conflict), D |
| AR-4 | Docker-in-Docker (privileged) | Yes. | `--privileged` defeats the isolation it provides. | Rejected by the M2 SRC rulings (no privileged mode, no DinD). | B |
| AR-5 | Rootless runtime (rootless Docker or Podman) driven by the orchestrator | Unknown on WSL2 / Docker Desktop. | Better than AR-3 (no host-root socket). | Same D19 conflict as AR-3. | D |
| AR-6 | AR-2, AR-3 or AR-5 plus a hardened container runtime for task containers (gVisor `runsc`, Kata) | Unknown on WSL2 / Docker Desktop. | Removes the shared-kernel attack surface for the candidate. | Additive. | D |

**Observation, not recommendation.** Every feasible placement for real tasks requires a second container per run. That contradicts D19 as written. The choice between AR-2, AR-3 and AR-5 cannot be made without first amending D19 (and possibly M0 §6) through the DECISIONS amendment procedure (`DECISIONS.md:479`). → **FD-1, STOP item.**

### 6.2 Run-structure alternatives

| ID | Structure | Pros | Cons |
|---|---|---|---|
| RS-1 | Per candidate: 1 baseline + 1 candidate container (M2 prototype) | Demonstrated (A); baseline contemporaneous with candidate. | 2× cost; no anomaly confirmation. |
| RS-2 | Admission-time certification (R baselines + R gold runs) **plus** per-candidate run(s) **plus** a per-session sentinel baseline | Baseline health is a *task property*, established once and re-checked for drift. | Drift between sentinel runs is undetected. Needs a rule for sentinel frequency. |
| RS-3 | RS-1 or RS-2 **plus** anomaly confirmation: any candidate-run anomaly triggers up to R_c fresh-container candidate re-runs | Separates reproducible candidate behavior from one-off infrastructure noise (L1). | Cost grows only on anomalies. |

### 6.3 Candidate execution model (for review, not yet a recommendation)

This combination follows from the analysis. It is **not** the only viable one; FD-1, FD-4, FD-7, FD-9 and FD-14 decide it.

```
ADMISSION (once per task, before any pre-registration):
  pull by digest → verify identity → R_b baseline runs + R_g gold runs in fresh containers
  → certify: required IDs map, baseline healthy, gold passes all, runs identical → content-addressed TaskSpec
EVALUATION (per candidate):
  [trusted] fresh container from digest, no network, limits, non-root(?), read-only root(?)
  [trusted] verify base commit + clean tree
  [trusted] git apply candidate            (no candidate code runs)
  [trusted] rematerialize test surface; remove candidate-added files under test roots; hash surface
  [trusted] git apply test patch
  ─── trust boundary: first interpreter start that can import candidate code ───
  [candidate-influenced] trusted launcher → pytest with trusted config + canaries → report
  [trusted] container fully stopped (PID namespace gone) → collect runtime channel + reports
  [trusted] classify with attribution rules; confirm anomalies by fresh-container re-runs
  [trusted] emit Verdict or raise SandboxExecutionError; write provenance
```

---

## 7. Environment Identity

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-ENV-001 | Every run uses the task image **by digest** (`image@sha256:…`), never by tag. Before the first run of a session, the orchestrator verifies that `RepoDigests` contains the exact digest and that `Os/Architecture` equals the spec's platform. On mismatch it raises (infra), never degrades. | A (probe `verify_image`) | Mismatched-digest and mismatched-platform fixtures → raise; evidence records image ID. |
| PV-ENV-002 | Inside every container, before any patch, the trusted script verifies `HEAD^1 == base_commit` (or the spec's declared base relation) and an empty `git status --porcelain`. Violation → baseline/infra error, never a candidate verdict. | A | Tampered-image fixture → raise. |
| PV-ENV-003 | The environment identity recorded for each run is: image digest, image ID, platform, image HEAD, base commit, test-patch SHA-256, protected-surface SHA-256 (post-restore), trusted-runner SHA-256, trusted-config SHA-256, interpreter path and version, pytest version, **installed pytest plugin set** (`pytest11` entry points), the exact environment-variable map, and the resource limits. | C | Evidence schema test; two runs differing in any one component have different environment identities. |
| PV-ENV-004 | The test-process environment is an **explicit allow-list** (image ENV plus the frozen `_DETERMINISTIC_ENV` plus runner variables). It is never inherited from the orchestrator (contrast F-4). | C | Canary variable in orchestrator env is absent inside the container. |
| PV-ENV-005 | The deterministic environment of D18 (`_DETERMINISTIC_ENV`, `verifier_sandbox.py:103`) is **reused, not redefined**, and demonstrably takes effect in the test process. **`python -I` must not be used**, because it silently ignores `PYTHONHASHSEED` [S:E2]. | B (D18) + C | In-container `hash()` of a fixed string is identical across two runs. |
| PV-ENV-006 | The published image is the complete environment: **no install, build or network step** at verification time. D19 Phase 1 is a no-op for real tasks. | A (SRC ruling; M2) + B (D19 permits a no-op Phase 1) | Network-none run of admission gold passes. |
| PV-ENV-007 | The environment is activated in a way validated per task (direct interpreter vs `conda activate`). The choice is part of the environment identity. Admission rejects tasks where the two invocations disagree on baseline or gold outcomes. | D (L6: validated for flask-5014 only) | Admission runs both invocations for R runs; they must agree. |

## 8. Baseline Execution and Task Admission

### 8.1 Baseline semantics

**Baseline healthy (BASELINE_HEALTHY)** iff, in a container that never received candidate code: every required test ID is present in the report, every PASS_TO_PASS test passed, and no FAIL_TO_PASS test passed. `failed` and `error` both count as "not passed" for FAIL_TO_PASS. `skipped` counts as not passed for both sets. This is the M2 rule (A); the treatment of `skipped` is new and needs a ruling (OQ-3).

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-BASE-001 | A baseline that is not healthy is **never** a candidate verdict. It is an environment/task defect: raise (§14). | A (Case C) | Fault-injected baseline → raise; candidate never classified. |
| PV-BASE-002 | Baseline and candidate for the same comparison use the **same digest, same runner, same config, same limits, same env map**. The evidence must show equality of every PV-ENV-003 component except the candidate patch. | A (probe) + C (full component list) | Evidence diff between baseline and candidate identities is exactly `{candidate_patch_sha256}`. |
| PV-BASE-003 | Baseline runs in a **separate fresh container** from any candidate run. | A | Container IDs differ; runtime channel shows two creations. |
| PV-BASE-004 | Zero-P2P tasks have no baseline health signal (a broken environment fails F2P either way). They are **inadmissible**. | C (prior finding, L10) | Admission rejects a zero-P2P spec. |
| PV-BASE-005 | When baseline evidence is taken (per candidate, RS-1; or per session sentinel, RS-2) is a frozen decision. Whichever is chosen, the baseline used for a verdict must be recorded by evidence ID. | C + FD-14 | Provenance links each Verdict to a baseline evidence ID. |

### 8.2 Task admission (certification) — the gate the verifier's guarantees depend on

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-ADM-001 | A task enters a corpus only after admission: R_b baseline runs and R_g gold runs, each in a fresh container, all under the production runner. | C | Admission report per task. |
| PV-ADM-002 | Admission criteria: all baseline runs healthy; all gold runs pass every required test; all baseline runs identical; all gold runs identical; every required ID mapped. Any failure → task excluded, with the reason recorded. | C (generalizes M2 A/F) | Deliberately broken specs are rejected with the right reason. |
| PV-ADM-003 | Dataset labels (F2P/P2P) are **untrusted input** until PV-ADM-002 passes (L11). | C | A spec with a mislabeled P2P test is rejected. |
| PV-ADM-004 | The admitted TaskSpec is content-addressed and immutable. Its digest is the verification contract the verifier executes. | C | Changing any field changes the digest; the verifier refuses an unknown digest. |
| PV-ADM-005 | Admission records resource profiles (wall time, peak memory) of baseline and gold runs, used to set per-task limits (§12). | C + D | Profiles present; limits derived by the frozen formula. |
| PV-ADM-006 | Admission happens **before** pre-registration of any experiment using the corpus, so a task-level defect can never VOID a running evaluation. | C | Pre-registration refuses a corpus containing an uncertified task. |
| PV-ADM-007 | The values of R_b and R_g. | E (statistical adequacy unknown; see OQ-5) | — |

## 9. Candidate Execution

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-CAND-001 | Each candidate run uses a **fresh container** from the pinned digest; no container is reused after candidate code executed in it. This includes flake reruns [S:E7], which contrasts with F-5. | A (fresh container per run) + C (reruns) | Every run has a distinct container ID; persistence fixture (Exp. X-3) shows no carry-over. |
| PV-CAND-002 | The candidate patch is applied with `git apply` (pinned mechanism, frozen). A non-applying patch → `PATCH_APPLY_FAILED` (grounded outcome, not infra). | A (mock) + B (`verifier_sandbox.py:210-212`) | Real-container non-applying patch fixture (L8). |
| PV-CAND-003 | Patch delivery never uses a host bind mount (copy-in to a created, not-started container, as in M2). | A | Inspect shows no binds. |
| PV-CAND-004 | Whatever the candidate does to the test surface, config surface or test roots is neutralized before tests run (§10). Legitimate source changes elsewhere are preserved byte-for-byte. | A (listed paths) + C (full rule) | Tree hash of non-test paths after restore equals the tree hash after candidate apply. |
| PV-CAND-005 | The candidate may not supply or influence the runner command, the config, the environment map, the selected tests or the limits. | C | Static: these are functions of the TaskSpec and runner only. |
| PV-CAND-006 | Result collection happens only after the candidate container has **fully stopped** (all processes in its PID namespace terminated). No reads while any candidate process may be alive [S:E10]. | C | Detached-process fixture (Exp. 10) cannot alter collected evidence. |

---

## 10. Test / Harness Integrity

The problem splits into four layers, each with a different achievable guarantee:

| Layer | What must hold | Achievable? |
|---|---|---|
| 10.1 Test artifacts | The tests executed are exactly base-commit tests + test patch. | Yes, via trusted pre-execution steps. |
| 10.2 Runner resolution | The pytest that runs is the environment's pytest, with the trusted config and plugin set. | Yes, via invocation and filesystem controls. |
| 10.3 Result channel | Reported outcomes are not altered after the run or by file-level means. | Partly: file-level forgery is detectable. |
| 10.4 In-process semantics | Candidate code imported by tests cannot alter pytest's judgment. | **No** (§5.4); only undifferentiated forgery is detectable. |

### 10.1 Test artifacts (L3 file-level, L5)

**Alternatives.**

| ID | Mechanism | Covers | Gaps | Evidence |
|---|---|---|---|---|
| T-1 | Restore a named protected-file list from base commit; delete candidate-added *config-named* files (M2 prototype) | Listed files; named configs anywhere | Candidate-added **non-config** modules inside test roots, e.g. `tests/pkg.py` shadowing the code under test [S:E3]; hand-picked list (L5). | A (listed), sandbox gap |
| T-2 | **Rematerialize whole test roots**: every directory touched by the test patch, plus config files on pytest's ini/conftest search path, restored from base commit; **all** candidate-added files under those roots deleted | T-1 plus E3 plus the list problem, via a rule instead of a list | Test code outside the declared roots; tasks whose legitimate fix adds files under test roots (discarded, as the official harness discards candidate test edits it overwrites). | C / D |
| T-3 | Mount the trusted test tree **read-only** over the test roots (from a trusted image layer or volume, no host bind) | T-2 plus candidate *runtime* writes to tests | Mount mechanics under the FD-1 placement; test suites that write into their own directory would break (fidelity). | D |
| T-4 | Reject (score) patches that touch test or config paths | Deters tampering | Stricter than the official harness; penalizes legitimate test edits; the scoring category is unclear. | E (policy) |

**Rule for the protected surface (replaces L5's hand-picked list; to be frozen):**
*Protected surface* = (a) every path in the test patch; (b) every file under each **test root**, where a test root is the directory of each path in (a) and its parents up to the repo root; (c) every file pytest consults for configuration or plugins on the path from the repo root to each test root (`pytest.ini`, `.pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `conftest.py`, `__init__.py`); (d) the trusted config and runner files, which live **outside** the repository. Part (b) is the part E3 requires. Whether (b) should be "the directory only" or "the directory's whole subtree" is OQ-2.

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-TEST-001 | Before the first candidate-code execution, the protected surface is restored to base-commit content, candidate-added files within it are deleted, and then the test patch is applied. | A (subset) + C (rule) | Tamper fixtures for (a)–(c) all neutralized; surface hash equals the gold run's. |
| PV-TEST-002 | The post-restore protected-surface hash is computed by a trusted script before candidate code runs, and must equal the admission-time hash for the TaskSpec. Mismatch → integrity failure attributed to the candidate (§14). | A (hash) + C (comparison) | Exp. 7. |
| PV-TEST-003 | Candidate edits to non-test source are preserved exactly (no over-deletion). | C | Tree-hash check of PV-CAND-004. |
| PV-TEST-004 | Symlinks in the candidate patch cannot redirect a protected path or any trusted write. | D | Exp. 14b. |
| PV-TEST-005 | Choice among T-2 and T-3 (and whether T-4 applies). | FD-7 | — |

### 10.2 Runner resolution (L4)

| Finding | Evidence |
|---|---|
| `python -m pytest` puts the working directory first on `sys.path`; a repo-root `pytest.py` replaces pytest and exits 0. | [S:E1a]; Python docs (Appendix C [2]) |
| `python -I -m pytest`, the console entry point, and a trusted launcher script outside the repo all defeat that shadow. | [S:E1b–E1d] |
| `-I` also ignores `PYTHONHASHSEED` and every other `PYTHON*` variable, which breaks D18. | [S:E2]; Appendix C [2] |
| `-P` / `PYTHONSAFEPATH` removes only the unsafe path entry (Python ≥ 3.11) and keeps the environment. | Appendix C [2]. **Not tested** (sandbox is 3.10). |
| pytest's default `prepend` import mode inserts the test directory first on `sys.path`, so a candidate module there shadows the code under test; `--import-mode=importlib` prevents it. | [S:E3, E3b] |
| A candidate `tests/pytest.ini` becomes the config file (ini discovery starts at the common ancestor of the arguments); an explicit `-c <trusted file> --rootdir <repo>` overrides it. | [S:E8, E8b] |
| A repo-root `sitecustomize.py` was **not** imported under either invocation (3.10). | [S:E9] (negative result) |
| A `.pth` written into a writable `site-packages` executes at every later interpreter start, **including `-I`**. | [S:E7] |

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-RUN-001 | The test process is started through a **trusted launcher located outside the repository**, or through a mechanism proven equivalent in the task image, so that no repository path precedes the environment's `site-packages` at interpreter start. | C [S:E1] | Exp. 4 in the real image. |
| PV-RUN-002 | `-I` is **forbidden** as the L4 control, because it disables D18's pinned environment. | C [S:E2] | Hash-seed check (PV-ENV-005). |
| PV-RUN-003 | pytest runs with an **explicit trusted configuration** (`-c` from a content-addressed copy taken at admission; `--rootdir` fixed), so no repository ini file can be selected. | C [S:E8b] | Exp. 8. |
| PV-RUN-004 | The import mode that blocks test-root shadowing (`importlib`, or T-2 deletion, or both) is chosen per task at admission and must preserve baseline and gold outcomes. | D (L6: `importlib` may change test semantics) | Admission runs both; must agree. |
| PV-RUN-005 | The installed plugin set is recorded, and plugin auto-loading is either disabled with an explicit plugin list or pinned by recorded identity. Plugins that read repository files (e.g. dotenv-style plugins) are either absent or listed as a known vector. | C + D | Exp. 9 (env via files). |
| PV-RUN-006 | The environment's `site-packages` and interpreter are **not writable** by the candidate process (non-root user and/or read-only root filesystem), which removes persistence within a run [S:E7]. | C + D (feasibility for SWE-bench images; official harness `chmod 777`s the repo for a non-root user, Appendix C [1]) | Exp. X-3. |
| PV-RUN-007 | The runner command, config, plugin set and import mode are part of environment identity (PV-ENV-003). | C | Schema test. |

### 10.3 Result channel (L3 file-level, L12)

| ID | Mechanism | Detects | Evidence |
|---|---|---|---|
| C-1 | JUnit file copied out after exit (M2) | nothing by itself | A (feasible), [S:E5] forgeable |
| C-2 | **Cross-consistency**: JUnit per-test outcomes, the pytest exit code and the pytest terminal summary must agree | Post-write rewrites that miss one channel [S:E5: exit 1 vs all-pass JUnit]; `os._exit` [S:E6: exit 0, no report] | C |
| C-3 | Completeness: every required ID present exactly once; no required test deselected or skipped | Deselection via config [S:E8]; collection sabotage | A (mapping) + C |
| C-4 | Canary tests (§10.4) | Undifferentiated in-process forgery | C / D |
| C-5 | Exit code only (frozen `VerifierSandbox`, F-1) | nothing | **Rejected** [S:E6, E8] |

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-RES-001 | `PASSED` requires: a report present and parseable; every required ID mapped exactly once with outcome `passed`; pytest exit code 0; the terminal summary consistent with the report; all canaries in their expected states. Exit code alone never suffices (rejects F-1). | C | Exp. 5, 6, 11. |
| PV-RES-002 | Report parsing is hardened: size cap, no DTD/entity expansion (the probe refuses `<!DOCTYPE`), and no path outside the container's result location. | A (probe) + C | Malformed and DTD fixtures. |
| PV-RES-003 | When the candidate-influenced channels are inconsistent with each other, the result is **not** `PASSED`. Attribution follows §14.4. | C | Exp. 6. |
| PV-RES-004 | A required ID that is missing in the candidate run while the baseline mapped all IDs is **candidate-attributable** (not infra), because the candidate controls collection-affecting code [S:E8]. | C | Exp. 5 variant. |

### 10.4 In-process semantics (L3 residual)

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-RES-005 | The trusted runner adds **canary tests** from a trusted file outside the repository, collected in the same session: at least one that must pass and at least one that **must fail**, with names not predictable from the task. A must-fail canary reported as passed → harness-integrity failure (candidate-attributed). | C (mechanism) + D (effectiveness) | Exp. 5 (blanket forgery [S:E4] must be caught); benign runs must show canaries correct. |
| PV-RES-006 | Detection of **targeted** in-process forgery (flipping only specific test IDs) is not claimed. | E | — |
| PV-RES-007 | Static screening of the candidate patch for harness-manipulation constructs (references to `_pytest`, `sys.modules` edits of test infrastructure, `atexit`, `os._exit`, `ctypes`, `builtins` rebinding) — either (i) record-only, or (ii) verdict-affecting. | E (false positive and negative rates unknown) → FD-9 | — |
| PV-RES-008 | Audit hooks are **not** relied on for detection: class attribute assignment raises no audit event on CPython 3.10 [S:E11c]. Behavior on 3.11+ is unverified. | C (negative finding) + D (3.11) | — |

---

## 11. Isolation Boundary

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-ISO-001 | Candidate code never executes in the container, user namespace or mount namespace that holds the orchestrator, the episode store, the evaluation sink, the corpus or the pre-registration (resolves F-6 for the production path). | C | Static: the production verifier has no code path executing candidate code locally; Exp. 14 shows none of those paths are reachable from the candidate container. |
| PV-ISO-002 | Task containers get: `--network none`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pids-limit`, `--memory` = `--memory-swap`, `--cpus`; **no** `--privileged`, **no** Docker socket, **no** host bind mounts, **no** Docker-in-Docker. | A (M2 flags) | `docker inspect` of every container in the evidence. |
| PV-ISO-003 | Filesystem: the candidate container's only writable areas are the repository working tree and bounded temp space. The root filesystem is read-only if the task image supports it. | C + D (image compatibility) | Exp. 14; admission shows gold passes under the configuration. |
| PV-ISO-004 | Process: all candidate processes live in the container's PID namespace, and collection happens only after teardown (PV-CAND-006). | C [S:E10] | Exp. 10. |
| PV-ISO-005 | Privilege: candidate processes run as a non-root user if the task image supports it. Otherwise the limitation is recorded per task. | D | Admission records user; gold passes as that user. |
| PV-ISO-006 | Kernel attack surface: a hardened runtime (gVisor, Kata) is optional and recorded in environment identity. | D | Feasibility test on the target host. |
| PV-ISO-007 | The legacy in-container `VerifierSandbox` path (AR-1: root, `CAP_SYS_ADMIN`, episodes mount) is **never** used for real-task candidates. | C (policy) + FD-13 | Static: the real-task adapter refuses the legacy verifier. |

## 12. Resource Limits

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-RSRC-001 | Every run has a wall-clock budget, memory limit (swap disabled), CPU quota and PID limit, all recorded in environment identity. | A (flags present) | Evidence. |
| PV-RSRC-002 | Per-task limits are derived from admission profiles by a frozen formula (e.g. `budget = max(floor, k × max(baseline, gold) wall time)`, memory likewise), so a legitimately slower or larger candidate is not penalized arbitrarily. | C + D (values of k and floors) | Admission profiles → limits; sensitivity experiment. |
| PV-RSRC-003 | **Candidate-only timeout**: the baseline completed within budget, and the candidate run exceeded it. The anomaly is confirmed by re-execution (§14.4). If reproducible → `FAILED` (candidate non-termination). If not reproducible → nominal verdict with `flaky=True`. | C (supersedes, for the production path, F-3's unconditional mapping) + D | Exp. 2. |
| PV-RSRC-004 | **Candidate-only memory exhaustion** inside the candidate's own cgroup (`OOMKilled` true, container limit reached, baseline peak well below the limit): confirmed by re-execution; reproducible → `FAILED`. | C + D (whether the runtime distinguishes a container-limit kill from host-level OOM on WSL2 is **unverified**) | Exp. 3. |
| PV-RSRC-005 | Resource exhaustion attributable to the host (e.g. daemon or VM out of memory, disk full), observed through the trusted runtime channel → infra (§14). | D (detection signals unverified) | Exp. 1 variants. |
| PV-RSRC-006 | Disk usage of the candidate container is bounded. | D (depends on storage driver) | Fill-disk fixture. |
| PV-RSRC-007 | The prototype rule "candidate-only OOM → `INFRA_ERROR`" is **not** carried forward. It lets a candidate choose exclusion or VOID over failure (FREEZE_RECORD §8). | B (freeze record) + C | — |

## 13. Network Policy

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-NET-001 | All task containers (baseline, candidate, admission) run with `--network none`. The runtime channel confirms `NetworkMode=none` for every container; any other value → raise. | A (Case E; probe checks) | Evidence. |
| PV-NET-002 | An in-container outbound probe runs after the tests and records the result. `connected` → integrity failure of the environment (raise). | A (probe) | Evidence. |
| PV-NET-003 | DNS resolution, IPv6 egress and access to host-published ports are probed as well. | D (not probed in M2) | Exp. 13. |
| PV-NET-004 | The orchestrator's own network needs (proposer model access) are outside the task container and irrelevant to it (D19's two-phase intent is preserved by construction). | B (D19 rationale) | Static. |

---

## 14. Verdict State Machine

### 14.1 Can the frozen contracts express the required semantics?

**Yes, without a new `VerdictState`, provided two conditions hold.**
(i) Infrastructure outcomes are **raised** (`SandboxExecutionError`), never returned.
(ii) Integrity failures attributable to the candidate are returned as `FAILED`, with the reason carried in `Verdict.output`.
Condition (i) is forced by M9 (§4.3(1)); condition (ii) by D17 (no new state).

The **cost** of (i) is that under the frozen M8 runner an exhausted infra retry VOIDs the evaluation (F-7). That is a frozen-pipeline consequence, not a contradiction. It is recorded as CX-5 and FD-3.

Internal states below are **verifier-internal classifications**. They are **not** enum values, and none is added to code.

### 14.2 Internal states → frozen outcome

| Internal state | Meaning | Frozen outcome | Attribution |
|---|---|---|---|
| `ENV_UNVERIFIED` | Digest, platform or base-commit check failed | **raise** `SandboxExecutionError` | infra |
| `BASELINE_UNHEALTHY` | Baseline fails §8.1 | **raise** | environment/task |
| `BASELINE_HEALTHY` | Precondition met | (continue) | — |
| `PATCH_APPLY_FAILURE` | `git apply` of the candidate fails | `PATCH_APPLY_FAILED` | candidate |
| `TEST_INTEGRITY_FAILURE` | Post-restore surface hash ≠ admission hash, or test patch fails to apply after restore | **raise** if the restore machinery failed; `FAILED` if a candidate artifact survived restore (a design defect that must also be logged loudly) | see §14.4 (OQ-7) |
| `HARNESS_INTEGRITY_FAILURE` | Canary contradiction, inconsistent result channels, missing required IDs | `FAILED` (reason in `output`) | candidate |
| `TIMEOUT` (candidate-only, reproduced) | §12 | `FAILED` | candidate |
| `RESOURCE_EXHAUSTED` (candidate-only, reproduced) | §12 | `FAILED` | candidate |
| `INFRA_FAULT` (trusted-channel evidence: create/start/copy failure, daemon error, host-level exhaustion) | Bounded fresh-container retries exhausted | **raise** | infra |
| `ANOMALY_NOT_REPRODUCED` | Candidate-run anomaly absent on confirmation | nominal state from first complete run, `flaky=True` | measurement quality (D17) |
| `CANDIDATE_FAILED` | Complete, consistent report; some required test not passed | `FAILED` | candidate |
| `CANDIDATE_PASSED` | PV-RES-001 satisfied | `PASSED` | candidate |

`NO_PATCH` remains the caller's state (`attempt.py:141`, `batch/runner.py:93`); the verifier is never called without a patch.

### 14.3 Transitions

```
START
 └─► verify env (digest, platform)          ── fail ──► raise (ENV_UNVERIFIED)
      └─► baseline evidence (fresh or sentinel, FD-14)
           ├─ unhealthy ────────────────────────────────► raise (BASELINE_UNHEALTHY)
           └─ healthy
               └─► candidate container: base check ── fail ──► raise (ENV_UNVERIFIED)
                    └─► git apply candidate ── fail ──► return PATCH_APPLY_FAILED
                         └─► restore surface, hash, apply test patch
                              ├─ restore machinery fault ──────► retry ≤ R_i ─► raise
                              └─► run (trust boundary) → stop → collect
                                   ├─ trusted-channel infra fault ─► retry ≤ R_i ─► raise
                                   ├─ anomaly (timeout / OOM / missing / inconsistent / canary)
                                   │     └─► confirm with ≤ R_c fresh re-runs
                                   │           ├─ reproduced ──► return FAILED (reason)
                                   │           └─ not reproduced ─► return nominal, flaky=True
                                   └─ complete & consistent
                                         ├─ all required passed ─► return PASSED
                                         └─ otherwise ───────────► return FAILED
```

### 14.4 Attribution rule (L1) — the central scientific decision

- **Principle.** An anomaly is attributed to **infrastructure only on evidence from a trusted channel that the candidate cannot influence** (§5.3). Otherwise it is attributed to the **candidate**, but only after confirming by re-execution that it reproduces. Non-reproducible anomalies become measurement-quality provenance (`flaky`), which A2 already excludes (`filters.py:105`).
- **Why symmetric.** Infra-by-default lets any candidate VOID an evaluation (§4.3(3)). Candidate-by-default lets host noise poison A2 (§4.3(2)). Confirmation by fresh re-execution is the only mechanism found that separates the two without trusting candidate-influenced evidence.
- **What it cannot do.** A deterministic infra fault that affects **only** candidate runs and leaves no trusted-channel trace reproduces on every re-run, so it is misattributed. No example of such a fault is known. Its existence is not ruled out → **E** (OQ-4).

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-ATTR-001 | Infra attribution requires trusted-channel evidence (§5.3). | C | Exp. 1. |
| PV-ATTR-002 | Every candidate-run anomaly is confirmed by up to R_c fresh-container re-runs before a candidate-attributed `FAILED` is returned. | C + D (R_c) | Exp. 1, 2, 3. |
| PV-ATTR-003 | A non-reproduced anomaly yields the nominal first-complete-run state with `flaky=True`. The analysis consequence of that nominal state for M9 is OQ-6. | B (D17 flaky provenance) + C | Exp. 1. |
| PV-ATTR-004 | Infra retries are bounded (R_i). Exhaustion raises; the M8 consequence is FD-3. | C | Exp. 1. |
| PV-ATTR-005 | Every attribution decision is recorded with the evidence that justified it. | C | Evidence schema. |

## 15. Failure Taxonomy (reason codes; recorded, not enum values)

| Reason code | Frozen outcome | Channel that evidences it |
|---|---|---|
| `IMAGE_IDENTITY_MISMATCH` | raise | runtime |
| `PLATFORM_MISMATCH` | raise | runtime |
| `BASE_COMMIT_MISMATCH`, `IMAGE_TREE_DIRTY` | raise | pre-execution |
| `BASELINE_UNHEALTHY:{p2p_not_passed, f2p_passed, unmapped, no_report, timeout, resource}` | raise | baseline |
| `CONTAINER_CREATE_FAILED`, `COPY_IN_FAILED`, `START_FAILED`, `RUNTIME_ERROR` | raise after R_i | runtime |
| `RESTORE_FAILED`, `TEST_PATCH_APPLY_FAILED` | raise after R_i | pre-execution |
| `NETWORK_NOT_ISOLATED` | raise | runtime / probe |
| `CANDIDATE_PATCH_DID_NOT_APPLY` | `PATCH_APPLY_FAILED` | pre-execution |
| `REQUIRED_TESTS_NOT_PASSED` | `FAILED` | candidate |
| `CANDIDATE_TIMEOUT_REPRODUCED` | `FAILED` | runtime + candidate |
| `CANDIDATE_RESOURCE_EXHAUSTED_REPRODUCED` | `FAILED` | runtime |
| `REQUIRED_IDS_MISSING` | `FAILED` | candidate |
| `RESULT_CHANNELS_INCONSISTENT` | `FAILED` | candidate |
| `CANARY_CONTRADICTION` | `FAILED` | candidate |
| `ANOMALY_NOT_REPRODUCED` | nominal, `flaky=True` | all |
| `ALL_REQUIRED_PASSED` | `PASSED` | candidate (PV-RES-001) |

**Fail-closed rule.** Any condition not in this table: `PASSED` is never returned; raise if it arose before the trust boundary, return `FAILED` (candidate-attributed after confirmation) if after. (C)

Placing the reason code and a deterministic evidence digest in `Verdict.output` puts them **inside the episode hash** (`verdict_output` is hashed, `episode.py:60`). That is legitimate only if the content is a reproducible function of (task, patch, environment) (D21's criterion). Timings, container IDs and temp paths must therefore be excluded. (B + C)

---

## 16. Provenance

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-PROV-001 | Every verification produces a content-addressed **evidence record** stored by the trusted orchestrator. It contains: environment identity (PV-ENV-003); inputs (candidate patch SHA-256, TaskSpec digest); per-run runtime-channel facts; per-run per-test outcomes; attribution decisions; the verdict. It is split into a *deterministic* part (hashed) and a *diagnostic* part (timings, container IDs; not hashed), as the M2 probe did. | A (split) + C (content) | Schema test; re-verification yields an identical deterministic digest (PV-DET-001). |
| PV-PROV-002 | Each evidence item is labelled with its **channel** (runtime / pre-execution / baseline / candidate-influenced, §5.3). This resolves L12 by labelling, not by pretending candidate-channel evidence is trusted. | C | Schema test. |
| PV-PROV-003 | Evidence is written only to a verifier-owned store outside any candidate container. It is never written into the episode store, the evaluation sink, or memory (D8 segregation preserved). | B (D8) + C | Static. |
| PV-PROV-004 | Episodes reference the evidence through the deterministic evidence digest carried in `Verdict.output` (§15), with no schema change. | C (no-amendment option) | Round-trip test. |
| PV-PROV-005 | Held-out measurements (`EvaluationRecord`, which has **no output field**, F-11) need a separate link from `(evaluation_identity, task_identity, arm, seed)` to the evidence digest. Options: (a) a verifier-side ledger keyed by those fields (no amendment); (b) an M8 record amendment. | FD-11 | — |
| PV-PROV-006 | The evaluation identity must change when the verification contract changes (F-12). Options: (a) bind the TaskSpec digest into `CorpusTask.material`, so it flows into task identity → manifest hash → `EvaluationProvenance.identity` with no amendment (the verification contract becomes part of what a task *is*); (b) amend `EvaluationProvenance`. Option (a) does **not** cover changes to the verifier *implementation* that leave the spec unchanged. | FD-10 + E (whether verifier-implementation identity belongs in evaluation identity) | Changing image digest changes the manifest hash under (a). |

## 17. Determinism

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-DET-001 | Re-verifying the same (TaskSpec, patch) yields the same frozen outcome, the same `Verdict.output`, and the same deterministic evidence digest (D18 L1–L3). | A (n=3, one task, one host) + B (D18) | Exp. 16 across admitted tasks. |
| PV-DET-002 | The D18 pinned environment is effective inside the task container (PV-ENV-005). | B + D (not yet shown in-container) | In-container hash check. |
| PV-DET-003 | Test order is the runner's deterministic collection order; no randomization plugins. | C | Plugin-set check (PV-RUN-005). |
| PV-DET-004 | Flakiness is measured at admission (R runs) and, for candidates, only through anomaly confirmation (§14.4); flaky outcomes carry `flaky=True` (D17, D21). | B + C | Exp. 16 with a known-flaky fixture. |
| PV-DET-005 | Whether the frozen convention "nominal state = first run" (`verifier_sandbox.py:222`) is the right nominal state for non-reproduced anomalies in the M9 endpoint. | E → OQ-6 | — |

## 18. Reproducibility

| ID | Requirement | Class | V: |
|---|---|---|---|
| PV-REPRO-001 | Given the evidence record, a third party can re-run the verification (digest, TaskSpec, patch, runner and config hashes, limits, invocation) without access to Velith internals. | C | Replay from evidence alone. |
| PV-REPRO-002 | Cross-host reproduction: admitted tasks give identical deterministic evidence on at least two hosts. | D (L9: one host only) | Two-host admission replay. |
| PV-REPRO-003 | Evidence and TaskSpecs are retained immutably, with a hash manifest, for the lifetime of any experiment that used them (as the M2 freeze condition 2 required). | A (practice) + C | Manifest verification. |

## 19. Security Invariants

| ID | Invariant | Class |
|---|---|---|
| PV-SEC-001 | Untrusted code never runs where trusted state is writable or readable (PV-ISO-001). | C |
| PV-SEC-002 | No candidate container has network, the Docker socket, host binds, extra capabilities or privilege escalation (PV-ISO-002). | A |
| PV-SEC-003 | No evidence produced after the trust boundary can raise a verdict to `PASSED` unless every PV-RES-001 check passes (§5.3). | C |
| PV-SEC-004 | No state from one run can reach another run (fresh container per run; no shared writable volume). | A (fresh containers) + C (reruns) |
| PV-SEC-005 | The runner, config and canaries are resolved from locations the candidate cannot write, and are hashed into environment identity. | C |
| PV-SEC-006 | Trusted pre-execution steps (`git apply`, restore, hashing) execute no repository-controlled code: no hooks, no filter drivers, no symlink traversal. | D |
| PV-SEC-007 | Result parsing cannot be exploited by hostile report content (PV-RES-002). | A + C |
| PV-SEC-008 | Every failure of a security invariant **fails closed**: never `PASSED`; raise before the trust boundary; candidate-attributed `FAILED` after it. | C |

## 20. Scientific Invariants

| ID | Invariant | Class |
|---|---|---|
| PV-SCI-001 | An infrastructure fault is never recorded as a grounded outcome, and never enters A2 (by raising, or through `flaky` quarantine). | B (D16.7, `filters.py`) + C |
| PV-SCI-002 | A candidate can never cause an infrastructure classification, except through behavior evidenced on a trusted channel (anti-DoS; §4.3(3)). | C |
| PV-SCI-003 | Baseline and candidate differ only by the candidate patch (PV-BASE-002). | A + C |
| PV-SCI-004 | **Residual, stated explicitly:** a `PASSED` verdict certifies that no *detectable* harness manipulation occurred. It does not certify the absence of targeted in-process forgery (§5.4). Every consumer-facing document must say so. | E |
| PV-SCI-005 | The verifier is identical across arms (M8's "one identical harness"); any verifier change changes evaluation identity (PV-PROV-006). | B (M8) + C |
| PV-SCI-006 | Dataset labels are empirical claims validated at admission, never assumed (L11). | C |
| PV-SCI-007 | No claim generalizes beyond the admitted tasks and the validated test frameworks (L10). Pytest-only until another framework is admitted with its own validation matrix. | C |

---

## 21. Adversarial Validation Matrix (must precede implementation freeze)

**None of these experiments has been run in a task container.** Where a sandbox precursor exists it is cited; it shows the *threat*, not the *control*. All experiments run under the candidate production configuration, in the real task image (initially `pallets__flask-5014`), through an experiment-only probe outside `src/`. Every experiment is paired with the benign control (gold patch → `PASSED`) under the same configuration, to show the control does not break legitimate candidates.

| # | Experiment | Setup | Expected state | Expected evidence | Failure condition | Remains unproven |
|---|---|---|---|---|---|---|
| 1 | Candidate-only infra fault | Healthy baseline; orchestrator injects a runtime fault into the candidate run only (kill the container from outside mid-run; fail `docker cp`; stop daemon briefly) | Trusted-channel fault → retry → gold eventually `PASSED`; exhausted retries → **raise** | Runtime-channel record of the fault and retries | Fault classified `FAILED`; or `PASSED` without a complete report | Deterministic candidate-only infra faults leaving no trusted trace (OQ-4) |
| 2 | Candidate timeout | Patch adds an infinite loop reached by one F2P test | `FAILED` (`CANDIDATE_TIMEOUT_REPRODUCED`) after R_c confirmations | Wall-clock over budget in all confirmation runs; baseline within budget | `PASSED`; raise; or unbounded run | Host-contention-induced timeouts on a loaded machine |
| 3 | Candidate resource exhaustion | Patch allocates memory beyond the limit in an F2P path; variant: fork bomb vs `--pids-limit` | `FAILED` (`…RESOURCE_EXHAUSTED_REPRODUCED`) | `OOMKilled=true` / PID-limit evidence in all confirmations; baseline peak well below | Raise (candidate-caused VOID); host affected | Distinguishing container-limit OOM from host/VM OOM on WSL2 |
| 4 | Candidate-added `pytest.py` (repo root and `src/`) | As [S:E1a] | Tests run under the environment's pytest; gold+shadow → `PASSED`; shadow only → `FAILED` | Runner identity in evidence; the shadow's marker absent from output | Shadow executes; exit 0 without report accepted | 3.11 `-P` behavior if used instead of a launcher |
| 5 | Candidate-added `conftest.py` (root, `tests/`, nested test subdir) with a force-pass hook; plus the in-source blanket forgery of [S:E4] | Real-image version of D0 plus [S:E4] | conftest variants: neutralized → `FAILED`. In-source blanket forgery: **canary contradiction** → `FAILED` | Removal log; surface hash = admission; canary outcomes | Any `PASSED` for a non-fix candidate | Targeted forgery (PV-RES-006, E) |
| 6 | Candidate-modified result files | Patch registers an `atexit` rewrite of the report [S:E5]; variant: `os._exit(0)` [S:E6] | `FAILED` (`RESULT_CHANNELS_INCONSISTENT` / `REQUIRED_IDS_MISSING`) | Exit code vs report vs summary disagreement recorded | `PASSED` | A forgery keeping all three channels consistent is class E (reduces to 5) |
| 7 | Candidate-modified tests | Patch edits the F2P test, a P2P test, and adds a new module under `tests/` shadowing the code under test [S:E3] | Neutralized; gold+tamper → `PASSED`; tamper only → `FAILED` | Surface hash = admission; candidate-added files listed as deleted | Any tampered byte reaches the run | Tests outside declared test roots (OQ-2) |
| 8 | Candidate-modified runner configuration | Patch adds `tests/pytest.ini` with `addopts = -k`, a `pyproject.toml` in a subdir, a `setup.cfg`, and edits root `pyproject.toml`/`tox.ini` [S:E8] | Trusted `-c` config in force; no deselection; outcomes as benign | Evidence shows trusted config hash; the rootdir recorded | Deselection or config change takes effect | Config consulted by plugins outside pytest's ini mechanism |
| 9 | Candidate environment-variable manipulation | Patch adds `.env`, edits `tox.ini` `setenv`, and sets `os.environ` at import for subprocess-spawning tests | Environment map in evidence equals the allow-list; outcomes unaffected except through candidate code's own in-process effects | Env map hash identical to baseline | Candidate-file-driven variable reaches the test process start | Plugins in other images that read repo files |
| 10 | Candidate subprocess manipulation | Patch spawns a detached process that sleeps and rewrites the report / writes to `/tmp` after pytest exits [S:E10] | Collection only after teardown; detached write absent from evidence | Container stopped before collection; no late modification | Any post-exit write affects evidence | — |
| 11 | Test-path shadowing | Candidate module in `tests/` named after a dependency imported by tests (e.g. `werkzeug.py`) and after the package under test [S:E3] | Deleted by T-2, or ineffective under the import mode | Deletion log / import-mode record | Shadow module imported | Import mode fidelity on other tasks (PV-RUN-004) |
| 12 | Import-path manipulation | `sitecustomize.py`, `usercustomize.py` and `.pth` at the repo root; runtime `.pth` write into `site-packages` [S:E7, E9] | No startup execution; runtime write fails (read-only / non-root) or has no effect on any later run | Write attempt result recorded; later runs clean | Candidate code runs at interpreter startup | Behavior on each supported interpreter version |
| 13 | Network access attempt | TCP to public IP, DNS lookup, IPv6, `host.docker.internal`, `172.17.0.1` | All blocked; `NetworkMode=none` | Probe results per target | Any connection | Kernel-level escapes (out of scope) |
| 14 | Filesystem escape attempt | Candidate code reads and writes `/`, `/proc/1/root`, `/var/run/docker.sock`, host paths; **14b:** patch with symlinks pointing to protected paths and outside the repo | No trusted asset reachable; symlink patch refused or neutralized | Listing of accessible paths; `git apply` result | Any trusted path readable or writable | Container-runtime vulnerabilities |
| 15 | Baseline unhealthy | Fault injected in both containers (M2 Case C), **plus** a P2P-failing variant (exercises the path M2 did not) | Raise, `BASELINE_UNHEALTHY` with the correct sub-reason | Baseline evidence | Candidate classified | — |
| 16 | Deterministic rerun | Gold, non-fix and each adversarial case re-verified R times; and on a second host | Identical deterministic evidence digests | Digest comparison | Any difference not labelled `flaky` | Hosts beyond the two tested |
| 17 | Legitimate candidate test failure | A plausible but wrong fix: F2P passes, one P2P regresses (L8 path not exercised in M2) | `FAILED` | Per-test outcomes | `PASSED`, or raise | — |
| 18 | Legitimate candidate test pass | Gold patch; and an alternative correct fix differing from gold | `PASSED` | All required passed; canaries correct | `FAILED` for a correct fix (false negative introduced by controls) | Correct fixes that legitimately need test-root or config changes (discarded by design) |
| X-1 | Patch that does not apply (L8) | Malformed patch in the real image | `PATCH_APPLY_FAILED` | `git apply` output | Anything else | — |
| X-2 | Admission rejects bad specs | Mislabelled P2P; zero-P2P; flaky test | Rejected with the right reason | Admission report | Admitted | — |
| X-3 | Persistence across runs | Candidate writes `.pth` / edits `site-packages` in run 1; honest run 2 follows | Run 2 unaffected (fresh container) | Run-2 evidence equals baseline | Any carry-over | — |
| X-4 | Invocation fidelity (L6) | Admission compares direct interpreter vs `conda activate`, and `prepend` vs `importlib` import mode | Agreement | Admission report | Disagreement → task excluded | Tasks not yet admitted |

**Matrix acceptance rule:** every row meets its expected state, with its benign control `PASSED`, on the target host. A row that cannot be made to pass either changes the design (back to specification) or is explicitly recorded as an accepted residual by the Scientific Review. Rows 5-targeted and 6-consistent are pre-declared residuals (class E).

---

## 22. Acceptance Criteria (for a future production verifier; not for this document)

1. Every class A, B and C requirement has a passing automated check (unit, integration, or matrix row).
2. Every class D requirement has been validated by its matrix row(s) on the target host, or re-classified by the Scientific Review.
3. Every class E item is either resolved by research, or recorded as an **accepted residual** in the freeze record, with its consequence for A2 and M9 stated.
4. The full adversarial matrix (§21) passes, with benign controls.
5. Admission of at least the pilot corpus is complete, with every admitted task's TaskSpec digest recorded.
6. All frozen gates pass: `ruff check`, `ruff format --check`, `mypy src tests`, `pytest -q`, run in the no-cache container (unchanged project gate).
7. The frozen-contract resolutions of §24 are ratified as DECISIONS entries **before** implementation begins.

## 23. Open Questions

| ID | Question | Class |
|---|---|---|
| OQ-1 | Execution placement AR-2 / AR-3 / AR-5 (with or without AR-6), and how D19 and M0 §6 are amended. | Decision (FD-1) |
| OQ-2 | The exact definition of "test root" for T-2 (directory vs subtree; tests outside declared roots). | E / D |
| OQ-3 | Treatment of `skipped` for P2P at baseline, and for F2P/P2P in candidate runs. | Decision |
| OQ-4 | Do deterministic, candidate-only infrastructure faults without a trusted-channel trace exist on the target host? | E |
| OQ-5 | Statistical adequacy of R_b, R_g (admission) and R_c (confirmation) against flakiness rates that are unknown. | E |
| OQ-6 | For non-reproduced anomalies, is the "first complete run" nominal state appropriate for the M9 endpoint, or does it bias arms that trigger more anomalies? | E |
| OQ-7 | `TEST_INTEGRITY_FAILURE` after restore: design defect (raise) or candidate-attributed (`FAILED`)? | Decision |
| OQ-8 | Is canary-based detection effective against the forgery classes seen [S:E4, E11b], and at what false-positive rate on benign tasks? | D |
| OQ-9 | Should static patch screening affect verdicts, be record-only, or be absent? | E |
| OQ-10 | Is a non-root user and read-only root filesystem compatible with the SWE-bench image family at scale? | D |
| OQ-11 | Real-task secondary suite (D21 model-gap signal): none (`secondary_passed=None`, A2 admits uncontradicted `PASSED`), or a defined held-out test set? | Decision / E |
| OQ-12 | Proposer-side leakage (future git history, upstream lookup; Appendix C [5][6]). Outside the verifier boundary, but it contaminates the evaluation the verifier serves. | Out of scope; flagged |
| OQ-13 | Does verifier-*implementation* identity belong in evaluation identity (F-12), or only the verification contract? | E |

### 23.1 Decisions that must be frozen before implementation (FD register)

| ID | Decision | Depends on |
|---|---|---|
| **FD-1** | Execution placement and the amendment of D19 (and M0 §6 if AR-2) | CX-1, CX-2 — **STOP item** |
| FD-2 | Infra outcomes are raised, never returned as `INFRA_ERROR` by the production verifier | §4.3, §14.1 |
| FD-3 | Accept "exhausted infra retry → evaluation VOID" under frozen M8, or amend M8 for per-task infra handling | CX-5 |
| FD-4 | Attribution rule (§14.4) and the value of R_c | OQ-4, OQ-5 |
| FD-5 | Timeout semantics and budget formula (PV-RSRC-002/003) | Exp. 2 |
| FD-6 | Resource-exhaustion semantics (PV-RSRC-004/005) | Exp. 3 |
| FD-7 | Test-integrity mechanism (T-2 / T-3 / T-4) and the protected-surface rule (§10.1) | Exp. 7, 8, 11; OQ-2 |
| FD-8 | Runner invocation, config and import-mode policy (PV-RUN-001…006) | Exp. 4, 8, 11, 12; X-4 |
| FD-9 | Result-channel rule (PV-RES-001), canaries, static screening, and **explicit acceptance of PV-SCI-004's residual** | Exp. 5, 6; OQ-8, OQ-9 |
| FD-10 | TaskSpec transport: amend `Task`, or have the verifier resolve a content-addressed TaskSpec from the adapter; bind the TaskSpec digest into `CorpusTask.material` | CX-3, CX-6 |
| FD-11 | Provenance link for M8 records (ledger vs amendment) | CX-7 |
| FD-12 | Admission gate: criteria, R_b/R_g, exclusions (zero-P2P, disagreeing invocations) | §8.2 |
| FD-13 | Status of the legacy in-container path (F-6): production prohibition only, or also remediation of compose/Dockerfile | CX-8 |
| FD-14 | Baseline cadence: per-candidate (RS-1) vs admission + sentinel (RS-2) | §6.2 |
| FD-15 | Real-task secondary suite | OQ-11 |
| FD-16 | Non-root / read-only / hardened runtime as requirements vs recorded options | OQ-10 |

---

## 24. Frozen-Contract Compatibility

| ID | Frozen contract | Tension / contradiction | Severity | Disposition (not resolved here) |
|---|---|---|---|---|
| **CX-1** | **D19** (`DECISIONS.md:376`): single container; "a `--network none` sidecar (reintroduces a second container and a Docker-socket dependency, contradicting the single-container model)" is an *alternative rejected* | Every real-task placement (AR-2/3/5) needs a second container per run; AR-3/5 need a socket or runtime dependency. | **Contradiction — STOP** | Superseding DECISIONS entry per the amendment procedure (`:479`), citing the M2 feasibility evidence. |
| **CX-2** | **M0 §6** (`M0_SPEC.md:120`) and PROJECT_STATE:127: "host … never as the source of truth for a verdict" | AR-2 computes the verdict in a host-side orchestrator. (AR-3/5 preserve it, but at the security cost in §6.1.) | **Contradiction under AR-2 — STOP if AR-2 is chosen** | Amend M0 §6's scope, or choose AR-3/5. |
| CX-3 | `Task` (`task.py:45-61`, `extra="forbid"`) | Cannot carry a TaskSpec (F-10). M2 set a precedent by adding an optional field (`secondary_test_command`, M2_SPEC §5). | Gap | FD-10: additive optional field (amendment) vs verifier-side resolution by `task_id` / handle (no amendment). |
| CX-4 | `VerdictState` closed (D16.7, D17) | Required semantics are expressible without new states (§14.1). | **Compatible** | Reason codes live in `output` / evidence only. |
| CX-5 | M8 runner (`evaluation/runner.py:76`) and M9 §3.5.1 (incomplete run → VOID) | Raised infra faults VOID the whole evaluation. Returning `INFRA_ERROR` instead would be scored 0 (biased). | Operational liability, not a contradiction | FD-3. |
| CX-6 | M8 `EvaluationProvenance` (F-12) | No verifier or environment identity. | Gap | FD-10 option (a) keeps it frozen; OQ-13. |
| CX-7 | M8 `EvaluationRecord` (`record.py`, `extra="forbid"`, no output field) | No provenance link for held-out measurements. | Gap | FD-11. |
| CX-8 | `docker-compose.yml` / `verifier.Dockerfile` (M0/M2 frozen config): root, `CAP_SYS_ADMIN`, episodes bind mount in the container that runs candidate code | Violates PV-SEC-001 for the *legacy* path. It is needed by frozen `VerifierSandbox` isolation tests. | Pre-existing risk (fixture-only path today) | FD-13. The production verifier must not inherit it. |
| CX-9 | D18 Level 4 via env pinning | `python -I` would silently break it [S:E2]. | Compatible if PV-RUN-002 holds | — |
| CX-10 | D17 / D21 `flaky` as provenance, excluded from hash; A2 excludes flaky | Used as the quarantine for non-reproduced anomalies (PV-ATTR-003). | **Compatible** (reuse) | OQ-6 on the M9 side. |
| CX-11 | D21 hash criterion for `verdict_output` | Reason codes and evidence digests in `output` must be reproducible. | Compatible with the constraint in §15 | — |
| CX-12 | Verifier protocols (`batch/runner.py:45`, `evaluation/attempt.py:62`) | A container verifier can implement `verify(task, patch) -> Verdict` structurally. | **Compatible** | — |
| CX-13 | Frozen `VerifierSandbox` behavior (timeout → `FAILED`, exit-code verdict, same-environment reruns) | The production verifier specifies different semantics (PV-RSRC-003, PV-RES-001, PV-CAND-001). These are implementation behaviors frozen by tests, not DECISIONS entries. | Divergence between two implementations of one protocol | A DECISIONS entry should record that the production verifier's semantics are authoritative for real tasks, and `VerifierSandbox` remains the fixture reference. |
| CX-14 | M9 endpoint ignores `secondary_passed` (F-8) | Makes primary integrity decisive (§4.3(4)). | Compatible; raises the bar | — |

**Contradictions requiring STOP:** CX-1 always; CX-2 if AR-2 is selected. Implementation cannot proceed until both have DECISIONS dispositions.

## 25. Implementation Handoff Requirements

A future handoff (not authorized by this document) must:

1. Reference the frozen PV specification version and the DECISIONS entries resolving CX-1, CX-2 (if applicable), and every FD item.
2. Implement behind the existing structural `Verifier` protocol, with no modification of `Task`, `Verdict`, `VerdictState`, `Episode`, M8, M9 or M10 unless an FD ruling amends them.
3. Deliver as atomic commits: (i) TaskSpec + admission; (ii) container execution; (iii) test-surface restoration; (iv) runner and result channel; (v) attribution and confirmation; (vi) provenance; (vii) adapter registration. Each commit carries its matrix rows.
4. Carry every matrix row (§21) as an automated test that runs against the real task image where the environment permits, and is capability-skipped with an explicit reason where it does not (the D19 CI precedent), never silently passed.
5. Keep the legacy `VerifierSandbox` untouched as the fixture reference, unless FD-13 rules otherwise.
6. Produce an evidence manifest and a freeze record for the pilot corpus, as M2 did.
7. Never write benchmark data into the repository.

---

## Appendix A — Sandbox research experiments (E0–E11)

**Environment:** Claude sandbox, Linux, **CPython 3.10.12**, **pytest 7.3.0** (same pytest as the flask-5014 image; Python differs: image has 3.11.10). No Docker; no task image. A venv stood in for the conda environment. Mock repository: `src/pkg/__init__.py` (`make(name) -> name`), `tests/conftest.py` (adds `src` to `sys.path`), `tests/test_x.py` with `test_must_fail` (asserts `make("a") == "b"`) and `test_ok`; `pyproject.toml` with `testpaths`. No `tests/__init__.py`. Nothing was written to any repository.

"Launcher" = `python /tmp/pvlab/trusted_launcher.py` containing `from pytest import console_main; sys.exit(console_main())`, located outside the mock repo.

| Exp | Candidate action | Invocation | Observed | Meaning |
|---|---|---|---|---|
| E0 | none | launcher | exit 1; `test_must_fail` failed, `test_ok` passed | Control. |
| E1a | adds repo-root `pytest.py` printing a marker and `sys.exit(0)` | `python -m pytest` | marker printed, **exit 0**, no JUnit | L4 confirmed: the working directory shadows pytest. |
| E1b | same | `python -I -m pytest` | exit 1, honest results | Isolated mode defeats it. |
| E1c | same | console entry point | exit 1, honest results | Defeats it. |
| E1d | same | launcher | exit 1, honest results | Defeats it. |
| E2 | — | `PYTHONHASHSEED=0 python -I -c "print(hash('velith'))"` ×2 | two **different** hashes; without `-I` identical | `-I` ignores `PYTHONHASHSEED` → breaks D18. |
| E1e | — | `PYTHONHASHSEED=0` without `-I` ×2 | identical hashes | Launcher form keeps D18. |
| E3 | adds `tests/pkg.py` (`make` returns `"b"`) | launcher | `test_must_fail` **passed**, `test_ok` failed | Test-directory shadowing of the code under test (not blocked by M2's config-name removal). |
| E3b | same | launcher `--import-mode=importlib` | honest results | Import mode blocks it. |
| E4 | appends 8 lines to **its own `src/pkg/__init__.py`**, patching `_pytest.reports.TestReport.__init__` to force `outcome="passed"` | launcher | **exit 0, "2 passed", JUnit all passed** | In-process forgery from candidate source; no config or conftest involved. |
| E5 | `atexit` handler in candidate source rewrites the JUnit file | launcher | exit 1, summary "1 failed, 1 passed", **JUnit all passed** | Post-write forgery; detectable by channel cross-consistency. |
| E6 | `os._exit(0)` at import of candidate module | launcher | **exit 0**, no JUnit | Exit-code-only verdict (F-1) says PASSED. |
| E7 | candidate source writes `zz_candidate.pth` into the env's `site-packages` | launcher, then an honest `python -I -c pass` | the later honest interpreter printed the candidate's marker | Persistence across runs in a writable env, even under `-I`. |
| E8 | adds `tests/pytest.ini` with `addopts = -k test_ok` | launcher | `configfile: pytest.ini`, rootdir `tests/`, "1 passed, 1 deselected", exit 0 | Nested config selected; deselection. |
| E8b | same | launcher `-c <trusted copy> --rootdir <repo>` | trusted config used, "1 failed, 1 passed" | Explicit trusted config overrides discovery. |
| E9 | adds repo-root `sitecustomize.py` | `-m pytest` and launcher | not imported in either | Negative result (3.10). |
| E10 | candidate source spawns a detached `sh -c 'sleep 2; echo … > late.txt'` | launcher | file absent at pytest exit, **present 3 s later** | Candidate processes outlive the test run. |
| E11 | E0, E4, E5 under a launcher with `sys.addaudithook` watching `object.__setattr__` on `_pytest` types and writes to the report path | audit launcher | identical event lists for E0 and E4; E4 forgery **not observed** | Naive audit hook ineffective. |
| E11b | patches module function `_pytest.runner.call_and_report` from candidate source | audit launcher | "2 passed", JUnit all passed, not observed | Second forgery variant, also undetected. |
| E11c | direct check: `A.__init__ = …`, `A.foo = 1`, `TestReport.__init__ = …` under an audit hook | plain | **no** `object.__setattr__` events for these; events only for `__doc__`/`__module__`/`__qualname__`/`__name__`/`__defaults__` | Class monkey-patching is invisible to audit hooks on 3.10. |

Not tested in the sandbox: `-P`/`PYTHONSAFEPATH` (needs 3.11); any container or runtime behavior; conda activation; SWE-bench images.

## Appendix B — Limitation analysis (frozen numbering; L13 added)

| L | Limitation (FREEZE_RECORD §7) | Status after this research | Addressed by | Residual class |
|---|---|---|---|---|
| L1 | Candidate-only faults | Mechanism proposed: trusted-channel attribution plus confirmation re-runs plus `flaky` quarantine | PV-ATTR-001…005, §14.4 | E (OQ-4), D (R_c) |
| L2 | Timeout / OOM not ruled | Semantics proposed (reproduced candidate-only → `FAILED`; trusted-channel host fault → raise) | PV-RSRC-002…007 | D (detection on WSL2) |
| L3 | Code manipulating pytest during test execution | **Split.** File-level: controllable (§10.1–10.3). In-process: shown unpreventable [S:E4, E11b]; blanket form detectable by canaries | PV-TEST-*, PV-RES-*, PV-SCI-004 | E (targeted forgery) |
| L4 | Import-path hijacking | Confirmed [S:E1a]; controls identified [S:E1b–d]; `-I` rejected [S:E2]; test-dir variant found [S:E3] | PV-RUN-001…004 | D (in-image validation; 3.11 `-P`) |
| L5 | Protected-set rule | A rule replaces the list (§10.1) | PV-TEST-001…005 | E/D (OQ-2) |
| L6 | Harness fidelity | Per-task admission comparison of invocations and import modes | PV-ENV-007, PV-RUN-004, X-4 | D |
| L7 | Tampering control (mock only) | Re-specified as real-image matrix rows 5, 7, 8 with benign controls | §21 | D |
| L8 | Untested verdict paths | Matrix rows 15 (P2P variant), 17, X-1, 2, 3 | §21 | D |
| L9 | Weak determinism evidence | Admission R-run identity plus two-host replay | PV-DET-*, PV-REPRO-002 | D |
| L10 | Scope (one task, pytest, zero-P2P) | Admission gate; zero-P2P excluded; pytest-only claim | PV-ADM-*, PV-BASE-004, PV-SCI-007 | C (stated scope) |
| L11 | Trusted labels | Labels validated at admission | PV-ADM-003, PV-SCI-006 | C |
| L12 | Self-reported evidence | Channel labelling; time-of-trust rule; cross-consistency | §5.2–5.3, PV-PROV-002, PV-RES-001 | E (in-process) |
| **L13** | **Provenance gaps in frozen M8 (F-11, F-12)** — *new; corresponds to the brief's "L12 provenance limitations"* | Options without amendment identified | PV-PROV-004…006 | Decision (FD-10, FD-11), E (OQ-13) |

**Brief ↔ record mapping:** brief L7 "self-reported evidence markers" = record **L12**; brief L12 "provenance limitations" = this report's **L13**; record L7 "tampering control" is not in the brief's list and is retained above.

## Appendix C — External sources

1. SWE-bench harness, `swebench/harness/test_spec/python.py` (main branch, fetched 2026-09-25). The eval script resets only the files in the test patch (`git checkout {base_commit} <modified>` / `rm -f <new>`), applies the test patch, runs `test_cmd` + directives under `conda activate`, and reverts the test files afterwards. The repo-setup script `chmod -R 777`s the repo "so nonroot user can run tests", and strips remotes and future tags. https://raw.githubusercontent.com/SWE-bench/SWE-bench/main/swebench/harness/test_spec/python.py
2. Python documentation, command line and environment: `-I` implies `-E -P -s` and ignores all `PYTHON*` variables; `-P` / `PYTHONSAFEPATH` added in 3.11; `python -m` prepends the current working directory unless `-P`. https://docs.python.org/3/using/cmdline.html
3. SWE-bench issue #465, "Repo State Loopholes During Agentic Evaluation". https://github.com/SWE-bench/SWE-bench/issues/465
4. Scale AI SWE-bench Pro issue #93, "Git Reward Hacking in SWEBench Pro OSS". https://github.com/scaleapi/SWE-bench_Pro-os/issues/93
5. "SWE-Bench Pro Verified: A Reliable Benchmark for Software Engineering Agents" (arXiv 2609.08149). Reports agents mining bundled `.git` history and upstream fixes. https://arxiv.org/abs/2609.08149
6. Cursor, "Reward hacking is swamping model intelligence gains". https://cursor.com/blog/reward-hacking-coding-benchmarks

Sources 3–6 are search results used only for OQ-12 (proposer-side leakage). They were **not** used to support any verifier requirement, and their specific figures were not independently verified.

*End of M2-PV specification research report — DRAFT for Scientific Review.*
