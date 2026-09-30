# M2-PV — Reconciliation Review (CSE report vs. SRC/Gemini review)

**Status:** Reconciliation review only. Not a decision, not an amendment, not an implementation authorization.
**Inputs:** `M2-PV_PRODUCTION_VERIFIER_SPEC_RESEARCH.md` (DRAFT, 2026-09-25); Gemini SRC review ("CONDITIONALLY APPROVED"); repository at `b14d918` (read-only); new sandbox experiments E12–E13 (Appendix A).
**Author:** Chief Systems Engineer. Conflict of interest as before: I wrote the report under review and the experiments cited here. Findings that go **against** my own report are marked ⚑.

Classification key (exactly one per item): **A** accept · **B** accept with rewording · **C** requires empirical validation · **D** requires formal architecture amendment · **E** reject.

---

## The critical scientific question (answered first)

Three claims, carefully separated:

| Claim | Established by process isolation? | What establishes it | Evidence |
|---|---|---|---|
| **A.** The candidate cannot modify the trusted collector's memory. | **Yes, conditionally.** The collector must never import repository code, **and** must sit outside the candidate's reach for signals, ptrace and `/proc/<pid>/mem` (different UID or container). With the same UID in the same container, memory stays intact, but the candidate can **kill** the collector [E12d]. | AR-2 already places the trusted collector (the host orchestrator) **outside the container**. That boundary establishes A, whatever the process layout inside the container. | E12b (collector never imported candidate code); E12d (same-UID kill). |
| **B.** The candidate cannot forge the test-result channel. | **No.** Each test's outcome is computed in the process that runs the test, and that process imports candidate code. Forgery **relocates** to the worker: under a process-isolated collector, the E4 forgery still yields `passed`/exit 0 for a failing test [E12b]. | Nothing known establishes B for tests that import candidate code. Cross-channel checks detect **inconsistent** forgeries [S:E5, E6]. Canaries detect **canary-unaware blanket** forgeries [E13a]. A **targeted**, channel-consistent forgery evades both [E13b]. | E12b, E13a, E13b. |
| **C.** The candidate cannot manipulate a test's semantic execution while producing a truthful-looking result. | **No.** Here the result is *truthful*: the test really passes, because candidate code special-cases the test (it inspects the caller's frame and returns the expected value) without touching pytest at all [E12c]. No execution boundary is involved. | Only test adequacy measures bear on this: hidden or held-out tests (D21 model-gap), test-awareness screening, mutation or property tests. **Open research (class E).** | E12c. |

**Conclusion.** Process isolation establishes **A** (given a boundary the candidate cannot cross). It does **not** establish **B** or **C**. Gemini's statement that process isolation "renders in-process report forgery impossible" is **refuted** by E12b. Its statement that the combination of process isolation, randomized canaries and cross-channel checks makes "both blanket and targeted forgery structurally impossible" is **refuted** by E13b.

My original report's claim ("no execution-boundary design can prevent this", §5.4) was **imprecise** ⚑. It conflated A with B. The corrected statement: the boundary protects the **collector** (A), not the **result's origin** (B), and not the **test's meaning** (C).

---

## SECTION 1 — Executive reconciliation

- **Agreement (substantial).**
  - The CX-1 and CX-2 contradictions are real and need formal dispositions.
  - AR-2 is the preferred placement direction.
  - The time-of-trust rule and the channel partition stand.
  - Infra outcomes are raised, never returned (M9 bias).
  - Attribution to infra requires trusted-channel evidence.
  - Confirmation re-runs plus `flaky` quarantine.
  - Admission gate, zero-P2P exclusion, T-2, trusted launcher, explicit config.
  - Evidence ledger without M8 amendment; legacy verifier confined to fixtures; RS-1 baseline cadence.
- **Disagreement (material).** Gemini overstates four things:
  1. Process isolation → "forgery impossible" (refuted: E12b).
  2. Canaries → "100%" (true only for canary-unaware blanket forgery; E13b evades).
  3. A2 "100% protected" (false: deterministic candidate-only infra faults (OQ-4), and the residual B/C forgeries flow into A2 as `PASSED`).
  4. R_b = R_g = 3 "necessary and sufficient" (3 clean runs bound a per-test flake rate only to ≤ 63% at 95% confidence; §4).
