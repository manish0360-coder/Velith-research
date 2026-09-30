# M2-PV — Implementation Handoff

## 1. Status

**BLOCKED for the requested full scope** (production verifier C1–C5, C8, C9). **One separable sub-scope is implementation-ready without contradiction:** the D29 identity-v2 migration, Track I (§27).

The two blocking contradictions are in §29 (BC-1, BC-2). Following the Phase-14 rule, **no workaround is invented**: the blocked units are specified only to the extent that frozen decisions determine them, and every undecided parameter is listed, not chosen.

This document authorizes nothing. It changes no repository artifact. Nothing in it has been executed; every test listed is a requirement, not evidence.

## 2. Baseline commit

- **Engineering repo:** `E:\Projects\OpenSourceLab\repos\Velith`.
- **HEAD = origin/main:** `1b0b7a09a41299ade38027cd17215fa42c2a7b09`, "docs(governance): freeze M8 identity v2 and M9 VM2".
- **Tags at HEAD:** `m8-identity-v2-frozen`, `m9-spec-frozen-oed7-vm2`.
- **Working tree:** clean at inspection.
- **Changes since `b14d918`:** exactly `docs/DECISIONS.md`, `docs/M8_IDENTITY_V2_SPEC.md`, `docs/M9_SPEC.md`.

**Frozen document hashes at HEAD:**

| File | SHA-256 |
|---|---|
| `docs/DECISIONS.md` | `47cc1e1c0ae31da0ce7497eef041ece93d89f02d4e1df02e0f2fcaa42b383706` |
| `docs/M8_IDENTITY_V2_SPEC.md` | `746be5770993b51ad22f71a217f3108aeeab910d73f288dcf811132df4f5285a` |
| `docs/M9_SPEC.md` | `94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e` |
| `docs/M8_SPEC.md` | `9ddd16d881d7a6123897859ede95d719a8c123ba06b9a6c5337e41bd5db1c093` |

**Research inputs** (`Velith-research`), content-addressed:

| Input | SHA-256 |
|---|---|
| M2-PV production verifier spec (**DRAFT**) | `dcecb46b0fd2100ddd30b7659aa76abedf3379c1d0af8501a5b32a46baf17c62` |
| Reconciliation review | `ce6cf7f42f1bd791238fb271982a2199581f7fe8b23f057fa71e4a816be8425d` |
| M2-PV-R ratification record | `84d67088792739cb972238666595458c0a6d41ff86bc5755d7c51ce7cb93d13a` |
| M2-PV-R3 identity spec | `d2c51ec15aa00f1c5924ea6aaed8e6de3f7ba286bfc27b5860b5d792b375888a` |

The M2 freeze record is `experiments/m2_container_prototype/FREEZE_RECORD.md` (probe `560834d5…`, evidence manifest `30c59a45…`).

## 3. Governing frozen decisions

| Decision | Status | Relevance |
|---|---|---|
| **D26** (`DECISIONS.md`) | Frozen | AR-2 execution boundary and mandatory constraints. **Leaves undecided:** runner mechanics; R_b, R_g, R_c; limit values; non-root, read-only-root and hardened runtime; protected-surface policy; TaskSpec schema (`DECISIONS.md:523`) |
| **D27** | Frozen | Evidence / classification / orchestration separation; hash-locked classifier requirements |
| **D28** | Frozen | Option D TaskSpec transport, D-1 to D-4 |
| **D29** | Frozen | M8 evaluation identity v2 |
| **M8 Identity v2** (`docs/M8_IDENTITY_V2_SPEC.md`) | Frozen, tag `m8-identity-v2-frozen` | Identity plumbing, VerificationManifest, M9/M10 reconstruction, 18 acceptance cases |
| **M9 VM2** (`docs/M9_SPEC.md`) | Frozen, tag `m9-spec-frozen-oed7-vm2` | `verification_manifest_hash` in pre-registration; statistics unchanged |
| **D8, D16.7, D17, D18, D19, D21** | Frozen | Held-out lock; verdict taxonomy; `flaky`; determinism; legacy verifier; secondary suite |
| **Ratified at M2-PV-R** (research record, not in `DECISIONS.md`) | RD-ratified | E12/E13 residuals; D21 real-task residual; **sequencing: architecture ratification → 5-task pilot → M2-PV production verifier automation** |

