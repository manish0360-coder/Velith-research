# M2-PV-P1 — Real-Task 5-Task Pilot Design

## 1. Document status

**DESIGN (research workspace). Not executed. Not authorized for execution.**

**Execution is BLOCKED** until two things happen:
- **(a) PB-1 is resolved.** The frozen M2 probe cannot accept a proposer-generated candidate patch (§15). The minimum separate change is an experiment-only pilot harness that requires its own authorization.
- **(b) The RD resolves the OPEN decisions in §30.**

**Engineering baseline:** `5476d82ed080df38349af79ef05d18480f934cce` (C-ID, local; `origin/main` = `1b0b7a0`). **Date:** 2026-09-26.

**Requirement classification** (used on every requirement):
- **[FROZEN]** — frozen spec or decision;
- **[RATIFIED]** — RD-ratified;
- **[EXISTING]** — present in code at the baseline;
- **[PROPOSED]** — this design; needs RD acceptance;
- **[OPEN]** — undecided; RD decision required;
- **[EXT]** — requires external verification on the execution host.

## 2. Purpose

Answer one architectural question, and nothing else:

> **Can the current proposer produce usable patches on real software-engineering tasks under the proposed sealed-task execution architecture?**

This is a feasibility pilot. It is **not** a benchmark, not a solve-rate estimate, not evidence that the production verifier is complete, and not an A0/A1/A2 evaluation. It must not contaminate future held-out evaluation. [RATIFIED]

## 3. Authoritative inputs

**Research documents (content-addressed):**

| Input | SHA-256 |
|---|---|
| `M2-PV_PRODUCTION_VERIFIER_SPEC_RESEARCH.md` (DRAFT) | `dcecb46b0fd2100ddd30b7659aa76abedf3379c1d0af8501a5b32a46baf17c62` |
| `M2-PV_RECONCILIATION_REVIEW.md` | `ce6cf7f42f1bd791238fb271982a2199581f7fe8b23f057fa71e4a816be8425d` |
| `M2-PV-R_ARCHITECTURE_RATIFICATION_AMENDMENT.md` | `84d67088792739cb972238666595458c0a6d41ff86bc5755d7c51ce7cb93d13a` |
| `M2-PV_IMPLEMENTATION_HANDOFF.md` | `8d193f10ec672da3aedda9014586fbe91b98b26e2c27fb17928432dad45299f2` |

**Repository artifacts at HEAD `5476d82`:**
- M2 freeze record: `experiments/m2_container_prototype/FREEZE_RECORD.md`; probe `560834d559fbf1063c7ad33afa675abac59535e45469bc0d9da3e8254f138e1f`.
- Frozen specs: `docs/M8_IDENTITY_V2_SPEC.md` (`746be577…`), `docs/M9_SPEC.md` VM2 (`94dbdb9e…`), `docs/DECISIONS.md` D26–D29 (`47cc1e1c…`).
- Code read (not modified):
  - `src/velith/agent/proposer.py` (`ProposerAgent`, `_extract_patch`);
  - `src/velith/llm/client.py` (`OllamaClient.generate`);
  - `src/velith/core/config.py`;
  - `src/velith/task.py`, `src/velith/corpus/loader.py`;
  - `src/velith/batch/provenance.py` (`derive_task_seed`);
  - `src/velith/evaluation/verification_manifest.py`, `src/velith/taskspec/store.py` (C-ID).

**External data:**
- **Source:** SWE-bench Verified via the Hugging Face datasets API.
- **Dataset revision:** `78f471bf655a3137b2e8a75af1501690ec009ec3`, lastModified 2026-08-16.
- **Retrieved:** 2026-09-26 (500 rows).

## 4. Pilot question and its operationalization

**"Usable patch"** [PROPOSED] = a proposer output from which a patch is extracted (`patch_produced`) that applies cleanly with `git apply` to the task's base tree in the sealed task container (`patch_applies`). Test outcomes (`verified_outcome`) are recorded as additional, **probe-level** evidence, not as a production-verifier verdict.

## 5. Scope / non-scope

**In scope:**
- five real SWE-bench Verified tasks;
- proposer generation (current `ProposerAgent` + `OllamaClient`, unmodified);
- sealed digest-pinned execution via the frozen probe's functions, used unmodified;
- evidence outside the repository.

**Out of scope:**
- the production verifier (BC-1/BC-2 still apply);
- a TaskSpec schema or production real-task adapter;
- canaries, R-values, the protected-surface policy;
- any write to memory, episodes or evaluation;
- any statistic, ranking or composite score;
- any A0/A1/A2 claim;
- any modification of M0–M10, frozen specs or the M2 probe.

## 6. P-1 / P-2 / P-3 [RATIFIED]

| Principle | Implementation in this design |
|---|---|
| **P-1** Hold-out hygiene | §10: exclusion registry keyed by SWE-bench `instance_id` and by pilot task identity; permanent |
| **P-2** Predeclared measurements | §17: exactly five primary measurements with fixed semantics; diagnostics labelled non-primary |
| **P-3** Interpretation | §24: only the enumerated conclusions; raw counts only; no solve-rate percentage, interval or ranking |