- **Errors in my own report surfaced by this reconciliation ⚑.**
  - (i) §5.4 conflated claims A and B.
  - (ii) FD-10 option (a), binding the TaskSpec digest into `CorpusTask.material`, has an unaccounted side effect. `material` is the text embedded as the **retrieval query** (`evaluation/attempt.py:125` → `retrieval/query.py:40-41` → `retriever.py:47`). Binding would perturb A1/A2 retrieval. Gemini accepted it without noticing.
  - (iii) PV-RES-001 required "exit code 0" together with must-fail canaries, which force a non-zero exit [E13]. That rule must be reformulated.
- **Factual slips in the Gemini review.**
  - `Task` is a pydantic `BaseModel`, not a "dataclass" (`task.py:45`).
  - FD-10 as ruled (a new optional `Task` field) **is** an amendment of a frozen contract, contrary to the review's framing that no frozen schema changes.
  - CX-2 says "does not violate" yet recommends amending M0 §6; the two statements are in tension.

### Classification of the 22 items

| # | Item | Gemini position | Class | Reason (short) |
|---|---|---|---|---|
| 1 | CX-1 / D19 | Contradiction real; amend | **D** | Agreed; needs a superseding DECISIONS entry (§5). |
| 2 | CX-2 / M0 §6 | "No violation"; amend anyway | **D** | The literal text (`M0_SPEC.md:120`: host Python "never as the source of truth for a verdict") conflicts with a host-side classifier. Gemini's intent-based reading is plausible but must be **ratified**, not assumed (§6). |
| 3 | AR-2 host orchestrator | Selected | **D** | Correct direction; it *is* the content of the D19 supersession and depends on items 1–2. |
| 4 | Process-isolated runner | Freeze condition; "forgery impossible" | **B** | Establishes A only; B not established [E12b]. Under AR-2 the trusted collector is already outside the container; in-container isolation adds crash containment only, at a fidelity cost (§7). Not a security freeze condition. |
| 5 | Semantic integrity (claim C) | Implied solved | **E** | Unsupported; E12c shows a truthful pass from a non-fix with no harness tampering. |
| 6 | Canary tests | "100%" | **B** | Detects canary-unaware blanket forgery [E13a], and only if the canary runs in a process that imported candidate code. Targeted forgery evades it [E13b]. |
| 7 | Cross-channel consistency | Part of "structurally impossible" | **B** | Detects inconsistent forgeries [S:E5, E6]; consistent forgery evades it [E13b, S:E4]. |
| 8 | Anti-VOID attribution | "Candidate CANNOT trigger VOID" | **B** | Direction correct. "Cannot" holds only if the candidate cannot induce **trusted-channel** faults through shared resources (disk, log volume, VM memory) (§8). |
| 9 | R_c = 2 | Fixed | **C** | Misattribution probability depends on independence of infra faults over time, which is unmeasured. |
| 10 | R_b = 3 | "Necessary and sufficient" | **C** | Statistically unsupported (§4); must be derived from a target flake bound or recorded as a cost choice. |
| 11 | R_g = 3 | Same | **C** | Same. |
| 12 | Timeout semantics | Reproduced → FAILED; `T = max(60s, 3×T_gold)` | **C** | Semantics consistent with the report. Formula unvalidated; it ignores baseline duration (the report used max over baseline and gold). |
| 13 | OOM semantics | Reproduced → FAILED | **C** | Container-limit vs host/VM OOM discrimination on WSL2 unverified. |
| 14 | T-2 restoration | "Completely resolves L5" | **B** | Rule accepted; OQ-2 (test-root definition, tests outside roots) remains open. |
| 15 | Trusted launcher | Approved | **A** | Sandbox evidence E1d/E1e; in-image confirmation stays a matrix row. |
| 16 | Explicit pytest config (`-c`, `--rootdir`) | Approved | **A** | Sandbox evidence E8b. (Gemini also mandates `--import-mode=importlib` globally; that part is **C**, see §4.) |
| 17 | TaskSpec digest | Approved | **A** | Content-addressed spec accepted. Its **transport** (FD-10) is a separate decision (§5, §10). |
| 18 | Verifier evidence ledger | Approved | **A** | Frozen-compatible (no M8 change); preserves D8 segregation. |
| 19 | M8/M9 compatibility | "Fully reproducible"; no M8 change | **B** | Raise-only infra accepted. Material binding perturbs retrieval ⚑; OQ-6 (flaky nominal state in M9) unresolved. |
| 20 | Real-task secondary suite | `None` | **B** | Accept, but record that D21's model-gap signal is **absent** for real tasks, so B/C residual forgeries enter A2 as uncontradicted `PASSED`. |
| 21 | Container hardening | Non-root / read-only "where supported"; fixed 4g / 256 PIDs | **C** | Non-root and read-only compatibility with SWE-bench images unverified (the flask image runs as root, per the U2 inventory). Fixed limits conflict with per-task derived limits (PV-RSRC-002). |
| 22 | PV-SCI-004 residual | "Scientifically false; preventable" | **E** | Rejected. The residual stands, sharpened to claims B and C. |

