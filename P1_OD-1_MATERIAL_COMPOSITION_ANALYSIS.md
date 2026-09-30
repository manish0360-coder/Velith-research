# P1 OD-1 — Material composition for the M2-PV-P1 feasibility pilot

**Type:** research / decision preparation. **No option chosen; nothing implemented or executed; Velith untouched.**
**Author:** Chief Systems Engineer.
**Date:** 2026-09-29.

**Basis:**
- P1 design `89f931e0…` (§§2, 4, 11, 12, 14, 17, 21, 22, 24, 27);
- D28 (`DECISIONS.md:560–581`);
- RD-2b = Option V (CLOSED);
- RD-0 amendment R1 (unratified) `98391696…`;
- the BRP prerequisites analysis `27751a5b…`;
- Velith `5452efc`.

**Options:**
- **M-A (bare):** `problem_statement` only.
- **M-C (non-gold retrieval):** `problem_statement` plus source files selected without gold information (for example BM25 over the base tree, top-k within a token budget).
- **Both:** M-A and M-C as two pre-declared paired conditions per task.

M-B (oracle files) is inadmissible because it leaks the fix location. M-D (named files) is outside this comparison.

---

## A. Evidence table

| # | Fact | Source | Class |
|---|---|---|---|
| E1 | P1 asks only: "Can the current proposer produce usable patches on real software-engineering tasks under the proposed sealed-task execution architecture?". It is "not a benchmark, not a solve-rate estimate". | P1 §2 | RATIFIED |
| E2 | "Usable patch" = extracted (`patch_produced`) **and** applies with `git apply` in the sealed container (`patch_applies`) | P1 §4 | PROPOSED |
| E3 | The proposer sends `Task.prompt` verbatim. It has **no repository, filesystem or tool access**. | P1 §11–12; `agent/proposer.py` | EXISTING |
| E4 | Under M-A, the proposer "must invent exact diff context lines without seeing the source". A failure to apply then "confounds 'proposer incapable' with 'prompt lacks code'". | P1 §11 | PROPOSED analysis |
| E5 | M-C "needs an experiment-side retriever and a context budget". The retriever may read only the base tree and `problem_statement`, and never `patch`, `test_patch`, F2P/P2P or `hints_text`. Its code is part of the evidence. | P1 §11, §22 item 2 | PROPOSED |
| E6 | `num_ctx`/`num_predict` are not set by the client (server defaults). Long prompts risk **silent truncation**. | P1 §12 (OD-3) | EXISTING + EXT |
| E7 | The client timeout is 120 s per call, with no retry; generation retries only on GEN_INFRA | P1 §12, §21 | EXISTING / PROPOSED |
| E8 | Measurements are recorded "per (task, condition)"; the budget is "5 tasks × {1 or 2} conditions × 1 attempt" | P1 §17, §21 | PROPOSED |
| E9 | Pre-declared interpretation for two conditions: "Stated as a paired observation per task only … No inference beyond the five tasks". Raw counts only. | P1 §24 (P-3) | RATIFIED principle / PROPOSED rule |
| E10 | Caveat: prompt-prefix caching can lower `prompt_eval_count` | P1 §17 | EXISTING caveat |
| E11 | The template puts the fixed header and `problem_statement` first, then the retrieved files under M-C. **The M-A prompt is therefore a strict prefix of the M-C prompt.** | P1 §11 (OD-2) | PROPOSED; derived |
| E12 | D28 D-2: `Task.prompt` is a pure function of `material`. "TaskSpec test data, hidden tests, gold patches and protected-surface details must never enter `material` or `prompt`." | `DECISIONS.md:572` | FROZEN (applies to real-task `Task`s) |
| E13 | Task identity = SHA-256(material). Material is also the **retrieval query input** for memory arms (`evaluation/attempt.py:125`). | M4 `corpus/manifest.py`; M8 | FROZEN / EXISTING |
| E14 | The exclusion registry is keyed by `instance_id` **and** identity, because different material bytes give a different identity | P1 §10 | PROPOSED |
| E15 | Seed rule `derive_task_seed(pilot_task_identity, 0)` | P1 §12 (OD-12) | PROPOSED |
| E16 | P1 is the predecessor to production-verifier automation (BC-1). Its evidence informs PV-freeze. | M2-PV-R §9; handoff §27 | RATIFIED |
| E17 | The BRP must use the **confirmatory** material → prompt function at verdict level. P1 supplies no p0. | RD-0 R1 clause 4; RD-2b | RD ruling (amendment unratified) |
| E18 | PB-1: the harness and generation script need their own authorization. Their location is OD-4. | P1 §15, §27 | OPEN |

## B. Option-by-option trade-offs

