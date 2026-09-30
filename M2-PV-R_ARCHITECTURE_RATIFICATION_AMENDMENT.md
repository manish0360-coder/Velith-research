# M2-PV-R — Architecture Ratification Amendment

**Document type:** Architecture ratification record (research workspace). **Not implementation. Not a schema change. Not an edit of any frozen artifact.**
**Ratifying authority:** Research Director (decisions recorded here as issued by the RD). **Drafted by:** Chief Systems Engineer. **Scientific review:** Scientific Review Council (Gemini), "M2-PV-R Hard-Stop Ruling — CONDITIONALLY APPROVED FOR ARCHITECTURE RATIFICATION".
**Engineering baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3` (clean).
**Date:** 2026-09-25

**Enactment status.** This document records the RD's architecture ratification decisions and the formal amendments they require. **It does not enact them.** `DECISIONS.md`, `M0_SPEC.md`, `PROJECT_STATE.md`, every M0–M10 specification, every contract and all code are unchanged. Entering D26–D28 into `DECISIONS.md`, and executing the amendments identified in §10, each need a separate authorization.

### Inputs (content-addressed)

| Input | SHA-256 |
|---|---|
| `M2-PV_ARCHITECTURE_RATIFICATION_DRAFT.md` | `0427c40906edaf8bf49899724bfdd395f925fd739c27f6fe1df5dcf3fb1be570` |
| `M2-PV_PRODUCTION_VERIFIER_SPEC_RESEARCH.md` | `dcecb46b0fd2100ddd30b7659aa76abedf3379c1d0af8501a5b32a46baf17c62` |
| `M2-PV_RECONCILIATION_REVIEW.md` | `ce6cf7f42f1bd791238fb271982a2199581f7fe8b23f057fa71e4a816be8425d` |
| SRC M2-PV-R Hard-Stop Ruling (as supplied to the CSE) | `b31818f8bbf7ad4c996d66b4a606ba0e8d70b95283afd1a6ef4f7ab76ec0c69d` |

---

## 0. Findings the Research Director must see first

1. **CX-A1 — M8 immutability vs the mandatory identity binding (unresolved; STOP item for amendment mechanics).**
   - `M8_SPEC.md:10` states: "Once frozen it is immutable; the M8 implementation is *extracted from* it and never redesigns it."
   - The RD-mandated VerificationManifest binding (§6) requires changing `EvaluationProvenance.identity`, an M8 contract.
   - M9 has an established in-place amendment precedent (OED-2, OED-7: re-ratified, re-tagged `m9-spec-frozen-oed2` / `-oed7`). M8 has **none**.
   - `M8_SPEC.md:11` still reads "Status: DRAFT" despite the `m8-complete` tag (F-13), so the authoritative frozen M8 text is itself ambiguous.
   - **This document does not choose the amendment mechanism.** It records the architectural requirement as ratified and the mechanism as an open RD decision (§13, Q-1).
2. **Directive naming correction (not a frozen contradiction).** The directive lists "M6 verifier". In the repository, **M6 is the retrieval substrate** (`docs/M6_SPEC.md`, `src/velith/retrieval/`). The verifier is the M1/M2 `VerifierSandbox` (`src/velith/harness/verifier_sandbox.py`). §10 analyzes both rows under their correct names rather than re-mapping silently.
3. **SRC statements not adopted as written.** Recorded so they are not silently accepted:
   - "ensures 100% cross-machine classification determinism" (SRC §4.2) is **replaced**, per the RD, by an acceptance requirement (§4).
   - The container flags are "complete and sufficient" (SRC §3.3): **not adopted**. Sufficiency against container escape is an open residual (§12, OQ-11).
   - "A1/A2 retrieval semantics remain 100% byte-identical" (SRC §5.1) **is adopted, with its basis stated**: it holds by construction because Option D changes neither retrieval input (`CorpusTask.material`, `Task.prompt`), subject to D-2.

---

## 1. Architecture (ratified)

```
                                   ┌──────────────────────────── TRUSTED ────────────────────────────┐
  CorpusTask {label, material, handle, partition}
     │  material ──► identity (SHA-256) ──► manifest / held-out lock      [unchanged, M4]
     │  material ──► retrieval query (A1/A2)                              [unchanged, M6/M7/M8]
     │
     │ handle  (= TaskSpec digest, D28)
     v
  TaskSpec Registry  (content-addressed; digest recomputed on every read; fail closed)
     │
     │ TaskSpec digest ─────────────────────────────────────────────┐
     v                                                                │
  Real Task Adapter  (registered behind frozen M5 TaskAdapter seam)   │
     │  Task{task_id: spec-independent (D-1), prompt = f(material) (D-2),
     │       repo_path = verified TaskSpec bundle (D-4), hidden_test_command = spec argv}
     │  static wiring guard: never → legacy VerifierSandbox (D-3)
     v                                                                │
  Trusted Host Orchestrator  (process manager only; D26)              │
     │   verifies image digest + platform; applies constraints;        │
     │   fail closed if isolation cannot be established               │
     │                                                                │
  ═══╪════════════════════════ TRUST BOUNDARY ════════════════════════│═══════════════════════
     │   (trust in a container's state ends at the first instruction  │
     │    of candidate code; pre-execution steps remain trusted)      │
     +──── baseline container   (no candidate code)  ── trusted relative to candidate
     +──── candidate container  ┐
     +──── rerun containers     ├─ UNTRUSTED after first candidate-code execution
     +──── (admission runs)     ┘   --network none, --cap-drop ALL, no-new-privileges,
     │                              bounded mem/CPU/PIDs/time/disk/output, no socket,
     │                              no privileged, no DinD, no host mounts
  ═══╪════════════════════════════════════════════════════════════════│═══════════════════════
     v                                                                │
  Evidence   runtime channel (trusted) · pre-execution channel (trusted) ·
     │       baseline channel (trusted rel. candidate) · candidate channel (UNTRUSTED content,
     │       collected by trusted orchestrator only after container teardown)
     v                                                                │
  Hash-locked Verifier Classifier  (D27: clean tree, locked env, self-verified identity)
     │                                                                │
     v                                                                │
  Verdict  (frozen VerdictState; infra raised, never returned)       │
     │                                                                │
     +──── Episode / evaluation evidence (ledger; evidence digest)    │
     │                                                                v
     +──── VerificationManifest identity  {task_identity → TaskSpec digest}  (evaluation population)
                 │  verification_manifest_hash = SHA-256(canonical sorted mapping)
                 +──── PreRegistration.identity        [FORMAL AMENDMENT REQUIRED — M9]
                 +──── EvaluationProvenance.identity   [FORMAL AMENDMENT REQUIRED — M8; CX-A1]
                                   └──────────────────────────────────────────────────────────────────┘
