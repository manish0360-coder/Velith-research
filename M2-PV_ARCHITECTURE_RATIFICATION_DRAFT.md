# M2-PV-R — Architecture Ratification Draft

**Status:** DRAFT FOR RESEARCH DIRECTOR RATIFICATION. **Nothing in this document is ratified, enacted, or frozen.** `DECISIONS.md`, `M0_SPEC.md` and every M0–M10 artifact are unchanged.
**Repository baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3` (clean).
**Inputs:** `M2-PV_PRODUCTION_VERIFIER_SPEC_RESEARCH.md` (DRAFT), `M2-PV_RECONCILIATION_REVIEW.md`, the Gemini SRC review, and the repository (read-only).
**Author:** Chief Systems Engineer.
**Proposed decision numbers** D26–D28 are provisional; the Research Director assigns numbers at ratification.

This draft proposes three coordinated decisions:

| # | Proposed decision | Nature |
|---|---|---|
| 1 | D26 — Real-task verification execution boundary | Scoped supersession of **D19** (real repository tasks only) |
| 2 | D27 — Verdict source-of-truth for real-task verification | Scoped clarification of **M0 §6**, and of the verifier sentence of **D13** (see §4, CX-R1) |
| 3 | D28 — TaskSpec digest transport | Contract-usage decision; **no frozen schema change** under the recommended option |

---

## 1. D26 — D19 supersession for real-task verification (proposed text)

> ## D26 — Real-task verification execution boundary (supersedes D19 for real repository tasks only)
>
> **Status:** PROPOSED — not ratified. **Supersedes:** D19, **only** for the verification of real repository-level tasks. D19 remains authoritative, unchanged, for the legacy synthetic-fixture verifier (`VerifierSandbox`: two-phase `unshare -n` under `CAP_SYS_ADMIN`, single container).
>
> **Evidence / flaw justifying the change (amendment procedure, DECISIONS.md:479).**
> (i) Real repository tasks require task-specific execution environments (interpreter versions, native libraries, pinned dependency sets) that cannot co-reside in the single Velith image. D19's single-container model (DECISIONS.md:380; M2_SPEC §10: "Single-container — no orchestrator/compose split") cannot execute them.
> (ii) The M2 feasibility prototype (commit `b14d918`, freeze record, evidence manifest `30c59a45db9e06556bc0a0529b290d43c7a4163066b3b3a4c138f97eaa6255f7`) demonstrated, for one task and benign candidates only: sealed, digest-pinned, network-less execution in a separate task container, driven by a host-side orchestrator.
>
> **Decision.**
> 1. **Placement (AR-2).** A trusted **verifier orchestrator** launches task containers through the local container runtime. Candidate code never executes in the Velith container, nor in any container, user namespace or mount namespace that holds the episode store, evaluation sink, corpus, pre-registration or evidence ledger.
> 2. **Environment.** Every execution uses a task-specific image referenced **by digest** (`image@sha256:…`). Before any container is created, the orchestrator verifies that the local image carries exactly that digest and the declared platform. Otherwise it raises.
> 3. **Fresh container per execution.** Each baseline run, candidate run, confirmation re-run and admission run uses a new container created from the pinned digest. No container is reused after candidate code has executed in it. Every container is removed unconditionally.
> 4. **Mandatory candidate-container constraints:** `--network none`; `--cap-drop ALL`; `--security-opt no-new-privileges`; bounded PIDs, memory with swap disabled (`--memory` = `--memory-swap`), CPU and wall-clock time; bounded writable storage and bounded captured output. **Prohibited:** Docker socket access from any task container, `--privileged`, Docker-in-Docker, and host bind mounts. Inputs are copied into a created, not-yet-started container; outputs are copied out only after the container has fully stopped.
> 5. **Fail closed.** If any constraint in point 4 cannot be applied or verified (via the runtime's own inspection of the created container), the orchestrator raises `SandboxExecutionError` and never runs candidate code under weaker isolation. This is D19's mandatory-isolation invariant, carried forward.
> 6. **Two-phase intent preserved by construction.** The proposal step's network access is outside every task container; task containers have no network phase. No install, build or network step occurs at verification time. The published image is the complete environment.
> 7. **Trust boundary.**
>    - **Trusted:** the orchestrator process and its pinned environment (D27); the container runtime (the orchestrator's runtime access is root-equivalent on the host and is a stated trust assumption); the content-addressed TaskSpec registry and evidence ledger; the trusted runner artifacts.
>    - **Trusted as an environment only after admission:** the task image at its digest.
>    - **Untrusted:** the candidate patch, and every process, file and output in a candidate container from the first execution of candidate code onward.
>    - **Evidence:** from the untrusted side, evidence may lower a verdict. It may yield `PASSED` only through the integrity checks the M2-PV specification freezes.
> 8. **Orchestrator identity.** The orchestrator's identity (per D27) is recorded in every verification's evidence.
>
> **Alternatives rejected.**
> - Status-quo in-container execution (environment infeasibility; places untrusted code beside the experience store).
> - Sibling containers via a Docker socket mounted into the Velith container (root-equivalent host control reachable from a container that historically executed candidate code).
> - Docker-in-Docker / privileged mode (defeats isolation).
> - Rootless runtimes and hardened runtimes (gVisor/Kata) are **not rejected**; they are deferred as options pending feasibility on the target host.
>
> **Consequences.**
> - `docker-compose.yml` and `docker/verifier.Dockerfile` are unchanged by this entry.
> - The legacy verifier is confined to synthetic fixtures and must never receive a real-task `Task`.
> - D13's single-machine discipline and D14's non-goals are unaffected.
> - CI can exercise the orchestrator only where a container runtime and the task images are available. Where they are not, tests are capability-skipped with an explicit reason (D19 CI precedent) and never silently passed.
>
> **Explicitly not decided by this entry:**
> - runner mechanics (launcher, explicit configuration, import mode, canaries, result-consistency rule);
> - attribution and confirmation counts (R_c), admission counts (R_b, R_g);
> - timeout and memory budgets;
> - non-root / read-only-root / hardened-runtime requirements;
> - protected-surface rule;
> - TaskSpec schema.
>
> These belong to the M2-PV specification, and several require empirical validation before freeze.

## 2. D27 — M0 §6 clarification (proposed text)

**The conflict precisely.**
- `M0_SPEC.md:120`: the host Python is used "only for editor tooling and pre-commit, never as the source of truth for a verdict."
- `PROJECT_STATE.md:127`: "the verdict is produced inside the container; the host is never the source of truth."
- `DECISIONS.md:263` (D13): "The deterministic verifier … runs inside a Linux container for bit-for-bit reproducibility."

Under D26 the **classification** step, which maps evidence to a `Verdict`, runs in the orchestrator outside any container. Read literally, that conflicts with all three statements.

> ## D27 — Verdict source-of-truth for real-task verification (clarifies M0 §6 and the verifier sentence of D13)
>
> **Status:** PROPOSED — not ratified. **Clarifies:** M0_SPEC §6 ("host … never as the source of truth for a verdict") and D13's verifier sentence, **for real-task verification under D26 only**. Neither is edited. Both remain authoritative for the Velith image, the CI gates and the legacy fixture verifier.
>
> **Evidence / flaw.** D26 places verdict classification outside any container. The intent of M0 §6 and D13 is reproducibility: nothing ambient on the developer's host may influence a verdict. That intent is preserved only if the classification step is itself pinned and identified.
>
> **Decision.** A real-task verdict is the output of three strictly separated parts:
> - **(A) Task-container execution evidence.** Produced **only** inside digest-pinned task containers (D26), plus the container runtime's inspection of those containers. This is the sole empirical input about the candidate's behavior.
> - **(B) Trusted verifier classification.** A deterministic function from (A), the TaskSpec and the frozen classification rules to a `Verdict`. It is computed by the Velith verifier code at a **recorded commit**, from a **clean working tree**, in a **pinned, hash-locked Python 3.12 environment** (D13). It receives **explicit inputs only**. Its identity (Velith commit, lock-file hash, interpreter version) is recorded in the evidence of every verification. An evaluation of record refuses to run from a dirty tree or an unlocked environment.
> - **(C) Ambient host state.** Host-installed packages, host environment variables, user configuration, working directory and host locale or time zone. It must **not** influence (A) or (B). The orchestrator passes an explicit environment allow-list to containers and reads no ambient configuration for classification.
>
> The scientific source of truth is **(A) interpreted by (B)**. **The host is not the source of truth.** It is the place where a pinned, identified, deterministic classifier runs. The same (A) and TaskSpec under the same (B) identity must yield the same `Verdict` on any machine.
>
> **Consequences.**
> - The verifier's implementation identity becomes part of verification provenance.
> - Whether it also enters M8 *evaluation identity* is not decided here (open question OQ-13; D28 §3.6).
> - `PROJECT_STATE.md:127` remains a correct description of the frozen M0–M10 pipeline and is not altered.

## 3. D28 — TaskSpec digest transport

### 3.1 Facts that constrain every option (repository, read-only)

| Fact | Evidence |
|---|---|
| Retrieval query = `CorpusTask.material` | `evaluation/attempt.py:125` → `retrieval/query.py:40-41` → `retriever.py:47` |
| Episode text embedded for retrieval = `episode.prompt` | `retrieval/retriever.py:21-27` |
| Proposer reads only `task.prompt` and `task.task_id` | `agent/proposer.py:97`, `:117` |
| Task identity = SHA-256 of `material` only; the label is excluded | `corpus/manifest.py:39-46` |
| Manifest hash = SHA-256 over sorted `identity → partition` only | `corpus/manifest.py:103-112` |
| `CorpusTask.handle` is loaded from `corpus.json` and **referenced nowhere else** in `src/` (not identity, not manifest, not retrieval, not episodes) | `corpus/loader.py`; repository grep |
| Frozen meaning of the handle: "a *verification handle* owned by the verifier"; the loader never inspects it | `M4_SPEC.md:34`, `:80` |
| Frozen adapter seam turns "a `CorpusTask`'s opaque handle into the concrete inputs the frozen proposer and verifier consume" | `M5_SPEC.md:56-57` |
| On `Task`, the verification handle is `repo_path` + `hidden_test_command`; `repo_path` "is the source the verifier copies" and is never operated on in place | `batch/adapter.py:8`; `task.py:50` |
| `Task`, `PreRegistration`, `EvaluationRecord` are `frozen=True, extra="forbid"` | `task.py:54`; `analysis/preregistration.py:78`; `evaluation/record.py:35` |
| `EvaluationProvenance` and `PreRegistration` contain no verification-contract component | `evaluation/provenance.py`; `preregistration.py:81-103` |

**Invariant to preserve (RD instruction):** A1/A2 retrieval semantics must stay exactly as they are. Operationally, **no option may alter `CorpusTask.material` or `Task.prompt`**, the only two retrieval inputs. Any option that satisfies this leaves retrieval byte-identical.

**Content requirement shared by every option:** the TaskSpec used at evaluation contains the verification contract only: image digest, platform, base commit, test patch, required test IDs, protected-surface rule inputs, trusted runner and config digests, limits. It **excludes the gold patch**, which belongs only to admission evidence. The proposer must never be able to reach a TaskSpec. It cannot today, because the proposer reads only `prompt` and `task_id`.

### 3.2 Options

- **Option A — Verification sidecar keyed by `task_identity`.** A separate file mapping `task_identity → TaskSpec digest`, loaded by the real-task adapter or the verifier alongside the corpus.
- **Option B — Content-addressed TaskSpec registry keyed by task identity.** The registry stores TaskSpecs by digest and exposes a lookup `task_identity → TaskSpec`.
- **Option C — Extend `Task`** with a verification-only field (e.g. `verification_spec_digest: str | None = None`), following the M2 precedent of adding the optional `secondary_test_command`.
- **Option D — Handle-carried digest (recommended candidate).** `CorpusTask.handle` holds the TaskSpec digest, a string written in `corpus.json`. A real-task adapter, registered behind the frozen `TaskAdapter` seam:
  1. resolves the digest in a content-addressed registry;
  2. recomputes the digest and fails closed on mismatch;
  3. materializes `Task(task_id=<stable, spec-independent id>, prompt=<pure function of material>, repo_path=<registry path of the verified TaskSpec bundle>, hidden_test_command=<the spec's declared test argv>)`.

  The container verifier re-verifies the bundle digest at use and treats a mismatch between `hidden_test_command` and the spec as a fail-closed error. No schema changes.
- *(Excluded by RD instruction: binding the digest into `CorpusTask.material`. It would change the retrieval query and task identity.)*

### 3.3 Comparison

| Dimension | A — Sidecar | B — Registry lookup by identity | C — Extend `Task` | D — Handle-carried digest |
|---|---|---|---|---|
| Frozen contract changes | None (new artifact) | None (new artifact) | **Yes:** `Task` (M1/M2 contract), `extra="forbid"` | None. Uses the handle and `repo_path`/`hidden_test_command` in their documented roles (M4:34, M5:56-57, `adapter.py:8`). `repo_path` points to a verified TaskSpec bundle rather than a git working copy, so an interpretation note is recommended. |
| Retrieval input change | None | None | None | None |
| A1/A2 embedding change | None | None | None | None |
| Corpus manifest change | None | None | None | None (handle not hashed) |
| M8 evaluation identity change | None, so the verification contract is **not** in evaluation identity (F-12 persists) | Same | Same | Same |
| Provenance | Two sources of truth (corpus and sidecar) can drift silently; needs its own digest and binding | Needs a rule for *which* spec version an identity maps to, which reintroduces a pin (i.e. A) | Digest travels explicitly with every `Task` | **Single source of truth.** The corpus file already carries the handle; the digest is re-verified at the adapter and at the verifier |
| Determinism | Deterministic if the sidecar is content-addressed and pinned | Deterministic only with a version pin | Deterministic | Deterministic (content-addressed; double verification) |
| Formal amendment required | No | No | **Yes** (frozen `Task`) | No. Interpretation ruling recommended. |
| Implementation complexity | Moderate (second artifact plus consistency checks) | Moderate-high (registry plus version-pin semantics) | Moderate, **plus** re-verification of every frozen `Task` consumer (M5 runner, M8 attempt's `model_copy`, fixture adapter, spike) | Low-moderate (adapter plus registry plus verifier-side check; frozen code untouched) |
| Risk to the frozen scientific comparison | Low for arms (same spec for all arms); medium for integrity (sidecar drift) | Low for arms; medium (version ambiguity) | Low for arms; **regression risk** to frozen M5/M8 code paths through a shared frozen type | Low for arms; low for integrity. Misrouting risk (a real-task `Task` given to the legacy verifier would be judged, not rejected) needs a composition-level guard. **This risk is shared by all options.** |

### 3.4 Recommendation for Research Director review

**Option D**, subject to RD ratification. The reasons, in order of weight:

1. **It uses the slot the frozen architecture designed for this purpose.** M4 defines the verification handle as "owned by the verifier" and opaque to the loader. M5 defines the adapter as the place where the handle becomes verifier inputs. Nothing is reinterpreted except `repo_path` pointing to a bundle, which the field's own documentation ("the source the verifier copies") accommodates.
2. **It leaves both retrieval inputs untouched by construction.** A1/A2 semantics are exactly preserved.
3. **It keeps one source of truth.** The corpus file names the verification contract, and it is re-verified at two independent points.
4. **It needs no amendment of a frozen type**, unlike C, and avoids A's drift and B's version ambiguity.

It was **not** chosen for ease of coding. A sidecar (A) is comparably easy; it loses on provenance integrity.

**Conditions attached to the recommendation:**
- **D-1** `Task.task_id` is spec-independent and stable (e.g. the corpus task identity), so re-pinning a TaskSpec does not alter episode identity through `task_id`. The verification contract enters episode identity instead through the deterministic evidence digest carried in `Verdict.output`, which is hashed as `verdict_output`.
- **D-2** `Task.prompt` is a pure function of `material`. The adapter must never place TaskSpec content (tests, test names, gold patch) into the prompt.
- **D-3** A composition-level guard ensures the real-task adapter can only be wired with the container verifier. The legacy verifier must refuse a real-task `Task` (by construction or by a static wiring test). A misrouted real task must never produce a verdict.
- **D-4** The interpretation note on `repo_path` is recorded, either with D28 or in the M2-PV specification.

### 3.5 What D28 does **not** solve: verification-contract binding to evaluation identity

Under **every** option, changing a task's TaskSpec (e.g. a re-pinned image) changes **neither** the manifest hash **nor** `EvaluationProvenance.identity` **nor** `PreRegistration.identity`. None of those has a verification component, and adding one is a frozen-schema amendment (M8/M9).

Frozen-compatible mitigation (proposed, not decided):
- At pre-registration time, compute a **verification manifest digest**: SHA-256 over the sorted `task_identity → TaskSpec digest` pairs of the pre-registered corpus.
- Record it in the evidence ledger and in the pre-registration's freeze record.
- The container verifier refuses any TaskSpec not in the registered verification manifest.

This is **procedurally bound** (ledger plus verifier check), **not identity-bound**. Binding it into `PreRegistration` / `EvaluationProvenance` would require a formal amendment. → RD question F-6.

### 3.6 Verifier-implementation identity (OQ-13, unchanged)

D27 records orchestrator identity in evidence. Whether a change of verifier *implementation* must also change evaluation identity is still open. The verification manifest (§3.5) does not cover it.

## 4. Cross-decision consistency

| Frozen element | D26 | D27 | D28 (Option D) | Finding |
|---|---|---|---|---|
| M0 §6 | Conflicts literally | Resolves by scoped clarification | — | Needs D27 ratification |
| **D13** ("verifier … runs inside a Linux container") | Classification runs outside a container | D27 scopes the clarification to D13 as well | — | **CX-R1: a real conflict not listed in the earlier reports.** The M2-PV research report and the reconciliation review named only D19 and M0 §6. D13's verifier sentence is a **third** frozen statement AR-2 conflicts with. Surfaced here, not silently resolved: D27 proposes to cover it, and the RD must ratify that scope (F-2). |
| D8 (held-out lock, pre-registration before the first real run, fixed base model) | Unaffected; the lock is upstream of verification | Unaffected | Handle not in identity or manifest, so the lock is unchanged | **CX-R2 (gap, not contradiction):** D8.2 requires pre-registration before the first real run, but the pre-registration does not pin the verification contract (§3.5) |
| D18 (Determinism L1–L4) | Digest pinning strengthens L4 | Adds the classifier environment to "same execution environment" | Content-addressed spec is deterministic | Consistent. D18's "asserted same-machine in CI" becomes capability-dependent (§1 consequences). |
| D19 | Superseded for real tasks only | — | — | Consistent by scoping. `M2_SPEC.md:232` ("Single-container — no orchestrator/compose split") falls under the same scoping and must be named in D26 (it is). |
| D21 (`flaky` provenance; `secondary_passed` identity) | — | — | No secondary suite for real tasks (`None`) | Consistent in contract. The loss of the model-gap signal is an accepted-residual question (F-7), not a contradiction. |
| M7 shared-retrieval invariant (D7) | Verifier identical across arms | — | No retrieval input changes | Consistent |
| M8 evaluation identity | — | — | Not bound (§3.5) | Gap, as CX-R2 |
| M9 statistical model (PASSED = 1, else 0; incomplete run → VOID) | Raise-only infra (VOID on exhausted retries) | — | — | Consistent. Operational VOID risk and the flaky-nominal question (OQ-6) remain open. |
| M10 executor | Unaffected | — | — | Consistent |
| D3 (bit-for-bit reproducibility given inputs, seed, environment) | Environment = task image digest | Adds classifier identity | Spec content-addressed | Consistent and strengthened |
| D14 non-goals (no premature scale infrastructure) | Single machine, local runtime | — | Registry is a local content-addressed store | Consistent |

**Contradictions found:** CX-R1 (D13), in addition to the known D19 and M0 §6 conflicts. **No contradiction** with M7, M9 or M10.

---

## 5. Output

### A. Proposed D19 amendment text
§1 (D26), verbatim as the proposed entry.

### B. Proposed M0 §6 clarification text
§2 (D27), verbatim as the proposed entry, including its scoping to D13's verifier sentence.

### C. TaskSpec transport comparison table
§3.3.

### D. Recommended transport architecture
**Option D (handle-carried TaskSpec digest, adapter-resolved, verifier re-verified)** with conditions D-1 to D-4 (§3.4). The verification-manifest procedure (§3.5) closes the evaluation-identity gap procedurally.

### E. Remaining contradictions and gaps
1. **CX-R1:** D13's verifier sentence conflicts with AR-2 (newly identified; proposed resolution inside D27).
2. **CX-R2:** the verification contract is not bound into pre-registration or evaluation identity (procedural mitigation only, §3.5).
3. OQ-13: verifier-implementation identity vs evaluation identity.
4. Carried forward, not addressed by these decisions: claims B and C (result-channel forgery, semantic manipulation); raise-only infra and its VOID risk; flaky-nominal effect on M9; R-value calibration.

### F. Exact questions requiring Research Director ratification
1. **F-1** Ratify D26 as written, superseding D19 **only** for real repository-task verification, with AR-2 placement and the stated trust assumption (the orchestrator's runtime access is root-equivalent)? *(yes / no / amend)*
2. **F-2** Ratify D27, including its scope over **both** M0 §6 and D13's verifier sentence (CX-R1)? *(yes / no / amend)*
3. **F-3** Accept D27's requirement that evaluations of record refuse to run from a dirty tree or an unlocked environment? *(yes / no)*
4. **F-4** Select Option D for TaskSpec transport, with conditions D-1 to D-4? *(D / A / B / C)*
5. **F-5** Accept the `repo_path` interpretation note ("path of the verified TaskSpec bundle, the source the verifier copies") as an interpretation, not an amendment? *(yes / no — if no, Option C's formal `Task` amendment becomes the path)*
6. **F-6** For the evaluation-identity gap: procedural verification manifest (no amendment), or a formal M8/M9 amendment adding a verification component? *(procedural / amendment)*
7. **F-7** Record the absence of a real-task secondary suite (loss of the D21 model-gap signal) as an accepted residual? *(yes / no)*

### G. What must go to Gemini for delta review
1. D26 text: scope (real tasks only), completeness of the constraint list, the fail-closed clause, and the stated trust assumption.
2. D27 text: the A/B/C separation, and the claim that the host is **not** the source of truth.
3. **CX-R1 (D13)**: confirm it is a real conflict and that D27's scope resolves it.
4. D28: the comparison table, the recommendation of Option D, conditions D-1 to D-4, and whether the `repo_path` interpretation is legitimate or disguises an amendment.
5. §3.5: whether a procedural verification manifest is scientifically sufficient before the first pre-registered real run (D8.2), or whether identity binding is required.
6. Re-confirmation of the reconciliation review's A/B/C analysis. Gemini has not yet responded to E12/E13.

### H. What must NOT happen yet
- No edit to `DECISIONS.md`, `M0_SPEC.md`, `PROJECT_STATE.md` or any M0–M10 artifact.
- No enactment, ratification claim or freeze of D26–D28 or of M2-PV.
- No production verifier code, adapter code, registry code or TaskSpec schema in the repository.
- No commit or push.
- No adversarial-matrix implementation until the RD authorizes the experiment-only probe v2.
- No binding of any verification data into `CorpusTask.material` or `Task.prompt`.
- No real-task `Task` routed to the legacy `VerifierSandbox`.

*End of M2-PV-R Architecture Ratification Draft — DRAFT, not ratified.*