## 7. Task-selection methodology [PROPOSED; computed, reproducible]

**Selection is outcome-blind:** no proposer output exists at selection time, and ease is not a criterion.

1. **Anchor (fixed):** `pallets__flask-5014`, the only task whose sealed environment is already demonstrated (M2, class A). It serves as the infrastructure control. It is already contaminated for held-out purposes (fully inspected in M2), which strengthens rather than weakens its exclusion.
2. **Eligibility filters.** Each is derived from a documented constraint, not from expected success. All must hold:
   - (a) the official `eval_script` test command begins `pytest ` (the probe's pytest/JUnit contract; this excludes django `runtests.py`, sympy `bin/test` and sphinx `tox`);
   - (b) every `test_patch` file is `.py` (the probe's test set equals the official directive set);
   - (c) ≥ 1 PASS_TO_PASS (a baseline health signal must exist; zero-P2P tasks are inadmissible, prior finding L10/PV-BASE-004);
   - (d) 1 ≤ |FAIL_TO_PASS| ≤ 5;
   - (e) the gold patch edits exactly one non-test file. This bounds the pilot to the single-shot, single-file question the current proposer can address. It is a scope constraint, not an ease criterion; difficulty labels vary among the selected tasks (§8).
3. **Repository exclusions,** made on infrastructure and trust grounds before the lottery:
   - `pytest-dev/pytest`: the code under test *is* the test runner, so candidate code would replace the runner (L4 amplified);
   - `psf/requests`: test suites with known network dependence, expected to fail under `--network none` as infrastructure noise;
   - `pallets/flask`: already used as the anchor.
4. **Lottery:** among eligible tasks in the remaining repositories (astropy, matplotlib, seaborn, xarray, pylint, scikit-learn; **pool = 98 tasks**), order by `SHA-256(instance_id + "|velith-m2pv-p1-pilot-v1")` ascending. Take the first task of each new repository until four are chosen.
5. **Reproduction:** anyone can recompute the pool and the picks from the dataset revision above and the salt `velith-m2pv-p1-pilot-v1`.

## 8. The five proposed tasks

All facts below were retrieved from SWE-bench Verified revision `78f471bf…` and are **[verified from dataset]** unless marked **[EXT]**. `hints_text` is recorded for its length only: it is excluded from the prompt (§11).

| # | instance_id | repo / version | base_commit | image (tag) | difficulty | test files (official cmd) | F2P | P2P | gold edit | problem stmt |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 (anchor) | `pallets__flask-5014` | pallets/flask 2.3 | `7ee9ceb71e868944a46e1ff00b506772a53a4f1d` | `swebench/sweb.eval.x86_64.pallets_1776_flask-5014:latest`; **digest verified in M2:** `sha256:eaf59700…f1fba4` | <15 min | `tests/test_blueprints.py` (`pytest -rA tests/test_blueprints.py`) | 1 | 59 | 1 file, 3 lines | 195 chars |
| T2 | `matplotlib__matplotlib-24570` | matplotlib 3.6 | `8f0003ae902952372824c9917975fb372c026a42` | `swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-24570:latest` (digest **[EXT]**) | <15 min | `lib/matplotlib/tests/test_offsetbox.py` (`pytest -rA …`) | 2 | 267 | `lib/matplotlib/offsetbox.py`, 4 lines | 1,356 chars |
| T3 | `scikit-learn__scikit-learn-14629` | scikit-learn 0.22 | `4aded39b5663d943f6a4809abacfa9cae3d7fb6a` | `swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14629:latest` (**[EXT]**) | 15 min–1 h | `sklearn/tests/test_multioutput.py` (`pytest -rA …`) | 1 | 26 | `sklearn/multioutput.py`, 24 lines | 1,814 chars |
| T4 | `astropy__astropy-7336` | astropy 1.3 | `732d89c2940156bdc0e200bb36dc38b5e424bcba` | `swebench/sweb.eval.x86_64.astropy_1776_astropy-7336:latest` (**[EXT]**) | <15 min | `astropy/units/tests/test_quantity_annotations.py`, `…/test_quantity_decorator.py` (`pytest -rA -vv -o console_output_style=classic --tb=no …`) | 1 | 339 | `astropy/units/decorators.py`, 2 lines | 1,572 chars |
| T5 | `pydata__xarray-6721` | xarray 2022.06 | `cc183652bf6e1273e985e1c4b3cba79c896c1193` | `swebench/sweb.eval.x86_64.pydata_1776_xarray-6721:latest` (**[EXT]**) | 15 min–1 h | `xarray/tests/test_dataset.py` (`pytest -rA …`) | 1 | 1,405 | `xarray/core/common.py`, 2 lines | 9,276 chars |

**Content hashes** (SHA-256 of the dataset strings; for provenance and leakage audit):

| # | problem_statement | patch (gold; never proposer-visible) | test_patch (never proposer-visible) | hints_text length |
|---|---|---|---|---|
| T1 | `f77d8eab7dd608172aa78b3b50dfa7e0e9b3a6a1c52d14a1cb02417eb5a0ab00` | `087d51d66413bfa35111ac0eca31f1db1636572702cfd967c428049b453f451d` | `e16f06b260b5169a49397e9d571b5af70317cd23792e1437232fabf718fe8871` | 0 |
| T2 | `e92b7455ee344da93d431a6f48428a89f1ee055b46c062bc804d4456e74c15a5` | `9e8828f0c2f3fd9dfca48f7973646b461982ce3bab6e52057ce8f9f0d6998453` | `26a8b7bf505a77812c24be9ff231fcf34422523d8ec17a1b46b4204b5a06e6fd` | 4,946 |
| T3 | `f86e27ce1f598af98703b4d161827503a9824a289e29450725ed2ee741798adb` | `ca103b1d37b3bb1413176609382daee9c33ae0c2bde2dc05300a2bd5287cd8cd` | `b73cf349fbf082664eac43c91879ba6d7fb63ae64bf24e8cb75d7f8190a132e9` | 381 |
| T4 | `1c51cc8817f7b2f1feb043bdd2a54fcc4f89150dad82c60dbd43f68d1dcdf90d` | `11f006a6ea5c6b90a0dfd5687f096bf7263c1c6adc9fe3c15874733983f3bc8a` | `1b6de57cdafbecfd2d072a4067ea0d47c4c901c123650665de67f927efc8934f` | 67 |
| T5 | `8885a8e303e07d8e74f13a24134ecd7d051a2e2ded38ac313d6667e68b93a021` | `47497c21bbb7e54a64da12a51355c18933620cd48dc4cf36f8cf4ba509b0eb88` | `4cac5b4f86e0c7cf802b95324cce75b45f43b67f88898ab40a81969aa2860d90` | 162 |

**FAIL_TO_PASS ids:**
- T1: `tests/test_blueprints.py::test_empty_name_not_allowed`.
- T2: `lib/matplotlib/tests/test_offsetbox.py::test_packers[bottom]`, `…::test_packers[top]`.
- T3: `sklearn/tests/test_multioutput.py::test_multi_output_classes_[estimator1]`.
- T4: `astropy/units/tests/test_quantity_annotations.py::test_return_annotation_none`.
- T5: `xarray/tests/test_dataset.py::TestDataset::test_chunks_does_not_load_data`.

**Why suitable, known risks, overlap, exclusion reason:**

| # | Suitability | Known infrastructure risks | Overlap with Velith evidence | Why excluded from future held-out |
|---|---|---|---|---|
| T1 | Environment demonstrated (M2 A–F); infrastructure control | Low (class-A evidence for this image and runner) | **Yes:** M2 prototype, freeze record, gold patch inspected | Already inspected; the pilot adds proposer exposure |
| T2 | Real bug, small edit; UI-library domain | The test file uses image comparison: fonts/freetype drift can make the baseline unhealthy **[EXT]** | None | Pilot exposure (P-1) |
| T3 | Multi-line fix (24 lines); API/logic domain | Heavy import; likely deterministic | None | P-1 |
| T4 | Decorator/type-hint semantics; two test files | Official flags differ from the probe's (`-vv -o console_output_style=classic --tb=no`): output format only, JUnit unaffected; old stack (astropy 1.3) **[EXT]** | None | P-1 |
| T5 | Long problem statement; large test file | 1,405 P2P: long runtime (timeout budget, §21); the 9,276-char statement is a prompt-length risk (§12, OD-3); optional zarr/dask dependencies **[EXT]** | None | P-1 |

**Replacement rule** [PROPOSED]: if a task is inadmissible at **admission** (§9, before any generation), it is replaced by the next eligible task *of the same repository* in lottery order. For T1 there is no replacement (sole flask task); if T1 is inadmissible, the pilot stops (§25). **No replacement after generation starts.**

## 9. Task admissibility [PROPOSED]

A task is **admissible** iff all of the following hold before any proposer call:
- (i) the image digest and platform are pinned and verified;
- (ii) the probe's base invariant holds (`HEAD^1 == base_commit`, clean tree);
- (iii) the probe **Case A** (gold) run classifies PASSED with a healthy baseline (every P2P passed, no F2P passed, every required id mapped), using the frozen probe CLI unchanged;
- (iv) the declared protected-config set exists as recorded (§14);
- (v) the prompt passes the leakage audit (§22) and fits the declared context window (§12).

Admission results are recorded and the admitted set is **frozen by hash** (§19) before generation.

## 10. Hold-out exclusion (P-1) [RATIFIED principle; mechanism PROPOSED]

**Hard rule:** `pilot_task ∉ future held-out population`, permanently.

**Registry** [PROPOSED]: `PILOT_EXCLUSION_REGISTRY.json` (research workspace; content-addressed, append-only).

```json
{"registry": "velith-pilot-exclusion", "version": 1, "dataset": "SWE-bench/SWE-bench_Verified",
 "dataset_revision": "78f471bf655a3137b2e8a75af1501690ec009ec3", "pilot": "M2-PV-P1",
 "excluded": [
   {"instance_id": "pallets__flask-5014",             "pilot_task_identity": "<sha256(material)>"},
   {"instance_id": "matplotlib__matplotlib-24570",    "pilot_task_identity": "<…>"},
   {"instance_id": "scikit-learn__scikit-learn-14629","pilot_task_identity": "<…>"},
   {"instance_id": "astropy__astropy-7336",           "pilot_task_identity": "<…>"},
   {"instance_id": "pydata__xarray-6721",             "pilot_task_identity": "<…>"}]}
```

It also records any admission-time replacements, and the replaced tasks themselves (they were exposed at admission).

**Keyed on `instance_id` as well as identity.** A task's M4 identity is `SHA-256(material)` (`corpus/manifest.py:39-46`). A future corpus may encode the same SWE-bench instance with *different* material bytes, and an identity-only exclusion would then silently miss it. `instance_id` is the stable key.

**Enforcement today:** procedural only. No frozen component can express the exclusion.
- M4's partition spec and manifest have no exclusion concept.
- M9 `PreRegistration` has no exclusion field.
- The VerificationManifest is held-out-only (Q-A) but binds TaskSpecs, not provenance of exposure.

**Future amendment required (not now):** a code-enforced check at corpus construction and/or pre-registration that rejects any held-out task whose `instance_id` or identity is in the registry. It is classified **C (future amendment)**. M8 is not modified.

## 11. Prompt construction

**[EXISTING]** The proposer sends `Task.prompt` verbatim to Ollama (`agent/proposer.py:97`). Source-file context is "a Task/fixture concern" (proposer module docstring). **[FROZEN, D28 D-2]** `Task.prompt` is a pure function of `CorpusTask.material`. **[EXISTING]** No real-task adapter exists; only `FixtureTaskAdapter`.

**Therefore the pilot must define `material` and the `material → prompt` function.** It must do so experiment-side, outside `src/`, without creating the production real-task adapter.

**`material` composition — OPEN (OD-1).** This is the single most consequential decision, because the proposer has no repository access:

| Option | Content | Gold-derived? | Consequence |
|---|---|---|---|
| **M-A (bare)** | `problem_statement` only | No | The proposer must invent exact diff context lines without seeing the source. A patch that fails to apply is then expected and **confounds "proposer incapable" with "prompt lacks code"** |
| **M-B (oracle files)** | + contents of the file(s) the gold patch edits | **Yes: leaks the fix location. Inadmissible** under this pilot's leakage rule | — |
| **M-C (non-gold retrieval)** | + contents of source files selected **without gold information** (e.g. BM25 over the base tree, top-k within a token budget) | No | Tests whether the proposer can patch *given* code. Needs an experiment-side retriever and a context budget |
| **M-D (named files)** | + files literally named in `problem_statement` | No | Deterministic and simple; often names no file |

**CSE recommendation (not a decision):** run **two pre-declared conditions per task**, M-A and M-C, so that a null result can be attributed to either the proposer or the context contract. Generation is cheap; execution cost only rises for patches that apply.

**Prompt template** [PROPOSED, fixed before execution; OD-2]:
- Fixed header: "You are fixing a bug in the repository `<repo>` at a fixed commit. Reply with a single unified diff patch only, in a fenced ```diff block, with paths relative to the repository root."
- Then `problem_statement` verbatim.
- Under M-C, then the retrieved files, each delimited as `--- FILE: <path> ---`.
- It mirrors the fixture prompt's "Reply with a unified diff patch only" instruction (`task.py`).

**Never in the prompt** [PROPOSED; audited §22]: TaskSpec contents; the gold `patch`; `test_patch`; FAIL_TO_PASS / PASS_TO_PASS ids; `hints_text`; image digest; verifier or probe internals; held-out or exclusion metadata; other tasks' data.

## 12. Proposer configuration

| Item | Value | Class |
|---|---|---|
| Agent | `velith.agent.proposer.ProposerAgent`, unmodified | EXISTING |
| Client | `velith.llm.client.OllamaClient.generate(prompt, model, seed, temperature)` → `POST /api/generate`, options `{seed, temperature}` only | EXISTING |
| Model | `Settings.ollama_model` default `"qwen2.5-coder"`. **Resolved size/quantization and weights digest [EXT]** (`ollama show`, `/api/tags`). The client records only the tag string as `model_version` | EXISTING / EXT |
| Temperature | 0.0 (`ProposerAgent` default) | EXISTING |
| Seed | `derive_task_seed(pilot_task_identity, 0)` (`batch/provenance.py:27`) | PROPOSED (OD-12) |
| Context window (`num_ctx`) | **Not set by the client**: the Ollama server default applies. Long prompts (T5; any M-C prompt) risk **silent truncation** | OPEN (OD-3) + EXT |
| Max generation (`num_predict`) | Not set: server default | OPEN (OD-3) + EXT |
| Tools / filesystem / network (for the model) | None; single text completion | EXISTING |
| Timeout | `Settings.ollama_timeout_seconds` = 120 s, one HTTP call | EXISTING |
| Retry | None in the client. The pilot policy is in §21 | PROPOSED |

**OD-3 options** (no code change to the frozen client):
- (a) accept the server defaults and **declare prompts longer than the default context inadmissible**;
- (b) create a derived Ollama model through a Modelfile with an explicit `num_ctx`/`num_predict`, recorded as a distinct model identity.

## 13. Patch artifact contract [EXISTING extraction + PROPOSED evidence]

**Expected format:** one unified diff, preferably fenced ```diff. Extraction is exactly `_extract_patch`:
- the first fenced block (language tag stripped);
- otherwise raw text starting with `diff --git`, `--- ` or `@@`;
- otherwise `""`.

**Rules:**
- **Produced** ⇔ `Proposal.has_patch` (non-empty extracted text).
- **Validity** is determined only by application: `git apply` inside the candidate container, by the probe's script. There is no separate parser.
- **Application test:** probe status `PATCH_APPLY_FAILED` (script exit 92) means it does not apply.
- **No patch:** `patch_produced = false`; no container is run for that (task, condition).
- **Retention:** the full raw completion text, the extracted patch and the prompt are retained as evidence files (§19), outside the repository. They are **never** fed back to any proposer and never written to memory.

**Four evidence layers, kept separate:**
1. proposer output (completion, extracted patch, tokens, latency);
2. patch application (candidate-container `git apply` result);
3. test-execution evidence (probe baseline and candidate JUnit, runtime state);
4. feasibility classification (§18).

## 14. Pilot execution architecture [PROPOSED]

```
Stage 0  Inventory [EXT]    per task: pull image by tag → record digest; verify platform, repo dir,
                            interpreter path, HEAD^1 == base_commit; list protected-config files
Stage 1  Admission          frozen probe CLI, unchanged: fetch-spec + run --case A (gold) → §9
Stage 2  Freeze pilot set   admitted tasks + material + prompts hashed → PILOT_SET manifest
Stage G  Generation         in the pinned Velith container: ProposerAgent → JSON on stdout only
Stage X  Candidate exec     pilot harness (PB-1) calls the probe's run_container/classify,
                            unmodified, with the candidate patch
Stage R  Report             measurements (§17), classification (§18), raw counts only
```

**Protected-config rule per task** [PROPOSED; OD-5]: the probe needs an explicit list. It is: test_patch files ∪ those of {`setup.cfg`, `pyproject.toml`, `tox.ini`, `pytest.ini`, root `conftest.py`, `conftest.py` in each test file's directory chain} that exist at the base commit. Existence is established in Stage 0 **[EXT]**.

This inherits limitation L5 (hand-picked surface) and the probe's known open holes (L4 import path, E3 test-directory shadowing, E4 in-process forgery). They are acceptable here only because the pilot claims **feasibility, not verdict integrity** (§26).

## 15. M2 probe reuse

**What the frozen probe CLI can do, unchanged:**
- `fetch-spec`: build a task spec outside the repo from the dataset, with a digest-pinned image;
- `run --case A`: digest verification, baseline plus gold candidate in fresh `--network none` containers, protected-surface restoration, JUnit mapping, and classification. **This is sufficient for admission** (§9).

**What it cannot do — PB-1 (blocking for Stage X):**
- The CLI's `--case` accepts only `A|B|C|D|D0|E`; the candidate patch is derived from the gold patch (`_case_inputs`).
- **There is no input for an externally generated candidate patch.**
- Smuggling a candidate into the spec's `patch` (gold) field would mislabel evidence as "gold", and is refused by `load_spec` when the candidate touches protected files. **Rejected: an unsafe workaround.**

**Minimum separate design change (not made here):** a new, experiment-only **pilot harness** that imports the frozen `probe.py` module **as a library, unmodified**. It calls `load_spec`, `verify_image`, `run_container(spec, role=…, candidate_patch=<proposer patch>, tamper=False, fault_cmd=None, …)` and `classify(...)`, and writes the evidence outside the repository.
- Its identity (file SHA-256) and the probe's SHA-256 are recorded in the evidence.
- The harness location (repo `experiments/` vs research workspace) and its authorization are **OD-4**.

**Generation stage:** the proposer requires the pinned Velith environment (Python 3.12, pinned dependencies). The **proposed** mechanism, with no repository change:
- pipe a research-workspace script into the existing `verifier` container (`docker compose run --rm -T verifier python - < gen.py`);
- the script uses `ProposerAgent`/`OllamaClient` unmodified and prints JSON to stdout;
- it writes no file;
- it reaches Ollama at `host.docker.internal` (D16.2).

This also needs authorization under OD-4.

## 16. Memory / episode isolation [PROPOSED; audited]

| Store | Access |
|---|---|
| Experience/episode store (`data/episodes/`) | **No write.** The generation script imports no store, writer or `Episode.build`. The SHA-256 of `data/episodes/episodes.jsonl` is recorded before and after; any change → abort (§25) |
| A1/A2 memory, checkpoints | Never read, never written |
| M8 evaluation sink, M9 pre-registration, M10 results | Never read, never written; M8/M9/M10 code never invoked |
| VerificationManifest / TaskSpec store (C-ID) | Not used: the pilot is not an evaluation of record |
| Evidence | Written only under an operator-given directory **outside** the repository (probe `outside_repo` rule) |
| Repository | Read-only; `git status --porcelain` empty before and after |

## 17. Measurements (P-2) — primary, predeclared

Recorded per (task, condition). **No other primary measurement may be added after results are seen.**

| # | Measurement | Type | Exact semantics | Missing-value behaviour |
|---|---|---|---|---|
| 1 | `patch_produced` | bool | `Proposal.has_patch` | `NA_GEN_INFRA` if generation raised `ModelUnavailableError` after the retry policy |
| 2 | `patch_applies` | bool | `true` iff the candidate run reached test execution (probe status ≠ `PATCH_APPLY_FAILED`, script got past `git apply`) | `NA_NO_PATCH` if not produced; `NA_EXEC_INFRA` if the candidate container failed before apply for infrastructure reasons |
| 3 | `verified_outcome` | enum | Probe classification: `PASSED` / `FAILED` / `PATCH_APPLY_FAILED` / `INFRA_ERROR`, plus the probe reason code; `NO_PATCH` if not produced. **Probe-level evidence, not a production-verifier verdict** | Never missing: `INFRA_ERROR` carries the reason |
| 4 | `token_count` | two ints | `prompt_tokens` = Ollama `prompt_eval_count`; `completion_tokens` = `eval_count` (as recorded by the client) | `NA_GEN_INFRA`. Caveat: prompt-prefix caching can lower `prompt_eval_count`; recorded as-is |
| 5 | `latency` | float s | `Proposal.latency_seconds` (client wall time of the single call) | `NA_GEN_INFRA` |

**Diagnostics (non-primary, labelled):**
- the git apply stderr excerpt;
- the probe's baseline and candidate per-test outcomes;
- container durations;
- the prompt SHA-256 and length;
- `done_reason`, if the harness records it.

**Forbidden:** composite scores, rankings, rates, percentages, confidence intervals.

## 18. Failure taxonomy [PROPOSED; deterministic, first match wins]

| Code | Condition | Attribution | Primary effect |
|---|---|---|---|
| `INADMISSIBLE_ADMISSION` | §9 fails before generation | Task/environment | Replace (§8) or stop |
| `INADMISSIBLE_LEAKAGE` | Leakage audit (§22) fails, or the prompt exceeds the declared context | Pilot design | Task excluded from interpretation; stop if systemic |
| `GEN_INFRA` | `ModelUnavailableError` after retries | Infrastructure | `NA_GEN_INFRA`; not a proposer failure |
| `NO_PATCH` | Completion yields no extractable patch | Proposer | `patch_produced = false` |
| `MALFORMED_PATCH` | Extracted text rejected by `git apply` as corrupt or not a patch (diagnostic from stderr) | Proposer | `patch_applies = false`; `verified_outcome = PATCH_APPLY_FAILED` |
| `PATCH_DOES_NOT_APPLY` | Well-formed diff whose context does not match the base | Proposer | Same as above |
| `BASELINE_UNHEALTHY` | Probe baseline unhealthy in the candidate-stage run | Infrastructure (**never** proposer) | `INFRA_ERROR` |
| `EXEC_INFRA` | Probe: image, container start or copy failure, runtime error, `RESULT_MAPPING` | Infrastructure | `INFRA_ERROR`; §21 retry |
| `TIMEOUT` | Candidate run exceeds the budget (probe `CANDIDATE_TIMEOUT` → FAILED) | Recorded as the probe classifies it; **flagged**, because attribution is not established (L1/L2) | Probe outcome kept; interpretation notes the flag |
| `RESOURCE_EXHAUSTED` | Probe `RESOURCE_KILLED` | Unattributed | `INFRA_ERROR` (probe prototype rule, not production, FREEZE_RECORD §8) |
| `TEST_INTEGRITY` | Candidate touched protected files (the restoration log shows removals or restored paths) | Recorded; outcome still probe-classified | Diagnostic flag |
| `CANDIDATE_FAILED` | Applies, tests ran, some required test not passed | Proposer | `FAILED` |
| `CANDIDATE_PASSED` | Applies and every required test passed | Proposer | `PASSED` (probe-level) |
| `HARNESS_FAILURE` | Unexpected pilot-harness exception | Infrastructure | Stop and report (§25) |

Infrastructure failures are **never** mapped to candidate failure. A task with unresolved `GEN_INFRA` or `EXEC_INFRA` after retries is reported as **not interpretable** for that condition.

## 19. Evidence and hashing [PROPOSED]

**Per task and condition,** under `<evidence-root>/<instance_id>/<condition>/`:
- `prompt.txt`, `material.txt`, `completion.txt`, `patch.diff`;
- `generation.json` (model, `model_version`, seed, temperature, tokens, latency, timestamp);
- the probe's `evidence.json` plus baseline and candidate `stdout.txt` and `junit.xml`.

**Hashes:**
- `PILOT_SET.json`: the admitted tasks with dataset revision, spec SHA-256s, image digests, material and prompt SHA-256s, protected-config lists. It is frozen **before** Stage G.
- `EVIDENCE_MANIFEST.sha256`: SHA-256 of every evidence file (the M2 manifest practice). Its hash is recorded in the pilot report.
- Probe SHA-256 (`560834d5…`), harness and generation-script SHA-256s, Velith commit.

## 20. Reproducibility [PROPOSED]

**Recorded:**
- task identity (`instance_id` + material SHA-256);
- environment identity (image digest, platform);
- proposer identity (model tag, `model_version` string, **weights digest [EXT]**, Ollama server version **[EXT]**, `num_ctx`/`num_predict` actually in force **[EXT]**);
- generation configuration (temperature, seed);
- all evidence hashes;
- UTC timestamps;
- host identity (OS/WSL kernel, Docker version, CPU and memory);
- Velith commit.

**Not claimed:**
- cross-machine determinism;
- that temperature-0 generation is bit-identical across hardware or Ollama versions;
- probe determinism beyond the M2 one-host evidence (L9).

## 21. Budget [PROPOSED; OD-7, OD-8]

| Budget | Limit |
|---|---|
| Generation | 5 tasks × {1 or 2} conditions × **1 attempt** each; 120 s per call (existing client timeout). **No re-generation after a produced patch**, whatever its quality |
| Generation retries | Only on `GEN_INFRA`: ≤ 2 retries with the identical request (same seed); outcome-independent |
| Execution: admission | 1 Case-A run per task (plus replacements); probe limits `--memory 4g --cpus 2 --pids 512`; `--timeout` 1800 s for T5 and 900 s for the others (OD-7) |
| Execution: candidate | 1 probe run (baseline + candidate) per produced patch |
| Execution retries | Only on `EXEC_INFRA`: ≤ 1 fresh-container retry; outcome-independent |
| Storage | Evidence ≤ 1 GB total (large `-rA` output expected for T5); abort if exceeded |

## 22. Leakage / threat model

**Channels and controls:**
1. **Gold, test or hints in the prompt:** automated audit before Stage G. The prompt must not contain the gold `patch` or `test_patch` text; any F2P/P2P test id; any line of the gold patch's `+`/`-` hunks; or any substring of `hints_text` longer than 40 characters. Any hit → `INADMISSIBLE_LEAKAGE`.
2. **Retrieval leakage (M-C):** the retriever may read only the base tree and `problem_statement`. It must never read `patch`, `test_patch`, F2P/P2P or `hints_text`. Its code is part of the evidence.
3. **Future git history in the task image** (published reports of agents mining `.git`): not reachable. The proposer has no filesystem or tool access, and only the prompt crosses to the model.
4. **Model pretraining contamination:** these public fixes (2018–2023) may be in the model's training data. **Not controllable; residual RS-P1.** A success does not show reasoning ability.
5. **Pilot-to-evaluation leakage:** §10 registry.
6. **Candidate-to-harness manipulation:** probe residuals (L4, E3, E4 in-process forgery) apply. Accepted for a feasibility pilot with a non-adversarial proposer, and stated in §26.

## 23. Execution procedure (after authorization; an executor makes no scientific decisions)

1. Verify the repository is clean at the recorded commit; record the hash of `data/episodes/episodes.jsonl`.
2. **Stage 0 [EXT]:** for T1–T5, pull by tag, record the digest, verify platform, repo dir, interpreter and `HEAD^1`, and list the protected configs.
3. **Stage 1:** frozen probe `fetch-spec` (with the §14 protected configs), then `run --case A`. Apply §9; apply the §8 replacement rule if needed. Write `PILOT_EXCLUSION_REGISTRY.json`.
4. **Stage 2:** build material and prompts per OD-1/OD-2 and run the leakage audit (§22). Freeze `PILOT_SET.json` and record its hash.
5. **Stage G:** one generation per (task, condition) (§21). Store the evidence.
6. **Stage X:** for each produced patch, run the pilot harness (baseline + candidate, fresh containers).
7. Verify the episode-store hash and the repository status are unchanged. Build `EVIDENCE_MANIFEST.sha256`.
8. **Stage R:** tabulate the five measurements; apply §24 verbatim.

## 24. Interpretation rules (P-3) [RATIFIED principle; rules PROPOSED]

**Report raw counts only** ("k of n admissible (task, condition) pairs"). Never a percentage, interval, rank or composite.

| Conclusion | Condition (pre-declared) |
|---|---|
| **C1** The proposer produced **no usable patch** on the admitted pilot population (per condition) | ≥ 3 admissible tasks and none with `patch_applies = true` |
| **C2** The proposer can produce usable patches on **at least some** selected tasks | ≥ 1 admissible task with `patch_applies = true`. Any `PASSED` is reported individually as probe-level evidence |
| **C3** Infrastructure prevents interpretable completion | < 3 admissible tasks after replacement, or unresolved `GEN_INFRA`/`EXEC_INFRA` on ≥ 3 tasks |
| **C4** A specific architecture component blocks feasibility | Systematic `INADMISSIBLE_LEAKAGE` from context overflow (the context contract); PB-1 unresolved (execution path); persistent `GEN_INFRA` (the proposer runtime). The component is named |
| **Two conditions (if OD-1 selects M-A + M-C)** | Stated as a paired observation per task only (e.g. "applies under M-C, not under M-A on T3"). No inference beyond the five tasks |

**Explicitly not concluded:** a solve rate; a model ranking; any A0/A1/A2 or memory claim; production-verifier correctness; generalization beyond these five tasks and this model configuration.

## 25. Stop / abort conditions [PROPOSED]

Stop the pilot and report if any of the following occurs:
- T1 (anchor) is inadmissible;
- the probe raises on network mode (not `none`);
- the episode-store hash or repository status changes;
- the leakage audit fails for a systemic reason;
- the evidence budget is exceeded;
- `HARNESS_FAILURE` occurs;
- a digest drifts between Stage 0 and Stage X;
- the model identity changes mid-pilot (tag resolves to different weights).

## 26. Residual risks

| ID | Residual | Effect on interpretation |
|---|---|---|
| RS-P1 | Pretraining contamination of public SWE-bench fixes | C2 does not imply reasoning; stated with every C2 |
| RS-P2 | Probe runner and result-channel holes (L4, E3, E4) | `verified_outcome` is probe-level, non-adversarial evidence only |
| RS-P3 | Silent context truncation (OD-3) | May convert a capability question into a context question; mitigated only by the §9 admission rule |
| RS-P4 | Official-command flag differences (T4) | JUnit mapping unaffected; fidelity to the official harness not claimed (L6) |
| RS-P5 | Environment drift (fonts for T2, runtime for T5) | Captured by admission (§9) and baseline health |
| RS-P6 | n = 5 | C1/C2 are existence statements, not rates |
| RS-P7 | Temperature-0 determinism not guaranteed | Single attempt, recorded identity; no replication claim |
| RS-1…RS-8 | M2-PV residuals | Unchanged; not addressed by the pilot |

## 27. Open questions

| ID | Question | Class |
|---|---|---|
| OD-1 | `material` composition: M-A only, M-C only, or M-A + M-C (and the M-C retriever and token budget) | **OPEN (RD)** |
| OD-2 | Exact prompt template text | OPEN (RD); proposed in §11 |
| OD-3 | Context/generation limits: accept server defaults plus an inadmissibility rule, or a Modelfile-derived model | OPEN (RD) + EXT |
| OD-4 | Pilot harness and generation-script **implementation authorization and location** (PB-1) | **OPEN (RD), blocking** |
| OD-5 | Protected-config rule (§14) | OPEN (RD) |
| OD-6 | Replacement rule (§8) | OPEN (RD) |
| OD-7 | Probe `--timeout` values (900 s / 1800 s), memory, CPU | OPEN (RD) |
| OD-8 | Retry numbers (§21) | OPEN (RD) |
| OD-9 | Registry format and location; future code-enforcement amendment (§10) | OPEN (RD) |
| OD-10 | Keep T1 (already inspected) as the anchor | OPEN (RD); proposed yes |
| OD-11 | Exclude `hints_text` from the prompt | OPEN (RD); proposed yes |
| OD-12 | Seed rule `derive_task_seed(identity, 0)` | OPEN (RD) |
| EXT-1…5 | Image digests (T2–T5), interpreter and repo paths, `HEAD^1` invariant, protected-config existence, Ollama model digest / server version / effective `num_ctx` | **EXT (Stage 0)** |

## 28. Pilot acceptance gate (before execution)

Every item must hold:
- all OD-1 to OD-12 ruled;
- PB-1 resolved by an authorized harness;
- Stage 0 **[EXT]** facts recorded;
- admission complete, with `PILOT_SET.json` and the exclusion registry frozen by hash;
- the leakage audit passed;
- the repository clean and the episode-store hash recorded.

## 29. Implementation boundary

This milestone produced **only this document**.
- **No source, test, spec, probe, TaskSpec or verifier change.**
- The pilot harness and generation script are **not written**; they require a separate authorization (OD-4).
- The M2 probe is to be reused **unmodified**, as a library.

## 30. Research Director decision checklist

- [ ] OD-1 material composition (and M-C retriever and budget, if chosen)
- [ ] OD-2 prompt template
- [ ] OD-3 context/generation limits
- [ ] OD-4 authorize the pilot harness and generation script (PB-1) and choose their location
- [ ] OD-5 protected-config rule
- [ ] OD-6 replacement rule
- [ ] OD-7 execution limits
- [ ] OD-8 retry policy
- [ ] OD-9 exclusion registry, and record the future enforcement amendment
- [ ] OD-10 T1 anchor
- [ ] OD-11 hints exclusion
- [ ] OD-12 seed rule
- [ ] Accept the five tasks from the pre-declared lottery (salt `velith-m2pv-p1-pilot-v1`, dataset revision `78f471bf…`)
- [ ] Authorize Stage 0 inventory (read-only, on the execution host)

*End of M2-PV-P1 pilot design.*