```

**Legend:**
- **TRUSTED:** orchestrator, TaskSpec registry, adapter, classifier, evidence ledger, pre-execution steps, container runtime (stated trust assumption: its API access is root-equivalent on the host).
- **UNTRUSTED:** the candidate patch, and every process, file and output inside a candidate or rerun container from the first execution of candidate code.
- **TRUST BOUNDARY:** the double rule above.

---

## 2. D26 — Real-task verification execution boundary (RATIFIED by the RD; not yet entered into `DECISIONS.md`)

> ## D26 — Real-task verification execution boundary (scoped supersession of D19 for real repository tasks)
>
> **Status:** Ratified by the Research Director (M2-PV-R). **Supersedes:** D19, **only** for the verification of real repository-level tasks. D19 remains authoritative and unchanged for the legacy synthetic-fixture verifier (`VerifierSandbox`: two-phase `unshare -n` under `CAP_SYS_ADMIN`, single container), including `M2_SPEC.md:232` ("Single-container — no orchestrator/compose split"), which D26 scopes identically.
>
> **Evidence / flaw (amendment procedure, `DECISIONS.md:479`).**
> - Real tasks require task-specific interpreters, native libraries and dependency sets that cannot co-reside in the single Velith image.
> - The M2 feasibility prototype (`b14d918`, evidence manifest `30c59a45db9e06556bc0a0529b290d43c7a4163066b3b3a4c138f97eaa6255f7`) demonstrated, for one task and benign candidates only, sealed digest-pinned network-less execution in separate task containers driven by a host-side orchestrator.
>
> **Decision.**
> 1. **Placement (AR-2):** trusted host verifier orchestrator → digest-pinned task container → candidate execution.
> 2. **Before execution:** the image digest (`image@sha256:…`) and the declared platform are verified. On mismatch the orchestrator raises.
> 3. **Fresh container per execution:** baseline, candidate, confirmation re-run and admission runs each use a new container from the pinned digest, removed unconditionally. No container is reused after candidate code executed in it.
> 4. **Mandatory constraints:**
>    - `--network none`; `--cap-drop ALL`; `--security-opt no-new-privileges`;
>    - bounded memory (swap disabled), CPU, PID count and wall time;
>    - bounded disk and captured output where the runtime supports it.
> 5. **Prohibited:** `--privileged`; any Docker socket or container-runtime access from a task container; Docker-in-Docker; host filesystem (bind) mounts. Inputs are copied into a created, not-started container; outputs are copied out only after full teardown.
> 6. **No candidate access** to the trusted experience/episode store, evaluation sink, pre-registration, corpus, TaskSpec registry or evidence ledger. None of these exists inside any task container, nor in any namespace shared with one.
> 7. **No install, build or network activity** during verification. The published image is the complete environment. D19's two-phase intent is preserved by construction: the proposer's network is outside every task container.
> 8. **Fail closed:** if any required constraint cannot be applied and verified (runtime inspection of the created container), the orchestrator raises `SandboxExecutionError` and never executes candidate code under weaker isolation.
> 9. **Classification (SRC-mandated amendment):** the host orchestrator **shall execute verdict classification only through the hash-locked verifier classifier environment specified by D27.**
> 10. **Role of the host:** the host is the **process manager**. It is **not** the scientific source of candidate test-execution evidence; that evidence originates only inside task containers (D27 A).
>
> **Trust boundary.**
> - **Trusted:** the orchestrator and its D27 environment; the container runtime (stated assumption: root-equivalent host access); the TaskSpec registry; the evidence ledger; trusted runner artifacts; the task image as an environment after admission.
> - **Untrusted:** the candidate patch, and everything in a candidate or rerun container from the first execution of candidate code.
> - **Evidence:** untrusted-side evidence may lower a verdict. It may support `PASSED` only through the integrity checks the frozen M2-PV specification will define, and then only with the residuals of §7.
>
> **Alternatives rejected:**
> - AR-1, in-container execution: environment infeasibility, and co-location with the experience store.
> - AR-3, socket-mounted sibling containers: root-equivalent host control reachable from a container.
> - AR-4, Docker-in-Docker or privileged mode.
>
> Rootless and hardened runtimes (AR-5/AR-6) are deferred options, not rejected.
>
> **Consequences.**
> - `docker-compose.yml` and `docker/verifier.Dockerfile` are unchanged.
> - The legacy verifier is confined to synthetic fixtures.
> - CI exercises real-task verification only where a runtime and the images are available; elsewhere it capability-skips with an explicit reason, never a silent pass.
>
> **Not decided by D26:** runner mechanics; R_b, R_g, R_c; limit values; non-root, read-only-root and hardened runtime; protected-surface policy; TaskSpec schema (§12).

## 3. How D26, D27 and D28 fit together (cross-decision consistency)

- **D26 → D27.** D26 fixes *where* candidate code runs and requires that classification runs only through D27's hash-locked classifier. D27 fixes *who judges*. Neither decision permits the host's ambient state to influence a verdict.
- **D28 → D26/D27.** D28 supplies the TaskSpec that D26's orchestrator executes and D27's classifier interprets. The TaskSpec digest is verified at the registry, at the adapter and at the verifier.
- **D28 → §6.** The TaskSpec digests carried by `CorpusTask.handle` form the VerificationManifest, which binds the verification contract into evaluation identity.
- **Checked against the frozen system:**
  - **M7 shared retrieval:** no retrieval input changes (D-2).
  - **M8 evaluation identity:** requires the §6 amendment; mechanism open (CX-A1).
  - **M9 statistical model:** unchanged (PASSED = 1, else 0; complete-case; VOID rules).
  - **D8:** held-out lock unaffected; pilot hygiene P-1 proposed.
  - **D13, D18, D19:** scoped clarifications and supersession.
  - **D21:** residual accepted (§8).
- **No contradiction** among D26, D27 and D28 themselves was found. The only unresolved frozen conflict is CX-A1 (§0, §11).

## 4. D27 — Real-task verdict source-of-truth (RATIFIED by the RD; not yet entered into `DECISIONS.md`)

> ## D27 — Real-task verification: evidence, classification and orchestration (clarifies M0 §6 and D13's verifier sentence)
>
> **Status:** Ratified by the Research Director (M2-PV-R). **Clarifies, for real-task verification under D26 only:**
> - `M0_SPEC.md:120` ("…never as the source of truth for a verdict");
> - `PROJECT_STATE.md:127`;
> - `DECISIONS.md:263` (D13: "The deterministic verifier … runs inside a Linux container").
>
> None is edited. All three remain authoritative for the Velith image, CI gates and the legacy fixture verifier.
>
> **Decision.** A real-task verdict is produced by three strictly separated functions:
> - **A. Task execution evidence.** Produced **only** inside the admitted, digest-pinned task container, plus the container runtime's inspection of it. This is the sole empirical input about candidate behavior.
> - **B. Verdict classification.** Performed **only** by the trusted, hash-locked Velith verifier classifier: a deterministic mapping from trusted evidence + TaskSpec + frozen rules → `Verdict`.
> - **C. Host orchestration.** A process-management function only: create, constrain, feed, tear down and collect. It contributes no evidence and no judgment.
>
> **The classifier MUST:**
> 1. run from a clean git tree at a recorded commit;
> 2. run under the exact locked Python environment (D13 target 3.12; hash-locked dependencies);
> 3. verify its own environment identity before classifying;
> 4. refuse evaluation-of-record execution if required identity cannot be verified;
> 5. use only explicit, recorded inputs;
> 6. prohibit ambient host state (host packages, environment variables, user configuration, working directory, locale or time zone) from affecting classification;
> 7. record classifier identity (commit, lock hash, interpreter version) in the evidence of every verification;
> 8. deterministically map trusted evidence + TaskSpec + frozen rules to a `Verdict`.
>
> **Source of truth.** The scientific source of truth is **A interpreted by B**. The host is **not** the scientific source of truth.
>
> **Determinism.** **Cross-machine deterministic classification is a mandatory acceptance requirement to be demonstrated by the M2-PV validation matrix.** It is an acceptance requirement. It has **not** yet been demonstrated: M2 showed one-host reproducibility for one task only.
>
> **Consequences.** Classifier identity becomes part of verification provenance. Whether it also enters evaluation identity remains open (OQ-9).

## 5. D28 — TaskSpec digest transport: Option D (RATIFIED by the RD; not yet entered into `DECISIONS.md`)

> ## D28 — TaskSpec digest transport (handle-carried, registry-resolved)
>
> **Status:** Ratified by the Research Director (M2-PV-R), subject to D-1 to D-4.
>
> **Decision.**
> - Transport chain: `CorpusTask.handle` → content-addressed TaskSpec registry → TaskSpec digest → real-task adapter (registered behind the frozen M5 `TaskAdapter` seam) → `Task`.
> - The digest is recomputed at the registry read, at the adapter and at the verifier. Any mismatch is fail-closed.
> - Grounded in frozen semantics: "a *verification handle* owned by the verifier" (`M4_SPEC.md:34`); the adapter turns "a `CorpusTask`'s opaque handle into the concrete inputs the frozen proposer and verifier consume" (`M5_SPEC.md:56-57`); `repo_path` + `hidden_test_command` are the `Task`'s verification handle (`batch/adapter.py:8`).
>
> **Mandatory conditions.**
> - **D-1:** `Task.task_id` remains spec-independent and stable. Re-pinning a TaskSpec never changes `task_id`.
> - **D-2:** `Task.prompt` is a pure function of `material`. TaskSpec test data, hidden tests, gold patches and protected-surface details must never enter `material` or `prompt`.
> - **D-3:** a static wiring guard prevents real-task `Task` instances from reaching the legacy `VerifierSandbox`. Real-task `Task` instances use only the production container verifier/orchestrator.
> - **D-4:** the `Task.repo_path` interpretation is formally documented as follows.
>
> **Interpretation note — D-4, proposed wording for the future M2-PV specification:**
> "For real-task verification, `Task.repo_path` is the path of the verified, content-addressed TaskSpec bundle, i.e. *the source bundle copied by the verifier* (`task.py:50`: 'the source the verifier copies — it never operates on this path in place'). It is not a git working copy. The legacy fixture interpretation is unchanged."
>
> **Invariants:**
> - Option D does **not** modify `CorpusTask.material`, does **not** alter task identity (`manifest.py:39-46`), and does **not** modify retrieval semantics.
> - Retrieval inputs are exactly `CorpusTask.material` (`evaluation/attempt.py:125`) and `episode.prompt` (`retrieval/retriever.py:27`). Neither is touched.
> - The TaskSpec used at evaluation **excludes the gold patch**, which exists only in admission evidence.

## 6. VerificationManifest identity binding (RATIFIED architectural identity boundary; amendments pending)

**The procedural-only manifest is REJECTED** (RD; SRC §6). The binding is an **architectural identity boundary**.

**Definitions:**
- `VerificationManifest` = the deterministic mapping `task_identity → TaskSpec digest` over the **evaluation population**.
- `verification_manifest_hash` = SHA-256 of the canonical serialization of that mapping, sorted by `task_identity`. It uses the same canonical rule as the frozen episode and evaluation identities: sorted keys, tight separators, UTF-8 (`episode.py` `compute_content_hash`; `evaluation/provenance.py`).

**Required propagation:**

```
different TaskSpec ─► different verification_manifest_hash ─► different PreRegistration.identity
                                                           └─► different EvaluationProvenance.identity ─► distinct evaluation
