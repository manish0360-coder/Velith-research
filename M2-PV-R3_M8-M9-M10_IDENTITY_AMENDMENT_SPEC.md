# M2-PV-R3 — M8/M9/M10 Evaluation Identity Amendment Specification

**Document type:** Specification of a future amendment. **This document is not the amendment.** It changes no repository artifact, no `DECISIONS.md` entry, no M8/M9/M10 specification, no schema and no code.
**Author:** Chief Systems Engineer. **Ratifying authority:** Research Director. **Review:** Scientific Review Council.
**Engineering baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3` (clean).
**Authoritative predecessor:** `M2-PV-R_ARCHITECTURE_RATIFICATION_AMENDMENT.md`, SHA-256 `84d67088792739cb972238666595458c0a6d41ff86bc5755d7c51ce7cb93d13a` (verified before drafting).
**Date:** 2026-09-25

Every statement about current behavior below is traced to a file and line at the baseline. **Ruling status:** Q-A to Q-H have been ruled by the RD and approved by the SRC delta review ("M2-PV-R3 — Delta Scientific Review and Ruling", supplied file SHA-256 `b87731b19b7552fddba3ffcf91eccb8d5fa1e4e28ef08906c8bbe86edf045381`); the ratified rulings are recorded in §18. Version strings and field names remain specification text until the Amendment Text Freeze Gate (§20).

---

## 1. Executive decision

1. **Mechanism (RD-selected).** A **formal, versioned M8 supersession**. M8 v1 is not modified in place; it remains the immutable historical specification. A successor, **M8 evaluation identity v2**, adds exactly one scientific component, `verification_manifest_hash`, plus one explicit version discriminator.
2. **Coordinated migration.** M8 identity v2, the M9 pre-registration amendment and the M10 reconstruction amendment are **one identity migration**. They must be specified, reviewed, frozen and implemented together, because M10 rebuilds M8 identities from M9 fields at two sites (§10). Partial adoption breaks the join by construction.
3. **No statistical change.** M9 statistical formulas and decision rules are unchanged; this amendment changes identity/version plumbing, not statistical inference (§7.4).
4. **No data migration.** No real M8, M9 or M10 artifact exists in the repository (§11.1). v1 identities stay reproducible at the historical commits; nothing is rehashed.
5. **Ratified RD rulings** (§18): evaluation population (Q-A: held-out only), version strings (Q-B), legacy-fixture handling (Q-C), classifier identity (Q-D), available-partition lineage (Q-E: deferred), and Q-F to Q-H.

## 2. CX-A1 resolution

**The conflict.**
- `M8_SPEC.md:10`: "Once frozen it is immutable; the M8 implementation is *extracted from* it and never redesigns it."
- The ratified VerificationManifest binding requires `EvaluationProvenance.identity` to change.

**Resolution (RD-selected mechanism, specified here).** Immutability is honored literally:
- M8 v1's text and code are never edited.
- The change is introduced as a **successor identity version**, M8 identity v2, defined by a new superseding DECISIONS entry and a new successor specification document (§20).
- The successor governs all evaluations **created after it is frozen**. v1 governs, historically, everything before.

**Status-ambiguity resolution (no edit to `M8_SPEC.md`).** `M8_SPEC.md:11` reads "Status: DRAFT — first complete draft, pending Scientific Review". Repository governance evidence shows the specification was frozen:

| Evidence | Location |
|---|---|
| Commit `49d9f75` (2026-08-01): "docs: add **frozen** M8 specification and implementation handoff" | `git log -- docs/M8_SPEC.md` (sole commit touching the file) |
| Handoff: "It is *extracted from* `docs/M8_SPEC.md` (frozen)" | `M8_IMPLEMENTATION_HANDOFF.md:5` |
| Tag `m8-complete` → `fe2b3d7` "docs: freeze M8 (m8-complete)" | `git tag` |
| "M8 — complete and certified (`m8-complete`)" | `PROJECT_STATE.md:96` |

**Governance resolution:** **M8 v1** = `docs/M8_SPEC.md` as committed at `49d9f75`, frozen and certified at `m8-complete`. It is the historical frozen specification of the completed M8 implementation. The "DRAFT" header is a **stale label** that the recorded governance contradicts.

**Contradiction check:** no frozen rule assigns authority to that header over the freeze commit, the handoff or the certification tag. This interpretation **does not conflict** with any frozen rule found, so there is **no STOP**. The stale label should be corrected only by a separate, explicitly authorized documentation change, or recorded in the D-entry (§20). This document does not correct it.

## 3. M8 v1 preservation

**What M8 v1 froze (identity-relevant):** `EvaluationProvenance` (`src/velith/evaluation/provenance.py`) with exactly eight components (`to_dict()`, lines 26-36):
- `checkpoint_identity`, `manifest_hash`, `arm`, `base_model`, `eval_seed`,
- the cost guard as three fields: `max_tasks`, `max_attempts_per_task`, `max_tokens`.

Identity (`provenance.py:57-66`):

```
EvaluationIdentity_v1 = SHA256_hex( UTF8( json.dumps(to_dict(), sort_keys=True,
                                               ensure_ascii=False, separators=(",", ":")) ) )