---

## SECTION 2 — Accepted Gemini decisions (class A)

1. **Trusted launcher outside the repository** (item 15). Also accepted: the `python -I` prohibition (E2) and the time-of-trust rule.
2. **Explicit trusted pytest configuration** (`-c` + `--rootdir`) (item 16).
3. **TaskSpec as a content-addressed, immutable verification contract** (item 17).
4. **Verifier-side evidence ledger** keyed by `(evaluation_identity, task_identity, arm, seed)` → deterministic evidence digest, with no M8 schema change (item 18).
5. Also accepted (FD register, compatible with the frozen contracts):
   - **FD-2:** infra is raised, never returned.
   - **FD-3:** exhausted infra retries → raise → VOID under the frozen M8. Accepted as the only frozen-compatible behavior, with its operational risk recorded.
   - **FD-13:** the legacy `VerifierSandbox` is confined to synthetic fixtures.
   - **FD-14:** RS-1, a fresh baseline per candidate (demonstrated in M2 Case A).
   - The channel partition (runtime, pre-execution, baseline, candidate-influenced).
   - Zero-P2P exclusion.

Accepted items still inherit their matrix rows. Acceptance of a direction is **not** a freeze.

## SECTION 3 — Gemini claims requiring rewording (class B)

| Gemini wording | Required wording |
|---|---|
| "Process-isolated test execution renders in-process report forgery impossible." | "A collector that never imports repository code and runs outside the candidate's process-control reach cannot have its **memory** altered by the candidate (claim A). Test outcomes remain candidate-influenced, because they are computed in processes that import candidate code (claims B, C remain open) [E12b]." |
| "Canaries detect blanket forgery with 100% certainty." | "A must-fail canary executed **in a process that has imported candidate code** detects forgeries that do not discriminate the canary from task tests [E13a]. Forgeries that discriminate by file, name or any other attribute evade it [E13b]. No detection rate against adaptive candidates is claimed." |
| "Process isolation + randomized canaries + cross-channel consistency render both blanket and targeted forgery structurally impossible." | **Rejected** (E13b is a counterexample; randomized names are irrelevant to path-based discrimination). Replacement: "These mechanisms raise the cost of harness-level forgery and detect its inconsistent and canary-unaware forms." |
| "A2 memory is 100% protected against infrastructure noise and setup crashes." | "Non-reproduced anomalies are quarantined from A2 via `flaky` (`filters.py:105`). Protection is conditional on R_c adequacy and on the absence of deterministic candidate-only infra faults (OQ-4). A2 is **not** protected against B/C residual forgeries, which arrive as uncontradicted `PASSED` when no secondary suite exists." |
| "Blanket test forgery, config manipulation, and report file rewriting are 100% blocked." | "Config manipulation (T-2 + explicit `-c`) and inconsistent report rewriting (cross-channel) are neutralized or detected for the tested vectors, pending real-image matrix confirmation." |
| "Candidate code CANNOT trigger a VOID outcome." | "Candidate-channel anomalies cannot yield VOID. The candidate must additionally be prevented from inducing **trusted-channel** faults through shared resources (§8); that is a validation obligation, not a property." |
| "T-2 rule completely resolves L5"; "Resolves L11 completely"; "matrix mathematically complete". | "T-2 replaces the hand-picked list with a rule; the test-root definition remains open (OQ-2)." "Admission validates labels for admitted tasks." "The matrix covers the enumerated vectors; completeness against unknown vectors is not claimed." |
| "Standard Docker with drop-caps and no-new-privileges provides a sufficient primary boundary." | "…provides the boundary demonstrated in M2 for benign candidates; sufficiency against container-escape attempts is not established (matrix row 14)." |
| CX-2: "Does an external orchestrator violate M0 §6? NO." | "It conflicts with the literal text; whether it conflicts with the intent depends on a ratified clarification (§6)." |
| FD-15: secondary = `None`, "A2 admits uncontradicted PASSED." | Add: "Consequence: the D21 model-gap safeguard does not exist for real tasks." |