```

**Why both identities must change together (repository fact).** M10 reconstructs every expected `EvaluationProvenance.identity` **from the PreRegistration's fields** (`analysis/binder.py:74-85`; `analysis/executor.py:115`). M9 requires the pre-registration to be "bound to exactly the M8 evaluation identity components" (`M9_SPEC.md:325`). So the component must enter **PreRegistration**, **EvaluationProvenance**, and **M10's reconstruction** in one coordinated amendment. Amending one alone would break the M10 join.

**Design observation (not a decision).** Under D28 the held-out `CorpusTask.handle` values *are* the TaskSpec digests. So the VerificationManifest is computable from the frozen held-out set itself (`evaluation/heldout_set.py`), without consulting the registry. That would let a future M8 consistency check (analogous to `_require_consistent`, `evaluation/runner.py:41-52`) verify `EvaluationProvenance.verification_manifest_hash` against the set being evaluated. This mechanism is for the future amendment to decide.

**Not implemented and not schema-changed by this document.** Required amendments are classified in §10. Amendment mechanics are open: CX-A1 (§0) and Q-1 and Q-2 (§13).

## 7. E12 / E13 — Accepted scientific limitations

Recorded as **ACCEPTED SCIENTIFIC RESIDUALS**. Evidence: sandbox experiments (CPython 3.10.12, pytest 7.3.0, no container) in `M2-PV_RECONCILIATION_REVIEW.md` Appendix A. Confirmed by the SRC (§2 of its ruling).

| ID | Finding | Status |
|---|---|---|
| **E12a** | Collector-memory protection was demonstrated under the tested process-isolated architecture: the collector never imported candidate code. | Demonstrated (sandbox) |
| **E12b** | Process isolation does **not** eliminate worker-side result-channel forgery. Candidate code can manipulate test-return behavior before IPC transmission. | Accepted residual |
| **E12c** | Process isolation does **not** establish semantic task integrity. Candidate code may inspect caller or test-harness context and special-case expected behavior. | Accepted residual |
| **E13a** | Must-fail canaries detect blanket, canary-unaware forgery. | Demonstrated (sandbox) |
| **E13b** | Targeted, channel-consistent forgery can bypass the tested canary and cross-channel checks. | Accepted residual |

**Explicitly rejected claims:**
- "100% security";
- "forgery is impossible";
- "container boundary proves semantic correctness";
- "A2 is 100% protected from adversarial candidate behavior".

**Required scientific statement (binding on every consumer-facing description of a verdict):**

> **PASSED** means that the candidate passed the required tests in the verified environment with no detected inconsistency under the frozen verifier rules.
>
> PASSED does **NOT** prove:
> - absence of all test-result forgery;
> - absence of all semantic manipulation;
> - absence of arbitrary adversarial candidate behavior;
> - correctness outside the tested verification surface.
>
> These are accepted residuals, not reasons to silently expand the claim.

## 8. D21 — Real-task secondary suite (Accepted residual)

- For standard SWE-bench real tasks, **no equivalent frozen secondary suite is currently available.**
- Therefore `secondary_passed = None` for real-task evaluations where no valid secondary suite exists.
- **No secondary metric is invented. No replacement model-gap metric is created.**
- The loss of the D21 model-gap safeguard is an **explicit scientific residual** to be recorded in the eventual M8/M9 provenance. The recording mechanism is open (OQ-7), because `PreRegistration` and `EvaluationRecord` are `extra="forbid"`.
- **Consequence stated, not hidden:** with `secondary_passed = None`, A2 admits every uncontradicted `PASSED` (`arms/filters.py:48-60`). The §7 residuals (E12b, E12c, E13b) therefore can enter A2 memory undetected.

## 9. Base-rate pilot (APPROVED)

**Sequencing (ratified):** architecture ratification → **5-task zero-experience base-rate pilot** → M2-PV production verifier automation.

**Pilot properties (ratified):**
- exactly **5** real SWE-bench tasks, unless a later approved research amendment changes this;
- current proposer;
- zero experience;
- no arm-memory writes; no episode-store writes;
- no contamination of M8/M9 evaluation data;
- an engineering feasibility measurement only: **not** evidence for A1/A2 effectiveness, **not** a production evaluation, **not** a substitute for verifier validation.

**Purpose:** only to measure whether the current proposer can produce usable candidate patches on real tasks, before investing in full production verifier automation.

**CSE-proposed additional conditions (NOT ratified; submitted for RD decision, Q-5 to Q-7):**
- **P-1 — held-out hygiene.** The 5 pilot tasks are recorded by task identity and **excluded from any future held-out partition**. Otherwise prompt or pipeline design informed by those tasks would contaminate held-out evaluation (D8.3 intent).
- **P-2 — pre-declared measurements.** For each task:
  - patch produced (yes/no);
  - applies (`PATCH_APPLY_FAILED` or not);
  - verified outcome under the frozen M2 experiment probe (baseline control included);
  - tokens and latency.
- **P-3 — statistical honesty.** With n = 5, 0/5 successes bounds the true solve rate only to ≤ 45% at 95% confidence (1 − 0.05^(1/5) = 0.451). The pilot can reveal a **usability failure** (no applicable patches). It cannot estimate a solve rate or confirm a floor effect. Its interpretation rule must be pre-declared before it runs (OQ-15).
- **P-4 — artifact location.** Pilot code and evidence stay in the research workspace or under `experiments/` by explicit authorization. The frozen `experiments/m2_container_prototype/probe.py` is **reused unmodified**, never edited.

---

## 10. Mandatory contract impact analysis

Classification: **CLARIFICATION** · **FORMAL AMENDMENT REQUIRED** · **NO CHANGE** · **OPEN**. Nothing below is changed by this document.

| Artifact / frozen rule | Current state | Required future change | Classification |
|---|---|---|---|
| **D19** (`DECISIONS.md:376-388`) | Single-container, two-phase `unshare -n`; sidecar and socket rejected | New entry **D26** superseding D19 for real tasks only; D19 unchanged for fixtures | **FORMAL AMENDMENT REQUIRED** (DECISIONS amendment procedure) |
| **M0 §6** (`M0_SPEC.md:120`) | "host Python … never as the source of truth for a verdict" | **D27** scoped clarification (A/B/C separation) | **CLARIFICATION** |
| **D13** (`DECISIONS.md:263`) | "verifier … runs inside a Linux container" | Covered by **D27** scope | **CLARIFICATION** |
| **D18** (`DECISIONS.md:362`) | L1–L4; env pinning; same-machine CI assertion | L4 environment now includes task image digest + classifier identity; cross-machine determinism is an acceptance requirement (D27) | **CLARIFICATION** |
| **D21** (`DECISIONS.md:404`) | `secondary_passed` identity; model-gap via secondary suite | Real tasks: `secondary_passed = None`; residual recorded | **NO CHANGE** to contract; residual-recording mechanism **OPEN** (OQ-7) |
| **CorpusTask** (`corpus/loader.py:35-51`) | `label, material, handle, partition` | `handle` carries the TaskSpec digest, per its frozen meaning | **NO CHANGE** |
| **Task** (`task.py:45-61`) | `repo_path`, `hidden_test_command` = verification handle | `repo_path` interpretation note (D-4) | **CLARIFICATION** |
| **PreRegistration** (`analysis/preregistration.py:78-103`) | Identity over the declared M9 design components; `extra="forbid"`; `SPEC_VERSION = "m9-spec-frozen-oed7"` | Add `verification_manifest_hash` to identity components (§6) | **FORMAL AMENDMENT REQUIRED** (M9 in-place amendment precedent: OED-2/OED-7 + re-freeze tag) |
| **EvaluationProvenance** (`evaluation/provenance.py`) | Identity "over exactly those components": checkpoint, manifest hash, arm, base model, eval seed, cost limits | Add `verification_manifest_hash` (§6) | **FORMAL AMENDMENT REQUIRED** — mechanism **OPEN** (CX-A1: M8 "immutable", no precedent) |
| **EvaluationRecord** (`evaluation/record.py:35-49`) | Carries `evaluation_identity`; no output or provenance field | None: the binding reaches records through `evaluation_identity`; the evidence link lives in the verifier ledger | **NO CHANGE** |
| **M8 evaluation identity** (M8_SPEC §3.5) | As EvaluationProvenance | As EvaluationProvenance, plus an M8 consistency check of the manifest hash against the evaluated set (design OPEN) | **FORMAL AMENDMENT REQUIRED** — mechanism **OPEN** (CX-A1) |
| **M9 pre-registration identity** (M9_SPEC §3.3, :325) | Mirrors M8 identity components | Mirror the new component | **FORMAL AMENDMENT REQUIRED** |
| **M10 binder / executor** (`analysis/binder.py:74-85`, `analysis/executor.py:115`) | Reconstructs `EvaluationProvenance` from PreRegistration fields | Must pass the new component in the reconstruction | **FORMAL AMENDMENT REQUIRED** (code follows the M8/M9 amendment; not listed in the directive but required by §6) |
| **M4 corpus manifest** (`corpus/manifest.py:103-112`) | Hash over `identity → partition` | None (VerificationManifest is a separate identity) | **NO CHANGE** |
| **M5 adapter** (`batch/adapter.py:26-31`) | Seam + fixture adapter; real adapters are registrations | New real-task adapter registration behind the unchanged seam (separately authorized) | **NO CHANGE** (seam) |
| **"M6 verifier"** (directive label) → **M6 retrieval substrate** (`retrieval/`) | Query = `material`; episode text = `prompt` | None (D-2 guarantees inputs unchanged) | **NO CHANGE** |
| **M1/M2 verifier** (`harness/verifier_sandbox.py`) — the actual verifier | Legacy fixture verifier under D19 | None; confined to fixtures; D-3 guard lives in composition code | **NO CHANGE** |
| **M7 arm memory** (`arms/`) | Shared-retrieval invariant; A2 admits non-flaky `PASSED` / `FAILED` | None; A2 admission of residual-affected `PASSED` is recorded (§8) | **NO CHANGE** |
| **M8 held-out evaluation** (`evaluation/runner.py`, `attempt.py`) | Unhandled `SandboxExecutionError` → abort → VOID | Runner consistency check for the manifest hash (with the identity amendment); raise-only infra and its VOID consequence retained | **FORMAL AMENDMENT REQUIRED** (with identity); VOID policy **NO CHANGE** |
| **M9 statistical analysis** (encoding, GEE, Holm, decision) | PASSED = 1 else 0; complete-case; VOID rules | None to the statistical model | **NO CHANGE** |
| **M2_SPEC §10** (`M2_SPEC.md:232`) | "Single-container — no orchestrator/compose split" | Scoped by D26 exactly as D19 | **CLARIFICATION** |
| **PROJECT_STATE.md:127** | "verdict is produced inside the container" | Covered by D27 | **CLARIFICATION** |
| **M2 prototype** (`experiments/m2_container_prototype/`) | Frozen feasibility evidence | None; reused unmodified by the pilot (P-4) | **NO CHANGE** |
| **M8_SPEC header** (`M8_SPEC.md:11`) | "Status: DRAFT" despite `m8-complete` | Status clarification needed before any M8 amendment (CX-A1) | **OPEN** |

## 11. Contradictions and governance findings

| ID | Finding | Status |
|---|---|---|
| **CX-A1** | M8 is declared immutable (`M8_SPEC.md:10`) with no amendment precedent, yet the ratified identity binding requires changing `EvaluationProvenance.identity`. M8's header still says DRAFT. | **UNRESOLVED — STOP for amendment mechanics** (Q-1, Q-2) |
| CX-R1 | D13's verifier sentence conflicts with AR-2 | Resolved in scope by **D27** (ratified) |
| CX-1 / CX-2 | D19 single-container; M0 §6 host source-of-truth | Resolved in scope by **D26** / **D27** (ratified) |
| N-1 | Directive label "M6 verifier" does not match the repository (M6 = retrieval) | Recorded (§0.2); both rows analyzed |
| N-2 | SRC overclaims ("100% cross-machine determinism", "complete and sufficient" flags) | Not adopted (§0.3) |

## 12. Open questions (preserved, not answered)

| ID | Question |
|---|---|
| OQ-1 | **Candidate-only deterministic infra faults** that leave no trusted-channel trace: do they exist on the target host? (They would be misattributed as `FAILED`.) |
| OQ-2 | **Timeout / OOM classification edge cases:** container-limit vs host/VM OOM discrimination on WSL2; budget formula; host-contention timeouts. |
| OQ-3 | **Exact retry policy:** R_i (infra retries), R_c (confirmation), independence of transient faults; VOID on exhaustion under frozen M8. |
| OQ-4 | **Protected-surface policy:** T-2 test-root definition; tests outside declared roots; read-only mount alternative. |
| OQ-5 | **Runner / import resolution:** trusted launcher in the task image; `-P` on 3.11+; import mode per task; plugin set. |
| OQ-6 | **Test canary design:** co-location with candidate-importing processes; exit-code rule with must-fail canaries; detection limits (E13b). |
| OQ-7 | **Secondary-suite absence:** where the D21 residual is recorded in M8/M9 provenance, given `extra="forbid"` schemas. |
| OQ-8 | **Proposer leakage:** future git history in task images, upstream lookup (outside the verifier boundary). |
| OQ-9 | **Verification contract identity details:** (a) whether classifier identity (D27) enters evaluation identity; (b) whether the available-partition TaskSpecs, which shape A1/A2 memory, need binding beyond checkpoint identity (they reach it only if verdict evidence digests enter `verdict_output`, per the unfrozen PV-PROV-004); (c) exact definition of "evaluation population". |
| OQ-10 | **Cross-machine determinism validation:** hosts, matrix, pass criterion. |
| OQ-11 | **Container escape residual:** sufficiency of the D26 constraints against kernel/runtime vulnerabilities; hardened runtime option. |
| OQ-12 | **Exact TaskSpec schema** (fields, canonical serialization, exclusion of the gold patch, version field). |
| OQ-13 | **Exact M8/M9 identity amendment mechanics** (CX-A1): M8 amendment procedure, field naming, spec re-freeze tags, M10 change set, the fate of existing fixture-era pre-registrations. |
| OQ-14 | Non-root, read-only-root and limits compatibility with SWE-bench images. |
| OQ-15 | Pilot interpretation rule: what outcome of the 5-task pilot triggers which next action (must be declared before the pilot runs). |

## 13. Questions for Research Director decision (next gate)

1. **Q-1 (CX-A1):** by what mechanism is M8's "immutable" evaluation identity amended? (a) An M8 in-place amendment following the M9 OED precedent, with a re-freeze tag; (b) a superseding DECISIONS entry defining "evaluation identity v2", with M8_SPEC left intact; (c) another.
2. **Q-2:** resolve the M8_SPEC header status ("DRAFT" vs `m8-complete`) before any M8 amendment.
3. **Q-3:** authorize entering D26–D28 into `DECISIONS.md` (a repository change, requiring separate commit authorization)?
4. **Q-4:** authorize the M8/M9/M10 identity-amendment specification work (spec only), after Q-1?
5. **Q-5 to Q-7:** accept or reject pilot conditions **P-1** (held-out exclusion), **P-2** (pre-declared measurements) and **P-3** (statistical honesty and pre-declared interpretation rule).
6. **Q-8:** authorize the pilot itself (location, task selection procedure, budget), which the ratification approves but does not execute.

## 14. Exact next gate

**Gate M2-PV-R2 — RD rulings on Q-1 to Q-8.** Then, in order:
1. the base-rate pilot (5 tasks, experiment-only, under the P-conditions if ratified);
2. the M8/M9/M10 identity-amendment specification;
3. M2-PV specification v2 incorporating D26–D28, §7 and §8;
4. the SRC delta review;
5. the validation matrix;
6. the M2-PV freeze;
7. only then, production verifier implementation.

---

## RATIFICATION STATUS

STATUS:
CONDITIONALLY RATIFIED ARCHITECTURE

D26:
RATIFIED — real-task scoped supersession of D19

D27:
RATIFIED — M0 §6 / D13 real-task clarification

D28:
RATIFIED — Option D, subject to D-1 through D-4

E12/E13:
ACCEPTED SCIENTIFIC RESIDUAL

VerificationManifest:
MANDATORY IDENTITY BINDING

D21:
ACCEPTED REAL-TASK SCIENTIFIC RESIDUAL

Base-rate pilot:
APPROVED — 5-task feasibility pilot before production verifier automation

Implementation:
NOT AUTHORIZED BY THIS DOCUMENT

Schema modification:
NOT AUTHORIZED BY THIS DOCUMENT

Repository modification:
NOT AUTHORIZED BY THIS DOCUMENT