```

- **No version component exists in v1.**
- `manifest_hash` is the **full-corpus partition manifest hash** (`corpus/manifest.py:103-112`: SHA-256 over the sorted `identity → partition` of every task, available *and* held-out). `HeldOutEvaluationSet` carries it (`evaluation/heldout_set.py`). The directive's term "held-out manifest hash" refers to this value. Its scope is the whole corpus split, not the held-out subset alone.
- The M8 runner checks `checkpoint_identity`, `manifest_hash` and `arm` for consistency (`evaluation/runner.py:41-52`) and stamps each `EvaluationRecord` with `provenance.identity` (`runner.py:81`).

**Preservation rules:**
- **P-V1-1.** v1 text, code and identities are never edited, rehashed or reinterpreted.
- **P-V1-2.** Any v1 identity remains reproducible by executing the v1 code at `b14d918` (or `m8-complete` for M8 alone).
- **P-V1-3.** No v1 record may be joined to a v2 pre-registration, or a v2 record to a v1 pre-registration (§12.4).

## 4. M8 v2 architecture

**What changes:** exactly two keys are added to the hashed identity payload:
1. `identity_version`, a constant string (proposed: `"m8-evaluation-identity-v2"`). It makes v2 payloads self-describing and v1/v2 unambiguous (§12).
2. `verification_manifest_hash`, a 64-character lowercase SHA-256 hex digest of the VerificationManifest (§5).

**What does not change:**
- the eight v1 components and their meanings;
- the canonical serialization rule;
- the hash algorithm;
- `EvaluationRecord` (§9);
- the sink;
- the runner's sweep, cost guard and write order;
- the attempt harness;
- A0/A1/A2 semantics;
- checkpoint identity;
- the corpus manifest.

```
M8 v2 dataflow
  HeldOutEvaluationSet{tasks (each with .identity, .handle), manifest_hash}
        │ (population per §6)
        v
  VerificationManifest  {task_identity → TaskSpec digest}  ──► verification_manifest_hash
        │                                                          │
        v                                                          v
  M8 consistency check (§13) ◄──── EvaluationProvenance_v2 {8 v1 components + identity_version
        │                                                   + verification_manifest_hash}
        v                                                          │ .identity
  run_heldout_evaluation (unchanged sweep) ──► EvaluationRecord.evaluation_identity