## SECTION 4 — Decisions requiring empirical validation (class C)

| Item | What must be measured | Why the fixed value is unsupported |
|---|---|---|
| **R_b, R_g** (Gemini: 3) | Per-test flake rates on a pilot of admitted tasks | If a test flakes independently with probability p per run, the chance that 3 runs all agree is (1−p)³: 0.857 at p = 0.05. Zero disagreements in n runs bounds p only to ≤ 1 − 0.05^(1/n) at 95% confidence: **63% for n = 3**, 26% for n = 10, ~1% for n ≈ 300 (rule of three). So R = 3 catches only very flaky tests. Low-rate flakiness must instead be handled at evaluation by confirmation and `flaky` quarantine. The admission R is a **cost choice with a stated detectable-rate bound**, not "necessary and sufficient". |
| **R_c** (Gemini: 2) | Rate and temporal correlation of transient infra faults on the target host | If transient faults were independent with rate q, a false "reproduced" needs q³. Host contention is plausibly time-correlated, and correlation is unmeasured. |
| **Timeout budget** | Wall-time distributions of baseline and gold across the pilot corpus; host-contention sensitivity | Gemini's formula uses gold only; baseline may be longer. The 60 s floor is unvalidated for large suites. |
| **OOM discrimination** | Whether `OOMKilled` / cgroup `memory.events` distinguish a container-limit kill from a Docker Desktop VM OOM on WSL2 | Unverified. Misdiscrimination converts host faults into candidate `FAILED`, or candidate faults into VOID. |
| **`--import-mode=importlib` as a global mandate** | Baseline and gold agreement under `prepend` vs `importlib`, per task | It can change import semantics (tests relying on test-directory `sys.path` insertion). T-2 deletion already removes the E3 vector, so importlib is defense in depth, to be decided per task at admission. |
| **Container hardening** (non-root, read-only root, limits) | Gold passes under each setting, per image | The flask-5014 image runs as root; the official harness `chmod 777`s the repo "so nonroot user can run tests", which suggests but does not demonstrate compatibility. |
| **In-container per-test process isolation** (if pursued) | Baseline and gold agreement vs single-session execution | Session- and module-scoped fixtures and inter-test state can change outcomes (a fidelity risk, L6). |
| **Anti-VOID shared-resource bounds** | Disk, log-volume and VM-memory exhaustion attempts (§8) | Determines whether "candidate cannot induce trusted-channel faults" holds. |

## SECTION 5 — Required D19 amendment (content for RD ratification; not enacted)

**Nature:** a *superseding, scoped* DECISIONS entry under the amendment procedure (`DECISIONS.md:479`). D19 is **not** edited.

**Proposed scope.** The new entry governs **real-task verification only**. D19 remains authoritative for the legacy fixture verifier (`VerifierSandbox`, `unshare -n`, `CAP_SYS_ADMIN`), which stays confined to synthetic fixtures (FD-13).

**Required content (each point must appear):**

