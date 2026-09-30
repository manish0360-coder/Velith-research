# SRC Review Request — S-R1 (primary completeness / VOID isolation) and S-R2 (realized n < planned n_conf)

**From:** Chief Systems Engineer, on behalf of the Research Director.
**To:** Scientific Review Council (Gemini).
**Date:** 2026-09-28.
**Type:** research-only. The request asks for an **exact mathematical/statistical ruling**, not a general opinion.
**Baseline:**
- Velith `5452efc` (D31 placed in `docs/DECISIONS.md`, SHA-256 `57e228d6…`);
- RD Freeze Decision Input `e69f4f48…`;
- SRC final review `c1ced0a2…`.

**Constraints on this review.** Do **not**:
- choose δ, Δ_true, pilot size, pilot scope, N_avail or the governing sensitivity scenario;
- authorize the pilot;
- freeze the successor specification;
- assume any implementation exists.

If a ruling would require superseding D31, D6, D7, D8 or D15, or M8 identity v2, **say so explicitly**. Do not rely on it implicitly.

---

## Part 0 — Frozen facts you must rule against

**F-1 — D31 (ratified, `DECISIONS.md`).**
- **Decision 6.** The primary estimand is Δ20 = P(A2 pass at final checkpoint K) − P(A0 pass), a paired contrast over held-out tasks. The hypotheses are H0: Δ20 ≤ δ vs H1: Δ20 > δ, with δ > 0. The test is an exact unconditional paired-proportion test at one-sided α = 0.01, applied at checkpoint K for every K. GEE is used only for a secondary, non-gating longitudinal trend. GO iff H0 is rejected; NO-GO otherwise. A Stage-1 GO is necessary-but-not-sufficient (D8.5).
- **Decision 9.** δ, the usable held-out n, K, N, α and target power (≥ 0.80) are specified jointly and frozen before any confirmatory evaluation of record. If power is below 0.80 at the maximum usable n, the confirmatory Stage-1 design is VOID before execution — never NO-GO. The frozen VOID dispositions are retained: global-incomplete; n = 0; empty VerificationManifest.
- **Decision 11.** If A1 is collected concurrently, the Stage-1 analysis reads no A1 outcome.
- **Decision 7.** T = 0.0 and N = 1. The held-out task is the unit, and uncertainty is task-level.

**F-2 — D8.6 (ratified; literal text unchanged by D31).**
> "Effect size reported, not just significance — with few seeds, magnitude and seed-spread are the primary evidence; an underpowered or noisy positive is treated as uninterpretable, not as a weak win."

**F-3 — Frozen M9 §3.5.1 (VM2; historical, not the successor).**
- **Complete-case:** if a task is missing an evaluation record at any pre-registered checkpoint for any of A0, A1 or A2, the whole task is excluded.
- **Global incomplete:** "If the M8 evaluation run did not complete for the full pre-registered held-out set, this pre-registration is void."
- **OED-7:** n = 0 after complete-case gives VOID.
- **Encoding:** PASSED = 1, and **every other verdict**, including INFRA_ERROR, is 0. A verdict of INFRA_ERROR is therefore an observed failure, **not** a missing cell. A cell is missing only when no evaluation record exists.

**F-4 — SRC final review (accepted).** The design chain is: pilot → p0 two-sided 95% CP interval → δ → Δ_true → planning discordance → exact-power minimization → n_conf → compare with N_avail → VOID if n_conf > N_avail. The test's Type-I control is exact and holds at every n: certified supremum plus Berger–Boos γ.

**F-5 — Frozen M9/M10 code paths by which secondary machinery or non-primary cells can currently block, void or decide.** These come from the CSE audit, verified at `5452efc`:

| # | Location | Frozen behaviour | Effect if reused unchanged by the successor |
|---|---|---|---|
| P1 | `analysis/decision.py:138, :153–175` | GEE model failure gives `MODEL_FAILURE_P_VALUE = 1.0` for that model's p-values in the K>1 Holm family | A GEE failure forces **NO-GO** |
| P2 | `analysis/executor.py:218–219` | When K > 1, the pre-flight requires `statsmodels == 0.15.0`; otherwise `ExecutionError` | A secondary-library problem aborts the run and **writes no result record** (no decision at all) |
| P3 | `analysis/completeness.py:75–84, :134–147` | Required cells = A0 plus A1 **and** A2 at **every** checkpoint. `evaluation_run_complete = False` gives `VOID_GLOBAL_INCOMPLETE`. Complete-case runs over all required cells. | Missing A1 or intermediate-A2 cells exclude tasks from, or **VOID**, the primary analysis |
| P4 | `analysis/executor.py:279–295`; `decision.py` K>1 family | The K>1 gating family includes the trend and interaction tests | Secondary inference gates the decision |
| P5 | `analysis/gee.py:276–343` | GEE design validation raises `GeeError` | A secondary structural failure is a **structural abort** |
| P6 | `analysis/executor.py:223–237` | Any sink record whose evaluation identity lies outside the expected set raises `ExecutionError` | If the successor's primary expected set excludes A1 or intermediate A2 records, their mere **presence** aborts the run |
| P7 | `analysis/binder.py:143–160` | Unexpected or duplicate cells raise `BinderError` | Same as P6, at the binder |