## 4. Scope

1. **Track I — identity-v2 migration (implementation-ready).** Coordinated M8/M9/M10 identity plumbing exactly as frozen in `docs/M8_IDENTITY_V2_SPEC.md` and M9 VM2.
2. **Track III — production verifier (BLOCKED; §29).** Specified only to the extent frozen D26/D27/D28 determine it; undecided parameters are listed.
3. **Track II — 5-task pilot.** Referenced for sequencing only. Its design gate is separate, and it runs on the frozen M2 probe, not on the production verifier.

## 5. Non-goals

- No change to M9 statistics, M8 v1, M0–M7 contracts or D26–D29.
- No new verdict state.
- No TaskSpec schema decision, no R-values, no limit values, no protected-surface rule, no runner mechanics, no canary design (all D26-undecided).
- No pilot execution.
- No available-task lineage (deferred, not solved).

## 6. Current architecture inventory (actual paths and interfaces at HEAD)

| Component | Path:line | Interface (actual) |
|---|---|---|
| Legacy verifier | `src/velith/harness/verifier_sandbox.py:140` | `VerifierSandbox.verify(task, patch) -> Verdict`; `Verdict` (`:120`): `state, output, secondary_passed, flaky, duration_seconds`; `SandboxExecutionError` (`:111`) |
| Verifier protocol (M5) | `src/velith/batch/runner.py:45` | `Verifier.verify(self, task: Task, patch: str) -> Verdict` |
| Verifier protocol (M8) | `src/velith/evaluation/attempt.py:62` | Same shape |
| Verdict taxonomy | `src/velith/episodes/episode.py:39` | `PASSED, FAILED, PATCH_APPLY_FAILED, NO_PATCH, INFRA_ERROR` |
| Task | `src/velith/task.py:45` | `task_id, repo_path, prompt, hidden_test_command, secondary_test_command`; `frozen`, `extra="forbid"` |
| Corpus task / loader | `src/velith/corpus/loader.py:35`, `:69` | `CorpusTask(label, material, handle, partition)`, `.identity`; `load_corpus(corpus_path, partition_spec_path) -> LoadedCorpus` |
| Adapter seam | `src/velith/batch/adapter.py:26`, `:34` | `TaskAdapter.materialize(corpus_task) -> Task`; `FixtureTaskAdapter` |
| M5 batch | `src/velith/batch/runner.py:53` | `run_batch(corpus, provenance, *, proposer, verifier, writer, adapter, guard, velith_version) -> list[Episode]` |
| M6 retrieval | `src/velith/retrieval/{query,retriever}.py` | Query = `CorpusTask.material` (`evaluation/attempt.py:125`); episode text = `episode.prompt` (`retriever.py:27`) |
| M7 arms | `src/velith/arms/filters.py` | A2 admits non-flaky `PASSED` (secondary not `False`) and non-flaky `FAILED` |
| M8 held-out set | `src/velith/evaluation/heldout_set.py:27`, `:45` | `HeldOutEvaluationSet(tasks, manifest_hash)`; `load_heldout_set(...)` |
| M8 runner | `src/velith/evaluation/runner.py:41`, `:55` | `_require_consistent(provenance, checkpoint, heldout_set)`; `run_heldout_evaluation(checkpoint, heldout_set, provenance, *, attempt, sink, guard) -> tuple[EvaluationRecord, ...]`. **Callers: tests only** (10 call sites in 3 test files) |
| M8 provenance (v1) | `src/velith/evaluation/provenance.py:27` | `EvaluationProvenance`: 8 fields; `to_dict()`, `.identity` |
| M8 record / sink | `src/velith/evaluation/record.py`, `sink.py:25` | `EvaluationRecord(evaluation_identity, …)`; `EvaluationSink.append / read_all` |
| M9 pre-registration | `src/velith/analysis/preregistration.py:69` | `PreRegistration` (20 fields + `identity`); `SPEC_VERSION = "m9-spec-frozen-oed7"` (`:32`); `build(...)` |
| M9 store | `src/velith/analysis/prereg_store.py:20` | `PreRegistrationStore.write / read` (write-once, integrity on read) |
| M9 statistics | `src/velith/analysis/{completeness,decision,emm,encoding,gee,holm,mcnemar,trend,wald}.py` | **Must remain byte-identical** |
| M10 binder | `src/velith/analysis/binder.py:74`, `:88`, `:121` | `_provenance_identity`, `_expected_identities`, `bind_observations` |
| M10 executor | `src/velith/analysis/executor.py:111`, `:127`, `:174`, `:300` | `_provenance_identity`, `expected_evaluation_identities`, `run_preflight`, `run_m10_analysis(*, preregistration, evaluation_sink, results_dir, a0_checkpoint_identity, task_identities, evaluation_run_complete)` |
| M10 result | `src/velith/analysis/result_record.py` | `AnalysisProvenance` / `AnalysisResultRecord` (no change; Q-F) |
| Container config | `docker-compose.yml`, `docker/verifier.Dockerfile` | Single `verifier` service; `cap_add: SYS_ADMIN`; episodes bind mount; `python:3.12.7-slim-bookworm`; no `USER` |
| Pins | `pyproject.toml`, `constraints/analysis-py312.txt` | `requires-python ==3.12.*`; ruff 0.6.9; `statsmodels==0.15.0` + 45-line constraints |
| M2 prototype | `experiments/m2_container_prototype/{probe.py,FREEZE_RECORD.md}` | Frozen evidence |
| Tests | `tests/unit` (47), `tests/integration` (10), fixtures | Identity-relevant tests listed in §24 |