1. **Names D19** and states the evidence: M2 feasibility freeze record (`b14d918`, manifest `30c59a45…`). Real tasks need task-specific environments that cannot co-reside in one image.
2. **Decision:** real-task candidates execute only in task-specific containers pinned by digest (`image@sha256:…`), one fresh container per execution (baseline, candidate, confirmation re-run, admission run).
3. **Placement:** a trusted verifier orchestrator (AR-2) launches task containers through the local container runtime. The orchestrator is **trusted and privileged** (runtime access is root-equivalent on the host). That trust assumption must be stated, not implied.
4. **Candidate constraints:** `--network none`; `--cap-drop ALL`; `no-new-privileges`; bounded PIDs, memory (swap disabled), CPU, wall time and disk; no Docker socket, no `--privileged`, no DinD, no host bind mounts.
5. **Mandatory-isolation invariant carried forward from D19:** if any constraint cannot be applied, the orchestrator raises and never runs candidate code with weaker isolation.
6. **Two-phase intent preserved by construction:** the proposer's network needs are outside task containers; task containers have no network phase.
7. **Alternatives rejected:**
   - AR-1: environment infeasibility.
   - AR-3: host-root socket exposure to a container that historically ran candidate code (F-6).
   - AR-4: privileged mode.
   - AR-5/AR-6: recorded as future options pending feasibility.
8. **Consequences:** `docker-compose.yml` and `verifier.Dockerfile` unchanged by this entry; D13's single-machine discipline preserved; D14 non-goals untouched.
9. **Open items explicitly not decided by the entry:** runner specifics, R-values, hardening beyond point 4.

## SECTION 6 — Required M0 §6 clarification (content for RD ratification; not enacted)

**The conflict precisely.** `M0_SPEC.md:120`: "the host Python is used only for editor tooling and pre-commit, never as the source of truth for a verdict." `PROJECT_STATE.md:127`: "the verdict is produced inside the container; the host is never the source of truth." Under AR-2 the **classification**, which maps evidence to a Verdict, runs in host-side Python. Literally, that conflicts.

**Intent (inferred, needs ratification).** The M0 concern is reproducibility: ambient host state must not influence a verdict. Gemini's reading matches this, but a reading is not a ratification.

**Required clarification content:**

1. The verdict's **evidence** is produced exclusively inside digest-pinned task containers.
2. The verdict's **classification** is computed by the Velith verifier code at a recorded commit, running in a **pinned, identity-recorded environment** (locked interpreter and dependencies, per D13's Python 3.12 target). **This is a new requirement.** Host Python used today for tooling is not automatically such an environment.
3. **No ambient host state** (host packages, environment variables, user configuration) may influence classification. The orchestrator passes explicit inputs only.
4. Orchestrator identity (commit, lock hash) is part of the verification evidence. This interacts with OQ-13 (whether verifier-implementation identity enters evaluation identity).
5. The clarification is scoped to real-task verification; the M0 container-sanity invariant for the Velith image stands.

## SECTION 7 — Process-isolated runner: specification requirements (reconciled)