```

## 5. VerificationManifest — formal definition

**Definition.** For an evaluation population `Π` (§6), `VM(Π)` is the finite map `task_identity ↦ taskspec_digest`, one entry per task in `Π`. Under D28 Option D, `taskspec_digest` is the task's `CorpusTask.handle`, verified against the TaskSpec registry.

**Canonicalization (reuses the repository's existing convention; no new format):**
- **Serialization:** `json.dumps(VM, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`. This is the identical rule used by `compute_content_hash` (`episodes/episode.py:96-102`), the corpus manifest (`corpus/manifest.py:109-112`), `EvaluationProvenance` (`provenance.py:63-66`) and `PreRegistration` (`analysis/preregistration.py:135`, via `compute_content_hash`).
- **Sorting:** by key (`task_identity`), ascending code-point order via `sort_keys=True`. Keys and values are lowercase hex, so the order is well defined.
- **Encoding:** UTF-8.
- **Hash:** SHA-256, lowercase hex digest.
- `verification_manifest_hash = compute_content_hash(VM)`. The existing helper can be reused unchanged.

| Condition | Required behavior |
|---|---|
| Empty population (`Π = ∅`) | **Reject** (`VerificationManifestError`). An evaluation over zero tasks has no verification contract. *Note:* this is a construction-time rule, distinct from M9 OED-7 (`n = 0` **after** complete-case exclusion → VOID), which is unchanged. |
| Duplicate task identity in `Π` (same identity occurring twice), same digest | **Reject.** Consistent with the binder's duplicate-cell rejection (`analysis/binder.py:132-156`). Reachable: the loader emits one `CorpusTask` per descriptor (`corpus/loader.py`), while the manifest collapses same-`material` entries (`corpus/manifest.py:80-97`). |
| Duplicate task identity with **different** digests | **Reject** (conflicting verification contracts). |
| Missing TaskSpec (a population task whose digest is absent from the registry) | **Reject.** |
| Invalid digest (not `^[0-9a-f]{64}$`, the repository's existing pattern at `preregistration.py:59`, `binder.py:43`) | **Reject.** |
| Registry content does not re-hash to its digest | **Reject** (D28 fail-closed). |

## 6. Evaluation population — analysis

**Repository facts.**
- `run_heldout_evaluation` iterates the entire `HeldOutEvaluationSet` (`evaluation/runner.py:72`: `for corpus_task in heldout_set`).
- Every arm and checkpoint is evaluated against the same set (M8 identical harness).
- A cost-guard halt produces an incomplete run → VOID (`M9_SPEC` §3.5.1).
- The corpus manifest hash covers all tasks, available and held-out (§3).

| Option | Definition | M8 held-out eval | A0/A1/A2 | Checkpoint identity | M8 runner | EvalProvenance / M9 prereg / M10 | Deterministic reruns | Verdict |
|---|---|---|---|---|---|---|---|---|
| **A** | Held-out set only: the identities in `HeldOutEvaluationSet` | Exact match: the set the runner iterates | Identical for all arms | Independent (memory bound separately) | Checkable from the set itself (handles present) | Known at pre-registration time | Stable | **Compatible** |
| **B** | "All tasks in a checkpoint/evaluation run" | Under current M8 code a run's task set **is** the held-out set, so B collapses into A. Checkpoints add no tasks to a run. | = A | = A | = A | = A | = A | **Equivalent to A** (no separate definition exists in code) |
| **C** | Union of identities actually evaluated | Differs from A only when a run halts early, which is VOID anyway | Could differ across arms if one halts | — | Only known **after** the run | **Not pre-registrable:** the identity would depend on outcomes, violating M9 §3.4 (design read from identity, never from outcomes) | Unstable under halts | **Rejected** |
| **D** | Full corpus manifest population: available + held-out, the same scope as `manifest_hash` | Superset of what M8 evaluates | Identical for all arms | Also binds the TaskSpecs of available tasks, whose verdicts form A1/A2 memory | Needs available-task handles at evaluation time (the held-out set does not carry them; `heldout_set.py` filters them out) | Known at pre-registration time | Stable | **Compatible, broader** |

**Scientific analysis.**
- An evaluation identity should distinguish evaluations whose **measurement conditions** differ.
- Held-out measurement conditions depend on (i) held-out TaskSpecs, directly, and (ii) arm memory, which `checkpoint_identity` already binds by content (§14).
- **A** binds (i) exactly. **D** additionally binds the verification contract that *produced* memory. That is lineage, which affects the evaluation only through memory content, and memory content is already bound.
- D is conservative: it does not assign one identity to evaluations whose population TaskSpecs differ (barring a SHA-256 collision). It can be falsely "different", e.g. an available-task TaskSpec change that leaves every episode identical. It also needs available-task handles inside M8, which the frozen held-out set deliberately excludes (**this would widen M8's read surface into the available partition**, a D8-sensitive boundary).

**Status: RATIFIED (Q-A).** The VerificationManifest is **held-out-only** (population A). Available-task TaskSpec lineage is not bound by the VerificationManifest; it remains a deferred M2-PV provenance concern (Q-E, §14).

## 7. PreRegistration identity

### 7.1 Current (verified)
`PreRegistration` (`analysis/preregistration.py:69-103`) has 20 declared fields plus `identity`. The identity is `compute_content_hash(model_dump() minus "identity")` (`:127-135`), so **every** declared field is hashed, including `spec_version`. `build()` stamps `spec_version = SPEC_VERSION = "m9-spec-frozen-oed7"` (`:32`, `:172`). `manifest_hash` and `checkpoint_identities` are validated as 64-character lowercase hex (`:105-125`).

### 7.2 v2 changes (proposed)
1. **Add field** `verification_manifest_hash: str`, with the same 64-hex validator as `manifest_hash`.
2. **Bump** `SPEC_VERSION` to the new M9 lineage string (proposed `"m9-spec-frozen-oed7-vm2"`), following the OED precedent of re-freeze tags. **This is the existing M9 version concept, reused, not a new one.**
3. `build()` gains a required keyword `verification_manifest_hash`.
4. **Everything else is preserved unchanged:**
   - `arms`, `manifest_hash`, `checkpoint_identities`, `base_model`, `eval_seed`, `max_tasks`, `max_attempts_per_task`, `max_tokens`;
   - the analysis-plan fields: `primary_endpoint`, `statistic_identifier`, `alpha`, `decision_rule`, `missing_data_rule`, `global_incomplete_disposition`, `empty_dataset_disposition`, `k1_family_size`, `kgt1_family_size`, `a0_time_invariant`, `a0_checkpoint_id_c`.

### 7.3 Payload, ordering, compatibility
- **Canonical payload:** `model_dump()` minus `identity`, serialized by `compute_content_hash`. Field ordering is irrelevant (`sort_keys=True`).
- **Backward compatibility:** a v1 pre-registration (`spec_version = "m9-spec-frozen-oed7"`, no `verification_manifest_hash`) **cannot be deserialized** by the v2 model (`extra="forbid"`, required field). This is intended.
- **Existing pre-registrations:** none exist (§11.1).
- **New pre-registrations:** must be v2.
- **Collision and duplicate cases:** a v1 and a v2 payload differ in key set (`verification_manifest_hash` present only in v2) **and** in `spec_version`. Equal identities would require a SHA-256 collision. The prereg store's write-once check (`analysis/prereg_store.py:47-53`) already refuses a different identity at an occupied path.

### 7.4 Frozen statistical invariant (explicit)
**This amendment does not change M9 inference.** Unchanged:
- outcome encoding (PASSED = 1, else 0; `analysis/encoding.py:39`);
- missing-data handling (complete-case; global-incomplete VOID; OED-7 empty-dataset VOID);
- GEE, EMM, Wald inference, McNemar (K = 1), Holm correction, α = 0.01, the decision rule, K = 1 handling, A0 time-invariance (OED-2).

Only identity/version plumbing changes. M9 statistical formulas and M9 decision rules are unchanged; this amendment changes identity and version plumbing, not statistical inference.

## 8. EvaluationProvenance identity

### 8.1 v2 definition (proposed)
```
EvaluationProvenance_v2.to_dict() = {
  "identity_version":          "m8-evaluation-identity-v2",   # new, constant
  "checkpoint_identity":       <unchanged>,
  "manifest_hash":             <unchanged: full-corpus partition manifest hash>,
  "arm":                       <unchanged>,
  "base_model":                <unchanged>,
  "eval_seed":                 <unchanged>,
  "max_tasks":                 <unchanged>,   # cost guard
  "max_attempts_per_task":     <unchanged>,   # cost guard
  "max_tokens":                <unchanged>,   # cost guard
  "verification_manifest_hash":<new: SHA-256 of VM(Π)>
}
EvaluationProvenanceIdentity_v2 = SHA256_hex(UTF8(json.dumps(to_dict(), sort_keys=True,
                                                     ensure_ascii=False, separators=(",", ":"))))
```

**Delta from the directive's illustrative formula.** The repository has **no version component** in v1, and the cost guard is **three** fields, not one. Both facts are preserved: the version is added as a new key; the cost guard keeps its three keys. The name remains `manifest_hash` (not "held-out manifest hash") because renaming a frozen key would change semantics beyond the amendment.

### 8.2 Two manifests, not interchangeable
| | `manifest_hash` (M4, existing) | `verification_manifest_hash` (new) |
|---|---|---|
| Maps | task identity → **partition** | task identity → **TaskSpec digest** |
| Scope | whole corpus (available + held-out) | evaluation population `Π` (§6) |
| Changes when | a task is added, removed or re-partitioned | any TaskSpec in `Π` changes (image digest, test patch, required tests, protected-surface inputs, runner/config digests, limits) |
| Fixes | *which* tasks and *which* split | *how* each task is verified |

Neither implies the other. A changed TaskSpec leaves `manifest_hash` unchanged, because identity depends on `material` only (`manifest.py:39-46`).

## 9. EvaluationRecord analysis

`EvaluationRecord` (`evaluation/record.py:35-49`) carries `evaluation_identity`, set from `provenance.identity` (`runner.py:81`).

**Conclusion: no schema change.** The binding is by **hash inclusion**: `evaluation_identity` is a SHA-256 digest over a payload that contains `verification_manifest_hash`, so a different manifest yields a different identity except with negligible probability under the standard SHA-256 collision-resistance assumption. The frozen executor already relies on this property for `manifest_hash` and `checkpoint_identity`, which records do not carry in plaintext (`analysis/executor.py:24-28`: "a wrong manifest or a wrong checkpoint yields a different digest and fails to resolve"). The same argument covers `verification_manifest_hash`. Adding it as a record field would be redundant, and would require an M8 record-schema change for no identity gain.

## 10. M10 dependency trace (whole-repository search)

Search: `grep -rn "EvaluationProvenance(" src tests` and the identity/`compute_identity` uses at baseline.

| Location | Role | v2 change required |
|---|---|---|
| `src/velith/analysis/binder.py:74-85` `_provenance_identity` | Rebuilds `EvaluationProvenance` from pre-registration fields (join key) | Pass `verification_manifest_hash=prereg.verification_manifest_hash`; construct the v2 provenance |
| `src/velith/analysis/binder.py:88-118` `_expected_identities` | A0 + A1/A2 expected-identity map | None beyond the above; collision check unchanged |
| `src/velith/analysis/executor.py:111-124` `_provenance_identity` | **Second, independent reconstruction** (duplicate logic) | Same change as the binder. **Both sites must change in one commit.** A mismatch would make the executor's pre-flight set disagree with the binder's map. |
| `src/velith/analysis/executor.py:127-140` `expected_evaluation_identities` | Pre-flight expected set | None beyond the above |
| `src/velith/analysis/executor.py:174-210` `run_preflight` | `verify_identity()`, arms, A0 identity checks | Add: refuse a pre-registration whose `spec_version` is not the v2 lineage (§12.4) |
| `src/velith/analysis/executor.py:213-228` `_verify_records_resolve` | Observed ⊆ expected | None: v1 record identities are digests of a different payload and are not expected in the v2 expected set (barring a SHA-256 collision) |
| `src/velith/analysis/prereg_store.py:35-66` | Write-once store; integrity on read | None to logic; the v2 model governs deserialization |
| `src/velith/analysis/result_record.py:96-99, 181` | `AnalysisProvenance` carries `preregistration_identity`, plaintext `manifest_hash`, `evaluation_identities` | **No change required**: v2 prereg identity and v2 evaluation identities already cover the new component. A plaintext `verification_manifest_hash` for parity with `manifest_hash` would be optional redundancy (Q-F). |
| `src/velith/evaluation/runner.py:41-52` `_require_consistent` | M8 consistency check | Add the §13 check |
| `src/velith/evaluation/runner.py:81` | Stamps record identity | None (uses `provenance.identity`) |
| **Tests constructing `EvaluationProvenance(`** | 8 files: `tests/integration/test_m10_heldout_execution.py`, `test_m8_heldout_evaluation.py`, `test_m9_analysis_pipeline.py`; `tests/unit/test_analysis_binder.py`, `test_analysis_executor.py`, `test_evaluation_heldout_safety_invariant.py`, `test_evaluation_provenance.py`, `test_evaluation_runner.py` | Update to v2 |
| **Tests constructing `PreRegistration`** | 7 files: `tests/integration/test_m10_heldout_execution.py`, `test_m9_analysis_pipeline.py`; `tests/unit/test_analysis_binder.py`, `test_analysis_executor.py`, `test_analysis_prereg_store.py`, `test_analysis_preregistration.py`, `test_analysis_result_record.py` | Update to v2 |

**The whole-repository search at baseline found no other identity reconstruction in `src/`.** On that evidence, the binder and executor are the only places where pre-registration fields rebuild `EvaluationProvenance`.

**Join chain (v2):**
```
PreRegistration_v2 ──(verify_identity, spec_version==v2)──► binder._provenance_identity / executor._provenance_identity
    ──► EvaluationProvenance_v2.identity  (per A0 + each (checkpoint, A1|A2))
    ──► expected set ──► records' evaluation_identity must ∈ set ──► observations ──► frozen M9 statistics
```

## 11. Migration policy

### 11.1 Existing artifacts (verified at baseline)
- The only data file present is `data/episodes/episodes.jsonl` (686 bytes; the M1 spike episode). Neither the evaluation sink (`data/evaluation/heldout.jsonl`, default `eval_sink_path`, `core/config.py:153`), nor any pre-registration (`data/analysis/preregistration.json`, `prereg_path`, `:173`), nor any M10 results directory exists in the repository tree. `docker-compose.yml` bind-mounts only `./data/episodes`, so in-container M8/M9/M10 outputs would not persist to the host.
- **Therefore: no real M8 evaluation, M9 pre-registration or M10 analysis artifact exists in the repository.** Artifacts on other machines or volumes cannot be verified from here and are not claimed either way.

### 11.2 Policy
| Class | Policy |
|---|---|
| M8 v1 evaluations | Historical only. Never migrated, never rehashed. (None exist in the repository.) |
| M9 v1 pre-registrations (`m9-spec-frozen-oed7`) | Historical only. Not loadable by the v2 model by design. (None exist.) |
| M10 v1 result records | Historical only. (None exist.) |
| Test fixtures | Updated to v2 in the implementation commit (§10). They are test data, not artifacts of record. |
| Future evaluations | **v2 required** for every evaluation of record created after the v2 freeze |

## 12. Versioning model

### 12.1 Version concepts (minimal)
- **M8:** one new concept, `identity_version`, inside the hashed payload (v1 has none; v2 introduces it).
- **M9:** the **existing** `spec_version`, bumped. No additional M9 version concept is introduced.
- No separate "identity schema version" or global version is introduced.

### 12.2 Proposed strings (RD to ratify; Q-B)
`identity_version = "m8-evaluation-identity-v2"`; `SPEC_VERSION = "m9-spec-frozen-oed7-vm2"`.

### 12.3 Hash boundary
The v2 hash boundary is the full v2 `to_dict()` (ten keys) for provenance, and all declared fields minus `identity` for pre-registration. `identity_version` and `spec_version` are **inside** their respective boundaries. So v1 and v2 payloads always differ, structurally (a different key set) and explicitly (a version value); their identities therefore differ except with negligible SHA-256 collision probability.

### 12.4 Mixed-version joins
| Join | Outcome | Mechanism |
|---|---|---|
| v1 prereg + v2 code | **Reject** | Deserialization fails (missing field / `extra="forbid"`); executor pre-flight also checks `spec_version` |
| v2 prereg + v1 records | **Reject** | v1 `evaluation_identity` ∉ v2 expected set → `ExecutionError` (`executor.py:223-228`) |
| v1 prereg + v2 records | **Reject** | v1 code cannot load a v2 prereg (`extra="forbid"`), and v2 identities ∉ v1 expected set |
| v2 prereg + v2 records, different VM | **Reject** | Identities differ → unresolved |

## 13. Consistency checks

### 13.1 M8 runner (future `_require_consistent` extension)
```
population Π (per §6) ─► VM(Π) (per §5 rules) ─► h = compute_content_hash(VM)
    ─► require provenance.identity_version == "m8-evaluation-identity-v2"
    ─► require provenance.verification_manifest_hash == h         (before any attempt)
```

| Case | Behavior |
|---|---|
| Match | Proceed (unchanged sweep) |
| Mismatch | `EvaluationError`, before any attempt or record |
| Missing TaskSpec | `EvaluationError` (from §5 construction) |
| Changed TaskSpec (registry digest ≠ handle) | `EvaluationError` (D28 fail-closed) |
| Missing task (Π smaller than pre-registered) | `h` differs → mismatch → `EvaluationError` (the population is fixed by `manifest_hash` + VM) |
| Extra task | Same → `EvaluationError` |
| Duplicate identity | `EvaluationError` (§5) |

All checks run **before** the first attempt, so no partial record is written. This is consistent with the runner's existing "halt loudly with no partial record" posture (`runner.py:66-67`).

### 13.2 M9 join argument (specification-level; conditional on SHA-256 collision resistance)
Let P be a v2 pre-registration, and let `E(c, a) = EvaluationProvenance_v2(c, P.manifest_hash, a, P.base_model, P.eval_seed, P.max_tasks, P.max_attempts_per_task, P.max_tokens, P.verification_manifest_hash).identity`.
- A record `r` binds to P iff `r.evaluation_identity ∈ {E(a0, A0)} ∪ {E(c_k, a) : k ∈ 1..K, a ∈ {A1, A2}}` (`binder.py:106-117`).
- Under the standard SHA-256 collision-resistance assumption, binding implies, except with negligible probability, equality of **all ten** payload components between the provenance that produced `r` and the reconstruction from P:
  - `identity_version`, `checkpoint_identity`, `manifest_hash`, `arm`, `base_model`, `eval_seed`, `max_tasks`, `max_attempts_per_task`, `max_tokens`, `verification_manifest_hash`.
- This preserves `M9_SPEC.md:325` ("bound to exactly the M8 evaluation identity components"), now with the v2 component set.

## 14. Checkpoint / available-task analysis

**How checkpoint identity is computed.** `checkpoint.py:40-49`: SHA-256 over the concatenation of the **sorted episode `content_hash` values** of the memory snapshot. Each episode `content_hash` covers `task_id`, `verdict_state`, `verdict_output`, `secondary_passed` and the other boundary fields (`episode.py:60-74`).

**Therefore:**
- An available-task TaskSpec change that alters any memory episode's `verdict_state` or `verdict_output` **does** change checkpoint identity, and thus evaluation identity.
- A change that leaves every memory episode byte-identical does **not**. By D-1, `task_id` is spec-independent; the TaskSpec digest appears in the episode only if the verifier writes an evidence digest into `verdict_output` (M2-PV requirement PV-PROV-004, **not yet frozen**).

**Gap (explicit):** if PV-PROV-004 is not frozen, the verification contract of available tasks is **not** bound into checkpoint identity. Held-out evaluation remains correctly identified by content under option A, but the *lineage* of how memory was verified is unrecorded in identity.

**Options for the RD:**
1. Freeze PV-PROV-004 (the evidence digest, including the TaskSpec digest, carried in `verdict_output`), which binds lineage into checkpoint identity.
2. Choose population D (§6).
3. Record memory lineage in a separate provenance record, outside identity.

**Status: RATIFIED (Q-E) — DEFERRED.** Available-task TaskSpec lineage remains a **deferred M2-PV provenance concern**. This amendment does **not** solve it: the gap described above remains, and none of options 1–3 has been adopted.

## 15. Classifier identity analysis

**Question:** should D27's classifier identity (Velith commit, lock hash, interpreter version) also enter `PreRegistration.identity` and `EvaluationProvenance.identity`?

- **For inclusion:** two evaluations classified by different verifier implementations are, strictly, different measurement instruments. D27 already requires recording classifier identity. Including it prevents cross-instrument pooling, the same logic that motivated the VerificationManifest binding.
- **Against inclusion:** classifier identity includes the Velith commit. Every unrelated commit (documentation, lint) would change evaluation identity, so a **pre-registration sealed before execution would no longer match** whenever any commit lands between sealing and the run. A narrower "classifier-rules digest" (hash of the frozen classification rules and TaskSpec semantics only) would avoid this. It has no definition yet.
- **Consequence of exclusion:** identical identities could be produced by different classifier versions. Detection then relies on evidence-ledger provenance, which is audit-level, not identity-level.

**Status: RATIFIED (Q-D).** Classifier identity enters **neither** `PreRegistration.identity` nor `EvaluationProvenance.identity`. It is recorded in verification evidence (D27). One evaluation of record, meaning every arm and checkpoint under one pre-registration, runs under **one** classifier identity, enforced through the evidence ledger. A classifier-rules digest may be revisited once the M2-PV classifier rules are frozen.

## 16. Adversarial identity matrix

**Nature of this matrix: a design/adversarial audit, not execution evidence.** Each row states the outcome the v2 specification determines, and the mechanism that determines it.
- **Specification-level PASS** means the specification, as written, determines the expected outcome through a traceable mechanism. Hash-based distinctness rows are conditional on SHA-256 collision resistance.
- **Implementation-validated PASS** requires an executed automated test against an implementation. **No implementation exists, so no row is implementation-validated.** All rows become required tests in the implementation handoff (§19).

| # | Case | Expected (specification) | Specification-level | Implementation-validated |
|---|---|---|---|---|
| 1 | Same evaluation, same TaskSpecs | **Same** identity (determinism of canonical hashing) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 2 | Changed image digest in one TaskSpec (Π) | TaskSpec digest changes → VM hash changes → **different** prereg and provenance identities | PASS (spec-level) | NOT VALIDATED — no implementation |
| 3 | Changed protected-surface inputs | Same chain → **different** | PASS (spec-level) | NOT VALIDATED — no implementation |
| 4 | Changed test command / required tests | Same chain → **different** | PASS (spec-level) | NOT VALIDATED — no implementation |
| 5 | Changed runner or config digest | Same chain → **different** (these digests are TaskSpec content, OQ-12) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 6 | Changed held-out population | `manifest_hash` and VM hash change → **different** | PASS (spec-level) | NOT VALIDATED — no implementation |
| 7 | Changed arm | **Different** (v1 component) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 8 | Changed checkpoint | **Different** (v1 component) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 9 | Changed evaluation seed | **Different** | PASS (spec-level) | NOT VALIDATED — no implementation |
| 10 | Changed cost guard (any of three fields) | **Different** | PASS (spec-level) | NOT VALIDATED — no implementation |
| 11 | v1 prereg + v2 evaluation | **Reject** (§12.4) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 12 | v2 prereg + v1 evaluation | **Reject** (§12.4) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 13 | Missing VerificationManifest (empty or absent hash) | **Reject** (validator; §5 empty-population rule) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 14 | Mismatched manifest hash (provenance vs computed) | **Reject** before any attempt (§13.1) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 15 | Duplicate task identity, same digest | **Reject** (§5) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 16 | Duplicate task identity, different digests | **Reject** (§5) | PASS (spec-level) | NOT VALIDATED — no implementation |
| 17 | Available-task TaskSpec change, memory unchanged | **Same** identity (Q-A: VerificationManifest is held-out-only). This is the intended boundary, **not** a claim that available-task lineage is solved (deferred, Q-E, §14) | PASS (spec-level, per ratified Q-A/Q-E boundary) | NOT VALIDATED — no implementation |
| 18 | Different classifier version, same everything else | **Same** identity (Q-D); a classifier change is detectable only via the evidence ledger (audit-level, not identity-level) | PASS (spec-level, per ratified Q-D) | NOT VALIDATED — no implementation |

Rows 17–18 are listed so the consequences of the ratified Q-A, Q-D and Q-E boundaries stay visible.

## 17. Contract impact table

| Artifact | v1 state | v2 requirement | Migration | Status |
|---|---|---|---|---|
| `M8_SPEC` | Frozen at `49d9f75`, certified `m8-complete`; stale "DRAFT" header | Unchanged; successor specification defines identity v2 | None (historical) | **Successor spec required** |
| `EvaluationProvenance` | 8 components, no version | + `identity_version`, + `verification_manifest_hash` | None | **Formal amendment (M8 v2)** |
| `PreRegistration` | 20 declared fields + `identity`; `spec_version = m9-spec-frozen-oed7` | + `verification_manifest_hash`; `spec_version` bumped | None (no instances exist) | **Formal amendment (M9, OED precedent)** |
| `EvaluationRecord` | `evaluation_identity` | None | None | **No change** |
| `M9_SPEC` | Frozen OED-7; §3.3 identity over declared components; :325 bound to M8 components | Amendment block adding the component; re-freeze tag | None | **Formal amendment** |
| M10 binder (`binder.py:74-85`) | Reconstructs v1 provenance | Reconstruct v2 | None | **Formal amendment (code)** |
| M10 executor (`executor.py:111-124`, `:174-210`) | Second v1 reconstruction; pre-flight | Reconstruct v2; `spec_version` pre-flight check | None | **Formal amendment (code)** |
| Checkpoint identity (`checkpoint.py:40-49`) | Content hash of memory | None; available-task lineage deferred per Q-E | None | **No change** (lineage gap deferred, not solved) |
| Held-out / corpus manifest (`manifest.py:103-112`) | Full-corpus `identity → partition` hash | None | None | **No change** |
| VerificationManifest | Does not exist | New derived identity object (§5) | n/a | **New (spec)** |
| `DECISIONS.md` | D19 (real tasks superseded by ratified D26), D27, D28 not yet entered | New entry: M8 evaluation identity v2 (supersession), citing CX-A1 | n/a | **Entry required (separate authorization)** |
| Existing evaluation artifacts | None in the repository (§11.1) | — | **No migration needed** | **Verified absent (repository only)** |
| `M8 runner` `_require_consistent` | Checks checkpoint, manifest, arm | + version and VM-hash check (§13.1) | None | **Formal amendment (code)** |
| `result_record.AnalysisProvenance` | Prereg identity + plaintext `manifest_hash` | None required (covered by identities); optional parity field | None | **No change** (Q-F) |

## 18. RD decisions (ratified; SRC delta review APPROVED)

The rulings are recorded as ruled by the RD and approved in the SRC delta review. The CSE analysis column is retained unchanged as the record of the options considered.

| ID | Decision | Ratified ruling | CSE analysis (retained) |
|---|---|---|---|
| **Q-A** | Evaluation population: A (held-out) vs D (full corpus) | **A — the VerificationManifest is held-out-only.** | Favors A (§6); D widens M8 into the available partition |
| **Q-B** | Version strings (`identity_version`, `SPEC_VERSION`) | `identity_version = "m8-evaluation-identity-v2"`; `SPEC_VERSION = "m9-spec-frozen-oed7-vm2"` | Proposed in §12.2 |
| **Q-C** | Legacy fixture evaluations. The fixture corpus handles (`tests/fixtures/corpus_min/corpus.json`: `"fixture-fits"`, `"meshes-clean"`, `"clears-envelope"`) are **not** 64-hex digests, so they cannot form a v2 VerificationManifest. Options: (a) v2 universal, fixture tests supply synthetic digest handles (test-data change only); (b) dual v1/v2 code support with a version discriminator; (c) fixtures stay v1 permanently. | **(a)** — one universal v2 path; fixture tests supply deterministic synthetic 64-hex digest handles (test-data change only) | Favors (a): one production identity path; v1 remains historical at `b14d918`. (b) adds a permanent second code path. (c) leaves the frozen pipeline tested on an identity it no longer uses. |
| **Q-D** | Classifier identity in evaluation identity | **Neither identity.** Recorded in verification evidence (D27); one classifier identity per evaluation of record. | Recommends neither, plus a one-classifier-per-evaluation rule (§15) |
| **Q-E** | Available-task verification lineage | **Deferred** as an M2-PV provenance concern. **Not solved** by this amendment. | Options in §14 |
| **Q-F** | Plaintext `verification_manifest_hash` in `AnalysisProvenance` | **No plaintext field.** | Not required; parity only |
| **Q-G** | Correction of `M8_SPEC.md:11`'s stale "DRAFT" label | **`M8_SPEC.md` untouched by this amendment**; the header is corrected only by a separate, explicitly authorized documentation task. | A separate doc change, or recorded in the D-entry only |
| **Q-H** | Empty-population rejection (§5) vs any other disposition | **Reject at construction** (`VerificationManifestError`); OED-7 unchanged. | Recommends rejection at construction; OED-7 unchanged |

## 19. Implementation handoff requirements (for a future, separately authorized handoff)

1. **One atomic migration:** M8 provenance v2, M9 pre-registration v2 and both M10 reconstruction sites, plus the M8 runner check, in a single reviewed change set. The binder and executor edits are in the same commit.
2. A `VerificationManifest` builder that implements §5 exactly, reusing `compute_content_hash`, with every rejection row as a unit test.
3. All 16 required adversarial rows (§16, 1–16) as automated tests. Rows 17–18 are tested according to the RD's Q-A, Q-D and Q-E rulings.
4. Updates to the 8 + 7 test files listed in §10, with no weakening of any existing assertion.
5. Import-boundary tests unchanged: M9-C2 still imports no sink or record surface; the binder imports no memory or retrieval.
6. **No statistical module changes.** A test asserts the M9 statistics modules are byte-identical to baseline.
7. The frozen project gates (`ruff check`, `ruff format --check`, `mypy src tests`, `pytest -q`) in the no-cache container.
8. No data migration code (§11).

## 20. Exact freeze gate

This specification becomes an amendment only through these steps, in order, each separately authorized:

1. **RD rulings** on Q-A to Q-H — **completed** (§18).
2. **SRC delta review** of this specification with those rulings — **completed: APPROVED**.
3. **Freeze of the amendment text**, as three coordinated artifacts, drafted in `Velith-research`:
   - (a) a new `DECISIONS.md` entry, *"M8 evaluation identity v2 (supersedes M8 v1 evaluation identity; resolves CX-A1)"*, following the amendment procedure (`DECISIONS.md:479`);
   - (b) a successor M8 identity specification document. M8_SPEC is not edited.
   - (c) an M9 amendment block (OED precedent) with its re-freeze tag.
4. **Separate authorization** to place those three artifacts in the repository: commit, then tag (proposed `m8-identity-v2-frozen` and `m9-spec-frozen-oed7-vm2`).
5. Only then, an implementation handoff (§19) and its own authorization.

**Until then:** no repository artifact, `DECISIONS.md` entry, M8/M9/M10 specification, schema or code is changed. The 5-task pilot remains gated separately.

*End of M2-PV-R3 specification — not the amendment itself.*