## 7. Target architecture

The ratified target (D26–D28) is unchanged:

```
CorpusTask.handle → TaskSpec registry → real-task adapter → Task
    → trusted host orchestrator → digest-pinned containers (baseline / candidate / reruns)
    → evidence → hash-locked classifier → Verdict
    → Episode / EvaluationRecord (evaluation_identity v2 ⊇ verification_manifest_hash)
```

Track I implements only the identity arm (VerificationManifest → M8/M9/M10). Track III implements the execution arm after its gates (§29).

## 8. Trust model (ratified; D26/D27)

- **Trusted:** verifier orchestrator; trusted runner artifacts; TaskSpec registry; VerificationManifest; evidence collector; classifier (hash-locked environment); pinned runtime identity; repository state outside candidate execution.
- **Trusted environment:** the admitted, digest-pinned task image, before candidate code runs.
- **Untrusted:** the candidate patch and process; candidate-created files and processes; candidate stdout, JUnit and results; candidate runtime behavior.

**Rule: trust in candidate-container state ends when candidate execution begins.** Candidate-produced evidence may lower a verdict. It supports `PASSED` only through integrity checks that are **not yet frozen** (BC-2), and then only subject to RS-1 and RS-2.

## 9. Execution boundary (D26; frozen constraints — implementation-ready as *requirements*, parameters undecided)

**Mandatory, decided by D26:**
- verify digest and platform before execution;
- fresh container per execution;
- `--network none`, `--cap-drop ALL`, `--security-opt no-new-privileges`;
- bounded memory (swap disabled), CPU, PIDs, wall time, and disk/output where supported;
- no privileged mode, no Docker socket, no DinD, no host mounts;
- no install, build or network at verification time;
- no candidate access to trusted stores;
- **fail closed** (`SandboxExecutionError`) if a constraint cannot be applied or verified;
- classification only through the D27 classifier environment.

**Undecided (D26):** limit **values**; non-root, read-only-root and hardened runtime. → Track III gate.

## 10. TaskSpec / D28