| ID (proposed) | Requirement | Class |
|---|---|---|
| R-PI-1 | The **trusted collector is the verifier orchestrator outside the task container**. It reads evidence only after the container has fully stopped. This establishes claim A under AR-2. | C (follows from AR-2; E12d shows why an in-container collector is insufficient) |
| R-PI-2 | Every process inside the candidate container is **candidate-influenced**, whatever the process layout. No in-container component is designated "trusted collector". | C (E12b, E12d) |
| R-PI-3 | In-container per-test process isolation is **optional**, justified only by **crash containment and per-test attribution** (one `os._exit` or segfault does not erase other tests' outcomes). It is **not** a forgery control. | B |
| R-PI-4 | If R-PI-3 is adopted, admission must show baseline and gold agreement with single-session execution for each task (fidelity), because shared fixtures and state may change outcomes. | C |
| R-PI-5 | Canaries must run **in the same process(es) as candidate-importing tests**, or they detect nothing (E13a requires co-location). Under per-test isolation, each worker needs its own canary pair. | C |
| R-PI-6 | Result-consistency rule, reformulated: the report, exit status and summary must be **mutually consistent**; must-fail canaries must fail and must-pass canaries pass; every required ID passes. **Exit code 0 is not required** when must-fail canaries are present [E13] (replaces PV-RES-001's exit-0 clause ⚑). | C |
| R-PI-7 | The verifier states the residual: claims B and C are not established (Section 9). | E (stated) |

## SECTION 8 — Anti-VOID specification (reconciled)

**Goal:** a candidate must not be able to convert its own failure into a VOID evaluation (frozen M8 abort, M9 §3.5.1). Infrastructure faults must never become candidate `FAILED`.

| ID (proposed) | Rule | Class |
|---|---|---|
| AV-1 | **Raise** (infra, may VOID) only on trusted-channel evidence obtained **independently of candidate behavior**: image identity failure; container create, start or copy failure **before** candidate code; restore or test-patch failure (pre-execution); runtime or daemon error not preceded by candidate resource exhaustion; baseline unhealthy. | B |
| AV-2 | Every anomaly after the trust boundary (crash, signal, `os._exit`, timeout, OOM within the container limit, missing or inconsistent reports, canary contradiction, collector death) is **candidate-attributed after confirmation**. Reproduced in all R_c fresh re-runs → `FAILED` with reason; otherwise the nominal state with `flaky=True`. | B |
| AV-3 | **Shared-resource bounding**, so the candidate cannot induce trusted-channel faults: per-container disk quota or tmpfs bound; cap on captured stdout/stderr and report size (the orchestrator truncates and records); memory limit plus headroom below Docker Desktop VM memory; PID limit; inode or file-count bound where supported. | C |
| AV-4 | A trusted-channel fault that occurs **after** the candidate exceeded a bounded resource is attributed to the candidate (causal precedence), subject to AV-2 confirmation. | C / D (causal-precedence detection needs validation) |
| AV-5 | Infra retries are bounded (R_i). Exhaustion raises, and the M8 run VOIDs. This is the accepted frozen-compatible consequence (FD-3), and every VOID records the evidence chain. | B (FD-3) |
| AV-6 | Validation rows: disk fill, stdout flood, VM-memory pressure, fork bomb, collector kill, container self-kill. Each must end in candidate `FAILED` (reproduced), never raise. | C |

What anti-VOID **cannot** guarantee: that a deterministic infra fault affecting only candidate runs, and leaving no trusted-channel trace, is not misattributed as `FAILED` (OQ-4, class E).

## SECTION 9 — Remaining scientific residuals

| ID | Residual | Class | Consequence |
|---|---|---|---|
| RS-1 | **Claim B:** candidate-controlled forgery of per-test outcomes that is channel-consistent and canary-aware [E13b, E12b]. | E | A false `PASSED` can enter A2 (no secondary suite) and score 1 in M9. |
| RS-2 | **Claim C:** truthful-looking passes via test-aware special-casing [E12c]. | E | Same, plus it is indistinguishable from a real fix by any execution evidence. |
| RS-3 | Deterministic candidate-only infra faults without a trusted trace (OQ-4). | E | Misattributed `FAILED` enters A2. |
| RS-4 | Flake-rate bound at admission (§4): low-rate flakiness passes admission. | C (quantifiable) | Handled only by evaluation-time confirmation. |
| RS-5 | M9 nominal state for non-reproduced anomalies (OQ-6). | E | Possible arm-correlated noise in the endpoint. |
| RS-6 | ⚑ Retrieval perturbation if the TaskSpec digest is bound into `CorpusTask.material`. | Decision | Non-semantic tokens in A1/A2 query embeddings; retrieval results change whenever the verification contract changes. |
| RS-7 | Absence of D21 model-gap signal for real tasks (FD-15). | Decision (accepted) | RS-1 and RS-2 are not filtered from A2. |
| RS-8 | Container-escape resistance (kernel/runtime vulnerabilities). | Out of scope beyond hardening | Recorded. |

**PV-SCI-004, reworded:** "A `PASSED` verdict certifies that the candidate passed the required tests in an environment whose configuration, test artifacts and runner were verified before candidate code ran, with no detected inconsistency or canary contradiction. It does **not** certify that test outcomes were not forged by candidate code in-process (claim B), nor that the candidate solves the task rather than the tests (claim C)."

## SECTION 10 — Exact conditions required before M2-PV freeze

1. **CX-1:** a D19-superseding DECISIONS entry with the §5 content, ratified by the RD.
2. **CX-2:** an M0 §6 clarification with the §6 content, ratified by the RD, including the new pinned-orchestrator-environment requirement.
3. **FD-10 transport re-decided** in light of RS-6. Either:
   - (a) bind the TaskSpec digest somewhere other than `material` (for example a manifest-level field, or a handle resolved by the adapter), with evaluation identity handled per OQ-13; or
   - (b) explicitly accept the retrieval perturbation.
   Any `Task` field addition is a formal amendment (class D).
4. **Spec draft v2** incorporating:
   - every Section 3 rewording;
   - Section 7 (R-PI-1…7), including the reformulated result rule (no exit-0 clause);
   - Section 8 (AV-1…6);
   - Section 9's reworded PV-SCI-004;
   - the claims A/B/C table;
   - E12–E13 as sandbox evidence.
5. **Explicit RD acceptance of residuals RS-1, RS-2, RS-3, RS-5 and RS-7**, stated with their A2 and M9 consequences. Without this acceptance, a freeze would claim more than the evidence supports.
6. **Validation plan fixed** for every class C item in Section 4, with numeric targets stated in advance (e.g. the flake-rate bound that sets R_b and R_g).
7. **SRC re-review of draft v2** limited to the deltas, confirming or contesting the A/B/C analysis and E12–E13.
8. The **experiment-only matrix run** (§21 of the report + AV-6 + E12/E13 in the real image) completed with an evidence manifest. It must come **before** the freeze: freezing class C items before measurement would repeat the error this reconciliation corrects.

## SECTION 11 — Proposed next milestone (single sequence)

**Next milestone: M2-PV-R — Architecture Ratification and Specification v2.**

1. **RD rules** on the §5 D19 supersession and the §6 M0 clarification, and on the FD-10 transport given RS-6. The CSE drafts the DECISIONS text only when the RD authorizes that drafting.
2. **CSE produces M2-PV draft v2** (outside the repository) incorporating Sections 3, 7, 8 and 9 and conditions 3–6.
3. **SRC re-reviews v2** (deltas only).
4. **RD authorizes an experiment-only probe v2** under `experiments/`: the §21 matrix, AV-6 and E12/E13 in the flask-5014 image, plus a pilot measurement of flake rates, wall times and OOM signals to set R_b, R_g, R_c and budgets.
5. **Freeze M2-PV** with that evidence and the RD's residual acceptance.
6. Then, and only then, the **implementation handoff**.

---

## Appendix A — New sandbox experiments (E12–E13)

Same environment as the report's Appendix A: CPython 3.10.12, pytest 7.3.0, host sandbox, no Docker, same mock repository. **Not container evidence.**

| Exp | Setup | Observed | Establishes |
|---|---|---|---|
| E12a | Collector process that **never imports** repository code; runs each test in a fresh worker (`python <trusted launcher> <nodeid>`), reads the worker's JUnit and exit code | `collector imported candidate? False`; honest results | Harness works. |
| E12b | Same collector; candidate source contains the E4 forgery | Collector still clean; **both tests `passed`, worker exit 0** | Claim A holds; claim B **not** established by process isolation. |
| E12c | No pytest tampering; candidate `make()` inspects the caller's frame and returns `"b"` only when called from `test_must_fail` | Both tests `passed` (truthfully) | Claim C: semantic manipulation with a truthful result. |
| E12d | Worker executes `os.kill(os.getppid(), SIGKILL)` | Collector killed (exit 137) | Same-UID in-container collector: memory integrity is not availability; the collector must be outside the container (R-PI-1). |
| E13a | Single session; trusted canary file with a must-fail and a must-pass test; blanket E4 forgery | Must-fail canary reported `passed`, so a contradiction is detectable | Canaries detect canary-unaware blanket forgery. |
| E13b | Same canaries; forgery rewrites only reports whose `nodeid` contains the task test file | Canaries correct (must-fail failed); required tests forged `passed`; exit 1 consistent with report | Targeted, channel-consistent forgery evades canaries and cross-checks; exit-0 rule incompatible with must-fail canaries. |

Environment note: the sandbox kernel reports Yama `ptrace_scope = 1`. The WSL2 / Docker Desktop kernel value is unverified. It bears on whether a same-UID worker could also *read or write* an in-container collector's memory, one more reason for R-PI-1.

*End of reconciliation review.*