Note on P3: the frozen global flag `evaluation_run_complete` is a single boolean covering all arms and checkpoints.

---

## Part 1 — S-R1: primary completeness and VOID isolation

Give an exact ruling on each of the following:

1. **Primary data set.** Must the Stage-1 primary decision use **only** the paired cells {A0 at episode 0, A2 at final checkpoint K} per held-out task?
2. **Isolation.** State, item by item, whether each of these must be **prevented** from blocking, invalidating, excluding tasks from, or VOIDing the primary A0-vs-A2@K exact test:
   - (a) missing A1 observations;
   - (b) *present* A1 observations (P6/P7);
   - (c) missing intermediate A2 checkpoints (k < K);
   - (d) GEE or secondary statistical failure (non-convergence, separation, singular covariance);
   - (e) secondary non-estimability (for example K = 1, or all-identical outcomes);
   - (f) `statsmodels`/GEE runtime or environment failure (P2);
   - (g) secondary p-value failure (non-finite, undefined).
3. **Exact rules required:**
   1. **Primary completeness.** Define which cells must exist for a task to enter the primary analysis, and how that relates to D31's "usable held-out n".
   2. **Primary VOID.** The complete, closed list of conditions that VOID the primary decision, including how the frozen global-incomplete condition (F-3, P3) must be re-scoped: to the primary cells only, or otherwise.
   3. **Secondary failure.** Its recorded disposition.
   4. **Secondary non-estimability.** Its recorded disposition.
   5. **Influence.** Whether secondary machinery can **ever** affect the primary GO/NO-GO, and if so, exactly how. Our expectation is "never", but rule on it.
4. **Reconciliation with P1–P7.** For each path, state whether the successor must **supersede** it (by versioned successor, per D31 decisions 3–4; frozen VM2 code stays historical), **reuse** it unchanged, or **re-scope** it, and give the exact successor behaviour.
5. **Ordering.** Must the primary decision be computed and fixed before any secondary computation? Must the result record be written even when every secondary computation fails?

## Part 2 — S-R2: realized n < planned n_conf

**Definitions.** Use exactly these five quantities, and correct them if needed:
- **n_conf:** the planned confirmatory sample size, frozen in the successor pre-registration before execution;
- **N_avail:** the usable held-out population available at design time, net of pilot exclusions;
- **n_admitted:** held-out tasks whose TaskSpec passes admission (gold-patch validation) **before** any confirmatory generation;
- **n_cc:** admitted tasks with both primary cells (A0 and A2@K) observed after execution (complete-case);
- **n_analyzed:** tasks entering the exact test.

Give an exact ruling on each of the following:

1. **Disposition when n_admitted < n_conf.** This is known before execution and is outcome-blind. Is it VOID before execution, or another explicitly defined disposition?
2. **Disposition when n_cc < n_conf after execution.** Choose among, or correct:
   - VOID before analysis;
   - analyzable with reduced power, with achieved power reported;
   - an asymmetric rule (a GO stands, and a NO-GO becomes VOID or uninterpretable);
   - another explicitly defined disposition.

   You must reconcile your ruling with **F-2 (D8.6), which treats an *underpowered positive* as uninterpretable**, and with **D31 decision 9, which forbids an underpowered design from producing NO-GO**. State whether any candidate rule contradicts either text. Type-I control of the exact test holds at every n (F-4), so explain precisely what power loss does and does not invalidate.
3. **Recomputation.** Must the power at n_cc be recomputed, and if so, under which fixed planning inputs (the pre-registered planning p0, Δ_true, discordance scenario and δ)? Is any recomputation using observed outcomes forbidden?
4. **Buffer.** Must the design pre-register an over-enrolment rule (for example n_target ≥ n_conf with a pre-declared expected-loss allowance) so that n_cc ≥ n_conf is expected? Rule on whether this is required or merely permitted. Do **not** choose the loss value.
5. **Post-hoc reduction of n_conf** (for example recomputing it after execution from observed discordance or base rate). Is any such reduction permissible? If not, state that explicitly.
6. **Informative missingness.** Primary-cell losses after execution (records absent) may depend on outcomes. State whether the rule must treat post-execution primary-cell loss differently from pre-execution admission loss.
7. **Minimum n.** Do **not** choose an arbitrary minimum n. If your rule implies a threshold, it must be derived only from the pre-registered design quantities.

---

## Required response format (for each of S-R1 and S-R2)

1. **SRC RULING:** ACCEPT / ACCEPT WITH CORRECTION / REJECT, of the CSE expectation stated above or of your own corrected rule.
2. **EXACT RULE:** normative wording suitable for the successor specification ("SHALL …"), with all quantities defined.
3. **RATIONALE:** a mathematical or statistical justification.
4. **WHAT BECOMES FROZEN.**
5. **WHAT REMAINS OPEN**, marking each item as RD or SRC.
6. **IMPACT ON THE M9/M10 SUCCESSOR.**
7. **WHETHER ANY CURRENT FROZEN CODE PATH MUST BE SUPERSEDED:** give it per path, P1–P7, and name the decision authority each supersession relies on (D31 decisions 3–4, or a new decision).

End with an **OVERALL RESULT:** READY FOR RD FREEZE / REQUIRES FURTHER SRC REVIEW / REQUIRES RD DECISION.