| Condition | Frozen requirement | Implementation locus | Status |
|---|---|---|---|
| D-1 | `task_id` spec-independent and stable | Real-task adapter | Specified; TaskSpec schema **undecided** |
| D-2 | `prompt` is a pure function of `CorpusTask.material`; TaskSpec content never enters `material` or `prompt` | Real-task adapter | Specified |
| D-3 | Static guard: real-task `Task` never reaches legacy `VerifierSandbox` | **Composition code and wiring test**; `verifier_sandbox.py` is frozen and not edited | Specified (B) |
| D-4 | `repo_path` = verified TaskSpec bundle, "the source bundle copied by the verifier" | Real-task adapter + container verifier | Specified |

**Not modified:** task-identity semantics, `material`, retrieval.

**Track I needs no TaskSpec schema.** VerificationManifest checks require only a **content-addressed byte store**: digest = SHA-256 of the stored bytes; "missing" means absent; "mismatch" means the re-hash differs.

## 11. VerificationManifest (frozen; M8 Identity v2 §3) — Track I

- **Population:** held-out only (the `HeldOutEvaluationSet` tasks).
- **Mapping:** `task_identity → CorpusTask.handle` (TaskSpec digest).
- **Canonical form:** `compute_content_hash(VM)` (`episodes/episode.py`): sorted keys, `(",", ":")`, `ensure_ascii=False`, UTF-8, SHA-256 lowercase hex.
- **`VerificationManifestError` on:** empty population; any duplicate task identity (same or different digest); missing TaskSpec; digest not `^[0-9a-f]{64}$`; stored bytes do not re-hash to the digest.

## 12. Baseline admission — Track III (BLOCKED)

**Frozen:** a baseline container never receives candidate code; an unhealthy baseline raises and is never a candidate verdict (M2 evidence, class A).

**Undecided:** R_b, R_g; admission criteria; baseline cadence (FD-12, FD-14: CSE/SRC-accepted, **not RD-ratified**).

## 13. Candidate execution — Track III (BLOCKED)

**Frozen:** a fresh container per execution; outputs are collected only after full teardown.

**Undecided:** runner mechanics; rerun count R_c; timeout and memory values.

## 14. Test integrity — Track III (BLOCKED)

**Protected-surface policy is undecided (D26).** The M2 prototype's listed-file restoration is class-A evidence for flask-5014 only.

## 15. Runner integrity — Track III (BLOCKED)

**Runner mechanics are undecided (D26).**
- **Sandbox evidence** (research, not frozen): `python -m pytest` shadowing; `-I` defeats `PYTHONHASHSEED` (so it conflicts with D18); a trusted launcher; explicit `-c`.
- **Import mode:** per-task validation required.

## 16. Result / evidence channel — Track III (BLOCKED)

**Frozen:** candidate-channel evidence is untrusted (D26 trust boundary); residuals E12/E13 are accepted.

**Undecided:** the result-consistency rule, canary design, and static screening (FD-9: not RD-ratified).

## 17. Verdict classifier — Track III (BLOCKED)

**Frozen (D27):**
- clean git tree, exact lock, self-verified identity;
- refuse evaluation-of-record execution if identity cannot be verified;
- explicit inputs only; no ambient state;
- classifier identity recorded in evidence;
- deterministic mapping.

**Frozen taxonomy:** no new `VerdictState` (D17).

**Undecided:** attribution rules and R_c.

## 18. Anti-VOID — Track III (BLOCKED on parameters)

**Invariant (RD):** a candidate must not be able to force an infrastructure condition that VOIDs an evaluation.

**Frozen consequences:**
- Infrastructure faults are raised (`SandboxExecutionError`).
- Frozen M8 has no per-task infra handling, so an exhausted infra retry aborts the run → VOID (M9 §3.5.1).

**Therefore the invariant depends on:**
- (a) candidate-attributed classification of every post-trust-boundary anomaly;
- (b) bounding every shared resource the candidate could exhaust to induce a trusted-channel fault (disk, log volume, VM memory, PIDs).

Rules (a) and (b) and their R-values are **undecided** (reconciliation AV-1 to AV-6: research, not ratified). **Residual RS-3 remains.**

## 19. Resource controls — Track III (BLOCKED)

Bounded memory (swap off), CPU, PIDs, time, and disk/output where supported are frozen as requirements. **Values are undecided.**

