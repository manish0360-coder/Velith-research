# Proposed DECISIONS.md entry — M8 evaluation identity v2

**Artifact type:** Proposed amendment text (research workspace). **Not** the engineering repository's `DECISIONS.md`, which is unchanged. It enters the repository only by separate authorization (commit and tag gate).
**Amendment package:** 1 of 3. Companions: `M8_IDENTITY_V2_SPEC.md` (successor M8 identity specification) and `M9_SPEC_AMENDMENT_VM2_BLOCK.md` (M9 amendment block).
**Source specification:** `M2-PV-R3_M8-M9-M10_IDENTITY_AMENDMENT_SPEC.md`, SHA-256 `d2c51ec15aa00f1c5924ea6aaed8e6de3f7ba286bfc27b5860b5d792b375888a` (RD-accepted; Q-A to Q-H ratified; SRC delta review APPROVED).
**Engineering baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3`.
**Drafted:** 2026-09-26. **Ratification date:** pending the Amendment Text Freeze Gate.

**Decision number:** assigned at entry. D26–D28 (M2-PV-R) are ratified but not yet entered into the repository's `DECISIONS.md`. This entry's number follows them; it is shown below as **D29 (provisional)**.

**Proposed decision-index row:**

| D29 | M8 evaluation identity v2 (supersedes M8 v1 evaluation identity; resolves CX-A1) | Accepted |

---

## D29 — M8 evaluation identity v2 (supersedes M8 v1 evaluation identity; resolves CX-A1)

**Status:** Accepted (upon ratification at the Amendment Text Freeze Gate). **Supersedes:** the M8 v1 evaluation identity (M8_SPEC §3.5; `EvaluationProvenance`), **for evaluations created after the v2 freeze only**. M8 v1 is not edited and remains the immutable historical specification. **Resolves:** CX-A1 (M8 declared immutable, yet the ratified VerificationManifest binding requires a changed evaluation identity). **Builds on:** D8, D18, D26, D27, D28.

**Evidence / flaw justifying the change (amendment procedure).**
- Evaluations conducted under different verification contracts (TaskSpecs: e.g. different image digests, required tests or protected-surface inputs) are different measurements.
- Under M8 v1 they receive the **same** evaluation identity: v1 identity covers the checkpoint, the corpus partition manifest, arm, base model, evaluation seed and cost guard, but no verification component (`src/velith/evaluation/provenance.py`).
- M8_SPEC declares itself immutable ("Once frozen it is immutable"). The change is therefore made by **versioned supersession**, not by editing M8 v1.
- M8 v1 status: `docs/M8_SPEC.md` as committed at `49d9f75` ("docs: add frozen M8 specification…"), certified at `m8-complete` (`fe2b3d7`). The file's "Status: DRAFT" header is a stale label contradicted by that governance record. The header is not edited by this decision (see Consequences).

**Decision.**

1. **VerificationManifest.**
   - Definition: the canonical mapping `task_identity → TaskSpec digest` over the **held-out evaluation population only** (the tasks of the `HeldOutEvaluationSet` under evaluation).
   - Hash: `verification_manifest_hash` = SHA-256 of its canonical serialization. This reuses the repository's existing canonical rule (`json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"))`, UTF-8, lowercase hex), with no new format.
   - Construction **rejects**, raising `VerificationManifestError` (for use by the M8 runner check): an empty population; any duplicate task identity (whether its digests are equal or differ); a missing TaskSpec; an invalid digest (not 64 lowercase hex); and TaskSpec content that does not re-hash to its digest.
2. **M8 evaluation identity v2.**
   - The hashed `EvaluationProvenance` payload gains exactly two keys:
     - `identity_version = "m8-evaluation-identity-v2"`;
     - `verification_manifest_hash`.
   - The eight v1 components are unchanged in name and meaning: `checkpoint_identity`, `manifest_hash`, `arm`, `base_model`, `eval_seed`, `max_tasks`, `max_attempts_per_task`, `max_tokens`.
   - The v2 payload therefore has exactly ten keys: `identity_version`, `checkpoint_identity`, `manifest_hash`, `arm`, `base_model`, `eval_seed`, `max_tasks`, `max_attempts_per_task`, `max_tokens`, `verification_manifest_hash`.
   - `manifest_hash` keeps its name and its meaning (the full-corpus partition manifest hash). It is distinct from `verification_manifest_hash`, and the two are not interchangeable.
3. **M9 binding.**
   - `PreRegistration` gains `verification_manifest_hash` and carries `spec_version = "m9-spec-frozen-oed7-vm2"`. This is the existing M9 version concept, bumped; no new global version system is introduced.
   - A pre-registration with that `spec_version` binds only to identity-v2 evaluations.