| Criterion | M-A | M-C | Both (paired) |
|---|---|---|---|
| Answers E1 | Only for a contract the proposer cannot use without source (E3, E4). A null result is **uninterpretable** about the proposer. | Tests whether the proposer can patch *given* code, which matches E1's "usable patch". A null result is still confounded by **retrieval misses**. | Separates "proposer" from "context contract" per task (E4, E9). **It is the only option with attribution inside P1.** |
| Architecture evidence (PB-1 and Stage X) | Candidates likely stop at `git apply`, so the sealed test-execution path is rarely exercised | More candidates reach test execution, so more of the sealed architecture is exercised | As M-C, plus M-A's extraction and format evidence |
| Design surface added | None beyond the template | A retriever specification (algorithm, pool, k, token budget), fixed before execution with no tuning on non-excluded tasks | Same as M-C |
| OD coupling | OD-2 only | OD-2 (file delimiters), **OD-3** (long prompts: inadmissibility vs a Modelfile model), **OD-5/D-2** (the retrieval pool must exclude test-patch paths and protected configs), **OD-7/OD-8** (latency against the 120 s timeout, E7), **OD-4** (the retriever enlarges the harness scope) | As M-C, plus **OD-9** (two identities per instance, E14) and **OD-12** (seeds differ per condition, E15) |
| Observability caveats | Minimal | Truncation risk (E6); retriever provenance required (E5) | As M-C. **Caching:** the M-A prompt is a prefix of the M-C prompt (E11, E10), so token counts depend on run order. An order or cache rule must be pre-declared (engineering). |
| Cost | Lowest | Moderate | About 2× generation; execution only for produced patches (E8) |
| Interpretation / governance | Simple | Simple | Pre-declared by E9. **Risk:** reporting "k/5 under M-C vs j/5 under M-A" as a comparison or rate would breach P-3. The only allowed output is paired observations per task. |
| Informs the future confirmatory material function | Tells whether bare material is viable (likely negative) | Tells whether retrieval-augmented material is viable | Both answers, per task |
| Confirmatory side effects (recorded, not decided here) | — | A retrieval-augmented confirmatory material would change task identity (E13), memory-retrieval queries (E13) and D-2 exposure (E12) | Same |
| Contamination of the future confirmatory population | 5 tasks, excluded | Same 5 tasks. Retriever **tuning** on other tasks would expose them, so tuning must be forbidden. | Same as M-C |
| BRP (Option V) | No binding; P1 material is experiment-side | No binding; informs the confirmatory function the BRP must use | No binding; the strongest evidence for that later decision |
| BC-1 / BC-2 | Unaffected | Unaffected | Unaffected |

## C. Contradiction and dependency audit

- **D28 D-2.** P1 builds experiment-side material and **not** D28 real-task `Task`s (P1 §11), so D-2 does not bind P1 directly. There is still an alignment gap: P1 §22's retrieval pool is "the base tree", which can include existing test files and protected configs. If M-C evidence is meant to inform a D-2-conformant confirmatory function, the M-C pool definition should exclude test-patch paths and protected-surface files. That definition is part of the OD-1/OD-5 ruling. **Not a contradiction.**
- **D30.3.** An experiment-side retriever outside `src/` is research code, not a platform mechanism. **Not a contradiction.** If retrieval later enters the confirmatory material function in `src/`, the D30.3 posture must be decided then.
- **P-3 / P1 §24.** Paired conditions are pre-declared and limited to per-task observations. **Consistent**, provided no rate or comparison is reported.
- **P-1 exclusion.** No new tasks under any option. The registry must record **both** material identities per instance if both conditions run. **Consistent.**
- **RD-0 / RD-2b.** No option lets P1 supply p0 or bind the confirmatory function. **Consistent.**
- **BC-1 / BC-2, D26/D27, D31, SM7–SM11, M9/M10.** Untouched by any option.

**Result: no contradiction.**

**Dependencies opened by the OD-1 answer:**
- **M-A:** OD-2 (template).
- **M-C or Both:** OD-2 (template with file delimiters), OD-3 (context and generation limits), OD-5 (protected set, and the retrieval-pool exclusion), OD-7/OD-8 (timeouts and retries under long prompts), OD-4 (harness scope including the retriever).
- **Both, additionally:** OD-9 (registry with two identities per instance), OD-12 (seed per condition), and a pre-declared generation-order or cache rule.

## D. Exact RD decision

For M2-PV-P1 only, choose one of **M-A**, **M-C** or **Both (paired)**.

If M-C or Both is chosen, the ruling must also fix, before execution and without tuning on any non-excluded task:
- the retriever (algorithm and version);
- the retrieval pool, including exclusion of test-patch paths and protected-surface files;
- k and the token budget.

## E. Unlocked once OD-1 is decided

- Drafting OD-2 (the exact template), and a concrete OD-3 analysis (prompt lengths against the default context, once the Stage-0 EXT facts are known).
- Scoping the OD-4 harness authorization, with or without the retriever.
- OD-9 and OD-12 wording.
- Recording P1's evidence plan for the later confirmatory-material decision (proposed **RD-13**; see below).

## F. Still blocked

- P1 execution: PB-1 harness authorization, OD-2 to OD-12, Stage-0 EXT inventory, admission.
- PV-freeze (BC-2), production-verifier implementation and validation.
- The BRP: RD-1, RD-2, RD-10, RD-11, RD-12, and the prerequisites in the BRP analysis.
- δ and the whole power chain.
- The successor specification freeze (G-A8).
- Implementation of anything.

**Proposed new register entry (not decided): RD-13 — confirmatory material composition.** This is the confirmatory material → prompt function the BRP must use. It affects task identity, memory-retrieval queries, D-2 exposure and D30.3. It is decided after P1, informed by its OD-1 evidence.

---

## RD RULING (2026-09-29): P1 OD-1 = M-C

For M2-PV-P1 only: issue plus fixed non-gold source retrieval. Paired M-A/M-C was not chosen, because it doubles generation and adds experimental degrees of freedom that P1's feasibility question does not need. The follow-on drafts are in `P1_OD-2_OD-3_RETRIEVAL_SPEC_DRAFT.md`.