## 20. Network / isolation controls

Frozen and implementable as requirements (§9). Class-A evidence covers `--network none` for one task only. DNS, IPv6 and host-published ports are unprobed.

## 21. Provenance

- **Frozen (D27):** classifier identity is recorded in verification evidence.
- **Frozen (D29):** one classifier identity per evaluation of record, enforced through the evidence ledger.
- **Undecided:** the evidence-ledger schema and the `verdict_output` evidence digest (PV-PROV-004 not frozen; it relates to deferred available-task lineage).

## 22. M8 Identity v2 — Track I (implementation-ready)

| Item | Requirement (frozen) |
|---|---|
| `EvaluationProvenance` (`evaluation/provenance.py`) | Payload of exactly 10 keys: `identity_version="m8-evaluation-identity-v2"`, `checkpoint_identity`, `manifest_hash`, `arm`, `base_model`, `eval_seed`, `max_tasks`, `max_attempts_per_task`, `max_tokens`, `verification_manifest_hash` (64-hex). Same canonical hash rule. `manifest_hash` not renamed. |
| VerificationManifest builder (**new module**, proposed `src/velith/evaluation/verification_manifest.py`) | §11 rules; reuses `compute_content_hash`; defines `VerificationManifestError` and a `TaskSpecStore` protocol (`read(digest) -> bytes | None`) |
| Content-addressed TaskSpec store (**new module**, proposed `src/velith/taskspec/store.py`) | Schema-agnostic byte store keyed by SHA-256; re-hash on read. **No TaskSpec schema.** |
| M8 runner (`evaluation/runner.py`) | `_require_consistent` adds: `identity_version` check; VM hash recomputed from the held-out set and compared **before any attempt**; no partial record. `run_heldout_evaluation` gains a required TaskSpec-store input; callers are tests only. |
| `EvaluationRecord` | **Unchanged** |
| Fixtures (Q-C) | `tests/fixtures/corpus_min/corpus.json` handles become deterministic synthetic 64-hex digests, with matching fixture blobs in a fixture store (test data only). M4 tests using opaque handles (`"h"`, `"opaque-…"`) are unaffected: they never build a VM. |

## 23. M9 VM2 — Track I (implementation-ready)

**`analysis/preregistration.py` changes:**
- `SPEC_VERSION = "m9-spec-frozen-oed7-vm2"`;
- add field `verification_manifest_hash` with the 64-hex validator;
- `build(..., verification_manifest_hash=...)`, required;
- the identity remains `compute_content_hash(all fields minus identity)`.

**Unchanged — must stay byte-identical:** `completeness.py`, `decision.py`, `emm.py`, `encoding.py`, `gee.py`, `holm.py`, `mcnemar.py`, `trend.py`, `wald.py`. That covers GEE, EMM, Wald, McNemar, Holm, the K = 1 and K > 1 decisions, OED-7, complete-case handling and VOID semantics.

**STOP rule:** any pressure to change a statistical module is a contradiction to report, not implement.

## 24. M10 integration — Track I (implementation-ready)

**Reconstruction sites (whole-repository search):** `binder.py:74` (`_provenance_identity`) and `executor.py:111` (`_provenance_identity`). There are no others in `src/`.

| Stage | Requirement |
|---|---|
| Construction | Both sites pass `verification_manifest_hash=preregistration.verification_manifest_hash` and build v2 provenance. **Same commit.** |
| Pre-flight (`run_preflight`, `:174`) | Refuse `spec_version != "m9-spec-frozen-oed7-vm2"`; `verify_identity()` as before |
| Validation | `_verify_records_resolve` unchanged: a v1 identity is not in the v2 expected set → `ExecutionError` |
| Failure | Loud `ExecutionError` / `BinderError`; no result record |
| Migration | None (no real artifacts exist; verified at `b14d918`). v1 remains historical at `b14d918`. |