4. **Coordinated migration.** M8 identity v2, the M9 pre-registration amendment and the M10 reconstruction amendment form **one identity migration**: specified, frozen and implemented together. M10 rebuilds the evaluation identity from pre-registration fields at two sites (`analysis/binder.py`, `analysis/executor.py`); both must reconstruct identity v2.
5. **Mixed-version joins are rejected:**
   - v1 pre-registration with v2 code or records;
   - v2 pre-registration with v1 records;
   - v2 with v2 under a different VerificationManifest.
6. **Consistency check.** Before any attempt, the M8 runner requires:
   - `identity_version == "m8-evaluation-identity-v2"`;
   - `verification_manifest_hash` equal to the hash computed from the evaluated held-out set.

   Any mismatch, missing or changed TaskSpec, missing or extra task, or duplicate identity halts with no record written.
7. **Fixtures (universal v2).** There is one v2 identity path for all evaluations, including synthetic fixtures. Fixture corpora supply deterministic synthetic 64-hex digest handles (a test-data change only). No dual v1/v2 code path exists.
8. **Classifier identity** (D27: commit, lock hash, interpreter) enters **neither** `PreRegistration.identity` nor `EvaluationProvenance.identity`. It is recorded in verification evidence. One evaluation of record (every arm and checkpoint under one pre-registration) runs under one classifier identity, enforced through the evidence ledger.
9. **Available-task TaskSpec lineage** is **deferred** as an M2-PV provenance concern and is **not solved** by this decision. The VerificationManifest binds held-out TaskSpecs only. Available-task verification affects evaluation only through memory content, which `checkpoint_identity` binds. A TaskSpec change that leaves every memory episode byte-identical is not reflected in any identity.
10. **No statistical change.**
    - M9 statistical formulas and decision rules are unchanged: outcome encoding (PASSED = 1, else 0), complete-case handling, global-incomplete VOID, OED-7 empty-dataset VOID, GEE, EMM, Wald inference, McNemar (K = 1), Holm correction, α = 0.01, the decision rule, and A0 time-invariance (OED-2).
    - This decision changes identity and version plumbing, not statistical inference.

**Rationale.**
- Binding the verification contract into evaluation identity ensures that differently verified evaluations cannot share an identity and so cannot be joined or pooled. This holds except with negligible probability under the standard SHA-256 collision-resistance assumption.
- Versioned supersession honors M8's immutability.
- Held-out-only scope matches exactly the population M8 evaluates, without widening M8's read surface into the available partition.
- Excluding classifier identity keeps pre-registration sealable before execution.

**Alternatives rejected:**
- A procedural-only verification manifest outside identity (rejected by RD and SRC at M2-PV-R).
- In-place editing of M8 v1 (violates M8 immutability).
- The full-corpus population (widens M8 into the available partition; conservative but unnecessary for held-out identity).
- Actually-evaluated tasks as the population (not pre-registrable).
- Dual v1/v2 code support, or fixtures kept on v1 (a permanent second path, or tests exercising an identity no longer used).
- Classifier identity inside evaluation identity (breaks pre-run sealing).
- A plaintext `verification_manifest_hash` in `AnalysisProvenance` (redundant: covered by the pre-registration and evaluation identities).

**Consequences.**
- **M8 v1** (`docs/M8_SPEC.md`, code at `b14d918` / `m8-complete`) remains historically reproducible. Its identities are never edited, rehashed or converted.
- **No migration.** No real M8 evaluation, M9 pre-registration or M10 analysis artifact exists in the repository (verified at `b14d918`), so there is no migration procedure, no rehashing and no v1→v2 conversion. Every evaluation of record created after the v2 freeze uses identity v2.
- **`EvaluationRecord` is unchanged:** `evaluation_identity` carries the binding by hash inclusion.
- **`AnalysisProvenance` is unchanged:** no plaintext `verification_manifest_hash`.
- **Checkpoint identity and the corpus manifest are unchanged.**
- **The stale "DRAFT" header** of `docs/M8_SPEC.md` is **not** corrected by this decision. It may be corrected only by a separate, explicitly authorized documentation task.
- **Successor texts:** the M8 identity v2 specification (`M8_IDENTITY_V2_SPEC.md`) and the M9 amendment block (`m9-spec-frozen-oed7-vm2`) are the normative texts of this decision. Proposed freeze tags: `m8-identity-v2-frozen`, `m9-spec-frozen-oed7-vm2` (created only at the separately authorized repository gate).
- **Acceptance cases.** The 18 identity cases of the successor specification are **specification-level** cases. They become implementation acceptance tests. None has been implementation-validated.
- **Implementation** requires its own handoff and authorization. This decision authorizes none.