**Tests to update (no assertion weakened):**
- constructing `EvaluationProvenance`: `tests/integration/test_m10_heldout_execution.py`, `test_m8_heldout_evaluation.py`, `test_m9_analysis_pipeline.py`; `tests/unit/test_analysis_binder.py`, `test_analysis_executor.py`, `test_evaluation_heldout_safety_invariant.py`, `test_evaluation_provenance.py`, `test_evaluation_runner.py`;
- constructing `PreRegistration`: `tests/integration/test_m10_heldout_execution.py`, `test_m9_analysis_pipeline.py`; `tests/unit/test_analysis_binder.py`, `test_analysis_executor.py`, `test_analysis_prereg_store.py`, `test_analysis_preregistration.py`, `test_analysis_result_record.py`.

**New tests:** VM builder rejection rows; the 18 identity cases (M8 Identity v2 §12) as acceptance tests; a statistics-byte-identity test (SHA-256 of the nine statistics modules vs `1b0b7a0`).

## 25. Residual risks

| RS | Mitigation implemented (by track) | Residual | Acceptance evidence required | NOT proven |
|---|---|---|---|---|
| RS-1 result-channel forgery | Track III: trusted collection after teardown; consistency and canary rules **undecided** | Targeted, channel-consistent forgery (E12b, E13b) | Matrix groups 6–7 with benign controls | Absence of forgery |
| RS-2 semantic manipulation | None available (E12c) | Test-aware special-casing | Documented only | Semantic correctness |
| RS-3 deterministic candidate-only infra faults | Track III attribution (undecided) | May be misattributed as `FAILED` | Group 21 | Their non-existence |
| RS-4 low-rate flakiness | Admission reruns (R undecided) plus `flaky` quarantine | Undetected below the rerun bound | Pilot/admission measurements | Flake-free tasks |
| RS-5 non-reproduced anomaly nominal state | D17 `flaky`; M9 nominal-state question open | Possible arm-correlated noise | — | Unbiasedness |
| RS-6 retrieval perturbation | **Mitigated by design:** D28 keeps `material`/`prompt` unchanged; Track I adds nothing to retrieval inputs | None known from transport | Test: retrieval inputs unchanged | — |
| RS-7 no real-task secondary suite | `secondary_passed=None` (ratified residual) | No D21 model-gap filter in A2 | Recorded in provenance (mechanism open) | Model-gap detection |
| RS-8 container escape | D26 constraints; hardened runtime optional (undecided) | Kernel/runtime vulnerabilities | Group 13–14 probes | Escape resistance |

## 26. Adversarial validation matrix (implementation test plan; not executed)

| # | Group | Attack | Expected observation → classification | Trusted evidence | Track | Provable by implementation? | Residual |
|---|---|---|---|---|---|---|---|
| 1 | Image identity | Wrong or retagged digest | Digest mismatch → raise before execution | Runtime inspect | III | Yes | — |
| 2 | Base commit | Image HEAD ≠ base | Raise | Pre-execution | III | Yes | — |
| 3 | Protected test surface | Edit/add tests, conftest | Neutralized per policy (**undecided**) | Pre-execution hash | III | After policy freeze | Out-of-surface tests |
| 4 | Runner shadowing | Repo-root `pytest.py`, test-dir modules | Runner not shadowed (mechanics **undecided**) | Runner identity | III | After runner freeze | Other import paths |
| 5 | Plugin/config manipulation | Nested `pytest.ini`, `pyproject` | Trusted config in force | Config hash | III | After runner freeze | Plugins reading repo files |
| 6 | Result forgery | `atexit` rewrite, `os._exit` | Inconsistency → `FAILED` (rule **undecided**) | Channel comparison | III | Partially | Consistent forgery |
| 7 | Targeted forgery | Per-nodeid report rewrite | Not reliably detected (E13b) | — | III | **No** | **RS-1** |
| 8 | Semantic manipulation | Caller-frame special-casing | Not detected (E12c) | — | III | **No** | **RS-2** |
| 9 | Timeout | Infinite loop | Reproduced → `FAILED` (values **undecided**) | Runtime | III | After values | Host contention |
| 10 | OOM | Allocate past limit | Reproduced → `FAILED` | Runtime `OOMKilled` | III | After values | WSL2 discrimination |
| 11 | Signal termination | Self-`SIGKILL`, collector kill | Candidate-attributed after confirmation | Runtime | III | After R_c | RS-3 |
| 12 | Network | TCP / DNS / IPv6 / host ports | Blocked; `NetworkMode=none` | Runtime + probe | III | Yes (TCP class-A for one task) | Unprobed channels until run |
| 13 | Process/container isolation | Detached process, `/proc` | No effect after teardown | Runtime | III | Yes | RS-8 |
| 14 | Host bind/socket | Access socket, host paths | Absent | Inspect | III | Yes | RS-8 |
| 15 | Rerun determinism | Repeat runs | Identical deterministic evidence | Evidence digest | III | Yes | Cross-host |
| 16 | Baseline integrity | Broken environment | Raise (`BASELINE_UNHEALTHY`) | Baseline channel | III | Yes | — |
| 17 | TaskSpec mismatch | Handle ≠ stored bytes | `VerificationManifestError` / fail closed | Store re-hash | **I** | Yes | — |
| 18 | VM mismatch | Provenance VM hash ≠ computed | `EvaluationError` before any attempt | Runner check | **I** | Yes | — |
| 19 | Identity mismatch | v1/v2 mixing; changed component | Reject / distinct identity (18 cases) | Hash inclusion | **I** | Yes (conditional on SHA-256) | Collision assumption |
| 20 | A2 contamination | Infra fault as `FAILED`; forged `PASSED` | Quarantine via `flaky` / raise | Classifier | III | Partially | RS-1, RS-2, RS-3 |
| 21 | Candidate-forced VOID | Exhaust shared resources | Candidate-attributed; never raise | Runtime + bounds | III | After AV rules | RS-3 |
| 22 | Flake handling | Nondeterministic test | `flaky=True`; excluded from A2 | Reruns | III | After R values | RS-4 |

## 27. Implementation milestones

**Evaluation of the proposed C1–C9 structure:**
- (i) **C6 and C7 must not be separate commits.** The frozen spec requires the M8, M9 and M10 identity changes as one atomic migration, with both reconstruction sites in one commit (`M8_IDENTITY_V2_SPEC.md` §8). They merge into **C-ID**.
- (ii) **C1–C5, C8 and C9 are blocked** (BC-1, BC-2).
- (iii) **The pilot precedes production automation** by ratified sequencing, and needs its own design gate, not C9.

| Milestone | Track | Status | Files / modules | Acceptance | Commit / rollback boundary |
|---|---|---|---|---|---|
| **C-ID** Identity-v2 migration | I | **Ready (no contradiction)** | `evaluation/provenance.py`, `evaluation/runner.py`, **new** `evaluation/verification_manifest.py`, **new** `taskspec/store.py`, `analysis/preregistration.py`, `analysis/binder.py`, `analysis/executor.py`; fixture data; the 11 distinct test files listed in §24 (8 + 7 listings, 4 overlapping) plus new tests | 18 identity cases; VM rejection rows; statistics-byte-identity; full gate (§28) | **One commit**; rollback = revert that commit (v1 reproducible at `1b0b7a0`) |
| Pilot design gate | II | Separate RD gate | Research workspace; frozen M2 probe reused **unmodified** | Pilot design ratified (P-1 to P-3 still pending RD) | No repository change |
| PV-freeze | III | Blocked | Freeze of the undecided D26 items plus FD-2/3/4/5/6/7/8/9/12/14/15/16, informed by pilot and validation-matrix evidence | M2-PV spec **FROZEN** | Docs only |
| C1–C5, C8 production verifier | III | Blocked until PV-freeze | Decomposition deferred to the frozen spec | — | — |

**Frozen artifacts that must stay unchanged in C-ID:**
- `docs/*` (all), `docs/M8_SPEC.md`, the nine statistics modules;
- `harness/verifier_sandbox.py`, `task.py`, `corpus/*`, `batch/*`, `retrieval/*`, `arms/*`;
- `evaluation/{attempt,checkpoint,context,heldout_set,record,sink}.py`, `analysis/{result_record,prereg_store}.py`;
- `docker/`, compose, `pyproject.toml`, `constraints/`, `experiments/`.

## 28. Verification gates (every milestone)

1. WSL + Docker.
2. `docker compose build --no-cache verifier`.
3. `ruff check .`, `ruff format --check .`, `mypy src tests`, `pytest -q` inside the container (pinned Ruff 0.6.9, pinned Python 3.12 and constraints).
4. Working-tree audit: exactly the milestone's declared paths.
5. Frozen-document hash verification (§2 table).
6. Statistics-module byte identity (C-ID).

No "works locally" acceptance; the commit only follows a green no-cache gate.

## 29. Contradiction audit

| ID | Finding | Class |
|---|---|---|
| **BC-1** | The requested milestones implement M2-PV production verifier automation (C1–C5, C8) **before** the 5-task pilot (C9 last). The RD-ratified M2-PV-R record fixes "architecture ratification → 5-task zero-experience base-rate pilot → M2-PV production verifier automation" (record line 272; status block line 403). | **D — blocking** |
| **BC-2** | Frozen D26 (`DECISIONS.md:523`) leaves runner mechanics, R_b/R_g/R_c, limit values, non-root/read-only/hardened runtime, protected-surface policy and the TaskSpec schema **undecided**. The M2-PV specification where they belong is **DRAFT**. Units E–R and V cannot be made implementation-ready without deciding them, which this handoff may not do. | **D — blocking** |
| C-1 | FD-2 (raise-only infra), FD-3 (VOID on exhausted retries), FD-13, FD-14, FD-15 were accepted by CSE and SRC but **never RD-ratified** | C — ratify before Track III |
| B-1 | `run_heldout_evaluation` gains a TaskSpec-store input (authorized by D29 / M8 v2 §7; callers are tests only) | B |
| B-2 | The VM needs a schema-agnostic content-addressed store; no TaskSpec schema needed (does not touch D26's undecided schema) | B |
| B-3 | Q-C fixture digests need matching fixture store blobs (test data) | B |
| B-4 | The D-3 guard lives in composition code and a wiring test; frozen `VerifierSandbox` is not edited | B |
| B-5 | The two M10 reconstruction sites change in one commit | B |
| A-1 | C-ID vs D29, M8 Identity v2, M9 VM2: consistent; M9 statistics untouched | A |
| A-2 | C-ID vs M0–M7 (retrieval inputs, task identity, arms): untouched | A |
| C-2 | Pre-existing: no `evaluation_run_complete` artifact or experience-accumulation orchestration for a real M8/M10 run (earlier audits). Outside this handoff. | C (future) |

**Result:** blocking contradictions BC-1 and BC-2 exist for the requested scope. **STOP for Track III.** Track I has none.

## 30. Definition of Done (C-ID only)

- 10-key v2 identity;
- VM builder with every rejection row;
- runner pre-attempt check;
- `SPEC_VERSION` bumped and field added;
- both M10 sites reconstructing v2;
- pre-flight `spec_version` check;
- 18 identity cases and VM rows as passing tests;
- statistics modules byte-identical;
- fixtures on the universal v2 path;
- all 11 listed test files updated without weakening;
- no-cache gate green;
- exactly the declared paths changed;
- frozen documents hash-identical;
- one commit.

## 31. Implementation authorization boundary

- This document authorizes **nothing**.
- C-ID requires an explicit RD implementation authorization.
- Track III requires the resolution of BC-1 (pilot first) and BC-2 (M2-PV specification freeze of the D26-undecided items plus the C-1 ratifications), then a new handoff.
- The pilot requires its own design gate.

## 32. NOT YET IMPLEMENTED

Everything is unimplemented:
- the identity-v2 migration;
- the VerificationManifest builder and TaskSpec store;
- the real-task adapter;
- the container orchestrator;
- baseline admission;
- candidate execution;
- the runner and result channel;
- the classifier and anti-VOID;
- the evidence ledger;
- the adversarial suite;
- the pilot.

No test in this document has been executed.

*End of M2-PV Implementation Handoff.*
