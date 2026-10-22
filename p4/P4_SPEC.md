# M2-PV-P4: Stage-1 feasibility gate on an uncontaminated repair corpus (SPECIFICATION DRAFT)

**Status:** DRAFT **v0.2**, 2026-10-12. Not ratified. **Nothing in this document is authorized to run.**
- v0.2 incorporates the RD decisions U-1 … U-8 (decision log, §16).
- **Order before execution:** RD review → SRC (Gemini) review → RD freeze → explicit RD execution authorization (§14).
- **Predecessors:**
  - P3: Velith-research `7b5118a` + erratum `49fc72d`.
  - F-1 fix: Velith `29fd12f` (D32).
  - SRC review C1–C5 (2026-10-12).

> **Blockers found while preparing v0.2.** These must be resolved before FG-0 and are reported here, not worked around (§15):
> - **B-1. The eligible pool may be empty.** The official SWE-bench-Live **Python** dataset (the RD's chosen source, U-3) shows task `created_at` values only up to **2025-08-30**. Its 2026 updates went to the MultiLang and Windows datasets. No Python task is known to exist after the 2026-08-01 cutoff (U-2).
> - **B-2. The Stage-1 input interface is not yet specified in Velith.** No real-dataset `TaskAdapter` exists; M5 places it out of scope. The P2/P3 oracle-file condition derives file selection from the gold patch, which is in tension with **D28 D-2** ("gold patches … must never enter `material` or `prompt`").
> - **B-3. The Stage-1 generation settings are not yet specified.** D31 item 7 requires T = 0.0 for evaluations of record, but this generator rejects `temperature`.
> - **B-4. Pool size versus Stage-1 reserve.** Illustrative Stage-1 power planning needs roughly 120–210 uncontaminated tasks in reserve, plus P4's 50 and the 2 compatibility-check tasks.

## 1. Question

> Does `claude-opus-5-5` have **sufficient uncontaminated zero-shot repair capability**, under the **intended Stage-1 input interface and settings**, to serve as the **A0 baseline** of Velith Stage 1 (D8.5, D31)?

- P4 is a pilot feasibility gate, **not** a Stage-1 evaluation of record.
- Its tasks and its compatibility-check tasks are permanently excluded from Stage 1 (D31 item 10).
- **Why it is needed.** P3's 6/13 is not interpretable as zero-shot capability, because 7/13 patches reproduce the upstream changed lines verbatim (F-2). Stage 1 needs a base rate that is neither at the floor nor at the ceiling.

## 2. Generator (U-1)

**Pinned:** provider Anthropic, endpoint `POST https://api.anthropic.com/v1/messages`, `anthropic-version: 2023-06-01`, model ID **`claude-opus-5-5`**. This is the documented model ID for Opus 5.5 on the Claude API.

**Documented facts** (Claude Platform docs, `models/opus-5-5/overview`, retrieved 2026-10-12):

| Item | Value |
|---|---|
| Training / reliable knowledge cutoff | June 2026 / June 2026 |
| Released | 2026-09-22 |
| Thinking | Adaptive, always on, cannot be disabled; depth via `effort` (default `medium`) |
| `temperature` | Rejected for this model (observed in P3, HTTP 400; amendment A-1) |
| Price | $4 / $20 per MTok (input / output) |

**Recorded per request:**
- the request body (the prompt is recorded as its SHA-256; the key is never recorded);
- every request parameter;
- UTC date and time;
- the response `id`, `model`, `stop_reason`, `usage` (including thinking tokens) and content-block types.

A response `model` other than `claude-opus-5-5` is a stop (§12).

## 3. Chronological eligibility (U-2): boundary B = 2026-08-01T00:00:00Z

B gives a one-month margin after the documented June 2026 training cutoff. **The cutoff is never weakened.** If the pool is insufficient, the result is reported as **P4-POOL-INSUFFICIENT** (§7).

A task is eligible only if **every** timestamp is ≥ B.

| Item | How verified |
|---|---|
| Issue opened | GitHub issue `created_at`, for every linked issue |
| Fix PR opened | PR `created_at` |
| Earliest PR commit | min(author date, committer date) over all PR commits |
| PR merged | PR `merged_at` |
| Base commit | committer date of the dataset's `base_commit` |

**Exclusions** (any one excludes the task):
- **E1. Pre-existing fix.** Any added line of the gold patch (at least 3 non-trivial lines per hunk) is found by `git log -S` over **all refs** of the upstream repository restricted to commits dated before B. This covers backports, cherry-picks and earlier branches.
- **E2. Earlier origin.** A linked, duplicate or referenced issue or PR opened before B contains a proposed fix (a diff or code block touching the gold files).
- **E3. Same change earlier.** The fix commit's `git patch-id` equals that of any commit dated before B in the upstream repository's refs.
- **E4. Not a code change.** The gold patch touches only docs, tests or configuration.
- **E5. Chronology unverifiable.** Any timestamp in the table cannot be retrieved.

**Recorded per candidate:** the chronology evidence (API responses and `git` outputs, hashed) in the pool manifest.

## 4. Corpus source, inventory and partition (U-3, U-8)

**Source (U-3).** One fixed, versioned **SWE-bench-Live Python-only** snapshot, identified by its Hugging Face dataset revision hash and its per-task image digests. **No silent source change.** If this source cannot supply the pool, P4 stops at FG-1 with **P4-POOL-INSUFFICIENT**, and any change of source is a new RD decision.

**Known status (B-1).** The dataset viewer, retrieved 2026-10-12, reports `created_at` from 2024-01-01 to **2025-08-30** across 3,688 rows in four splits. That is the PR creation date, the only date field the dataset provides. The maintainers announced monthly Python updates on 2025-09-17. Their later announcements (2026) concern MultiLang, which has no Python, and Windows. Until FG-1 measures it, the expected eligible count is **zero**.

**FG-1 inventory (read-only; no images, no generation):**
1. Download the snapshot rows at the pinned revision.
2. Apply §3 to every Python task with PR `created_at` ≥ B.
3. Write the pool manifest: revision hash, row hashes, chronology evidence and the eligibility verdict per task.
4. Report N_eligible.

**Reserve before selection (U-8).** The Stage-1 reserve size R is fixed by the Stage-1 successor's own power and sample-size plan, not by P4.
- **P4 needs** N_eligible ≥ R + 50 (P4) + 2 (compatibility check), before admission losses. If that fails, the result is P4-POOL-INSUFFICIENT.
- **Illustration only**, not a decision (exact conditional sign test, one-sided α = 0.01, power ≥ 0.80):
  - with δ = 0.15 (p01 = 0.20, p10 = 0.05), about 115–120 tasks;
  - with δ = 0.10 (p01 = 0.15, p10 = 0.05), about 205–210 tasks.
  - D31 fixes δ only after the pilot base rate, so the Stage-1 plan must size R under a declared planning δ.

**Partition.** Before any selection:
- a frozen lottery splits the eligible pool into the **Stage-1 reserve** (R), the **compatibility set** (2) and the **P4 frame**;
- the seed is derived from the pool-manifest SHA-256;
- all P4 and compatibility tasks enter the exclusion registry.

**Compatibility check (U-3).** Two tasks are drawn **only** from the compatibility set. They are used solely to show that the frozen probe gate, the pinned image and the dataset adapter work end to end: gold Case A, no generation. They are never used in P4 or Stage 1.

## 5. Stage-1 input interface and settings (U-4, U-5)

**Prerequisite (B-2).** P4 uses exactly the input interface Stage 1 will use. That interface does **not** yet exist.
- Velith's `TaskAdapter` seam (M5) has only the fixture adapter; a real-dataset adapter is out of scope in M5.
- D28 D-2 constrains it: `Task.prompt` must be a pure function of `material`, and gold patches, hidden tests and protected-surface details must never enter `material` or `prompt`.

**Therefore** the **real-task adapter prompt contract** must be specified and ratified, as a Velith decision, **before the P4 corpus is selected (FG-0b)**. P4 does not invent it.

**Requirements P4 places on that contract:**
- it is gold-blind (D28 D-2);
- it is deterministic, a pure function of `material`;
- its content and size are budgeted within the generator's context;
- it is identical between P4 and Stage 1.

**Candidates for the RD:**
- **I-1. Problem statement only.**
  - It's the SWE-bench protocol, but that protocol assumes an agent with repository access.
  - Velith's proposer is single-shot and has no repository tools, so I-1 is expected near the floor.
- **I-2. Problem statement + gold-blind retrieved source files.**
  - Uses the P1 OD-2 template and the OD-3 BM25 retrieval, already specified and frozen in research.
  - Compatible with D-2. **CSE recommendation.**
- **I-3. Problem statement + oracle gold files (P2/P3).**
  - File selection derives from the gold patch, so it is in tension with D-2.
  - It needs an explicit RD ruling and would only measure a localization-free upper bound.

**Settings (U-5).** `effort = medium`, `max_tokens = 8192`. Both are frozen in the PILOT_SET **only if** the Stage-1 settings decision (FG-0b) adopts the same values. Otherwise P4 adopts the Stage-1 values.
- **B-3:** D31 item 7 (T = 0.0) cannot hold for this generator, and a new decision is required.
- No temperature and no system prompt.
- One generation per task, never rerun. At most one retry, only if no completion was received.

## 6. Frozen before generation (task 1)

The following are frozen at **FG-6** in `p4/PILOT_SET.json`, each with a SHA-256:
- the task-selection and exclusion rules (§3, §4);
- the pool manifest, partition and exclusion registry;
- per task: dataset row hash, image digest, spec, **gold patch** (admission only, never in a prompt), **test patch**, FAIL_TO_PASS / PASS_TO_PASS lists, Stage-X timeout, and **prompt bytes** (built by the ratified interface, with prompt SHA);
- the generation parameters (§5);
- the semantic-validity rubric (§9);
- the scoring rules and decision bands (§8);
- the harness, adapter and extractor SHAs;
- the pinned image ID (§10).

Any later change to any of these is a stop (§12).

## 7. Admission and selection

- **Admission** (P2 Phase-A pipeline with a SWE-bench-Live adapter). A task is admitted only if all hold:
  1. the image is pulled by digest and its identity checked;
  2. the spec is built;
  3. **Case A:** the gold patch PASSES the frozen gate;
  4. the base blob equals the working tree for the files the interface reads;
  5. the prompt fits the token budget;
  6. the leakage audit PASSES (no gold or test text in the prompt);
  7. chronology eligibility is re-confirmed.
- **Selection:** a frozen-order walk over the P4 frame, with a repository cap of ≤ 4 and no backfill, until **n = 50** are admitted.
- **Outcome codes before any generation:**
  - **P4-POOL-INSUFFICIENT:** N_eligible < R + 52, or fewer than 40 admitted. This is reported as a substantive finding, not a failure.
  - **P4-D:** void for infrastructure reasons.

## 8. Outcomes, statistics and decision rule (U-6, U-7)

**A0 (P4).** The generator under the ratified interface and settings (§5): zero-shot, no memory, one attempt per task.

**Primary outcome: semantically valid verified repair (SVR).** All three must hold:
1. **gate pass** (VERIFIED_PASS: every FAIL_TO_PASS and PASS_TO_PASS test passes);
2. **extended regression:** no new failure relative to the gold patch in the full test files of the touched modules;
3. **no disqualifier** from §9.

The **gate-only pass rate** is reported as a secondary outcome.

**Interval.** Exact **Clopper–Pearson, two-sided 90%** interval [L, U] for p0 = k / n_v.

**Decision rule** (thresholds frozen before the pool is drawn: p_low = 0.10, p_high = 0.80):

| Code | Interval condition |
|---|---|
| **P4-INFEASIBLE** | U < 0.10 |
| **P4-CEILING** | L > 0.80 |
| **P4-FEASIBLE** | L ≥ 0.10 **and** U ≤ 0.80 |
| **P4-INCONCLUSIVE** | any other interval (it straddles 0.10 or 0.80) |

**Integer bands at n_v = 50** (computed 2026-10-12; boundaries checked):
- **INFEASIBLE:** k = 0–1. At k = 1, U = 0.0914; at k = 2, U = 0.1206.
- **INCONCLUSIVE:** k = 2–9. At k = 9, L = 0.0972.
- **FEASIBLE:** k = 10–34. At k = 10, L = 0.1127; at k = 34, U = 0.7879.
- **INCONCLUSIVE:** k = 35–44. At k = 35, U = 0.8051; at k = 44, L = 0.7768.
- **CEILING:** k = 45–50. At k = 45, L = 0.8012.

**Reconciliation with v0.1:** identical to the v0.1 n = 50 row. Because some tasks may become NA, the rule is applied to the realized n_v (≥ 40) using the bands in Appendix A.

**Inconclusive policy (U-7).** Stop at n = 50. An INCONCLUSIVE result is reported as such: **no Stage-1 go and no automatic extension**. Any further data collection is a new, separately authorized study.

**Secondary outcomes:**
- PATCH_APPLIES;
- failure layers;
- `stop_reason`;
- thinking tokens;
- multi-fence and in-fence-prose counts (C2 monitor);
- gold similarity (§11).

**Not decided by P4:** δ, the Stage-1 n and power. P4 supplies the pilot base rate D31 item 8 requires.

## 9. Semantic-validity rubric (frozen; applied to every gate pass)

| Code | Disqualifier | Evidence required |
|---|---|---|
| D-a | Special-cases test values: a conditional on a literal from the FAIL_TO_PASS tests or the issue, returning a fixed output | The cited diff line(s) plus the matching literal |
| D-b | Neutering: removes or bypasses the behaviour at issue (constant return, swallowed exception, deleted branch) where the gold patch does not | The cited diff lines plus the corresponding gold lines |
| D-c | Touches tests or configuration (protected paths) | The gate's protected-path record |
| D-d | Extended-regression failure | Failing test IDs (candidate vs gold) |

**Review procedure:**
- Two independent reviewers (CSE; SRC with a redacted package).
- A disqualifier applies only with cited evidence.
- Disagreement goes to the RD, and is recorded.
- Both SVR and gate-only rates are reported.

## 10. Verifier image (task 4)

**Build procedure** (separately authorized, FG-4):
1. Export a clean tree with `git archive 29fd12ffb289defd3a490e6d7c5f16151aa856b7`, into a temporary directory outside both repositories.
2. Build with `docker build -f docker/verifier.Dockerfile -t velith-verifier:p4-29fd12f <tree>`.
3. **Never use `docker compose build`.** The compose file hardcodes `velith-verifier:m0`.

**Checks after the build:**
- `proposer.py` SHA-256 = `3986ae09…`;
- `velith-verifier:m0` still = `sha256:36c4c00b…`;
- record the new image ID and the base-image digest.

**Known non-determinism.** The Dockerfile's base tag isn't digest-pinned, so the recorded image ID is the pin.

## 11. Contamination audit (task 3) and its limits

**Before generation:**
- the §3 chronology plus E1–E3, per task;
- a leakage audit of the prompts.

**After generation:**
- for every generated patch, the changed-line overlap with the gold patch: exact identity, and a SequenceMatcher ratio;
- a search for **out-of-prompt specifics**, i.e. issue or PR numbers, identifiers or comments from the gold patch, linked discussion or commit messages that appear in the output but nowhere in the prompt (the P3-08 "GH4074" pattern);
- every flagged task listed with its evidence.

**Interpretation:**
- Flags are **evidence of possible exposure**, not proof.
- Exact overlap on short fixes can arise from convergence.
- A model cannot reproduce text it never saw, but it may have seen the same text through channels other than the fix itself.
- The **decision uses the rate over all valid tasks**, flagged ones included, as frozen. The rate with flagged tasks excluded is reported as a sensitivity analysis and never changes the decision code.

**Limits:**
- No visibility of private forks, mailing lists, chat, or non-GitHub mirrors.
- The vendor cutoff is a documented claim P4 cannot verify.
- Training on post-cutoff data, for example later fine-tuning, cannot be excluded.
- The audit cannot separate convergence from memorization for one- or two-line fixes.

## 12. Budget, stop rules, independence (task 6)

**Budget:**
- **API:** P4 uses at most 50 generations × (≤ 20k input × $4/MTok + ≤ 8,192 output × $20/MTok), about **≤ $12.50**. Hard cap **$20**; at the cap, the run stops and the result is P4-D. `count_tokens` preflight is free.
- **Compute:** FG-1 inventory, about 1–3 h (metadata and git history only). Phase A walks about 80–120 candidates at about 12–20 min each. Phase B runs 50 tasks. In total, about 25–45 h.
- **Storage:** per-pull free-space gate of ≥ 2.5 × compressed size + 10 GB; images are deleted after use.

**Stop rules** (resumable; a stop is never a task outcome):
- a response `model` ≠ `claude-opus-5-5`;
- the pinned image ID, extractor SHA, harness SHA or PILOT_SET SHA changes;
- the budget cap is reached;
- unresolved infrastructure failures on ≥ 3 tasks;
- a probe network mode other than `none`;
- missing chronology evidence for an admitted task;
- any write to frozen P1–P3 evidence or to the `m0` image.

**Independent review:**
- SRC review of this specification before freeze.
- After the run:
  - a read-only audit (P3 pattern);
  - an independent Docker reproduction of **every** SVR and gate pass;
  - two-reviewer semantic review;
  - SRC review of `P4_REPORT.md`.

## 13. Diagnostic: the six P3 passes (task 5; separate from P4's primary outcome)

**Inputs.** P3-04, -05, -07, -08, -09, -11, with the recorded patches. P3 evidence is unchanged and there are no API calls.

**Steps:**
1. Apply the §9 rubric (two reviewers).
2. Extended regression, candidate vs gold, in each task's image re-pulled by digest.
3. For P3-07 and P3-11, whose solutions differ from gold, a differential check on the issue's reproduction inputs.

**Output.** `p4/diagnostics/p3_six_pass_review.md`, **diagnostic only**. It never enters a P4 statistic or a P3 endpoint. It may run before P4 under its own authorization.

## 14. Gates (each separately authorized; in order)

| Gate | Content | Pass criterion |
|---|---|---|
| **FG-0a** | This specification: RD review → SRC review → revisions | Comments resolved |
| **FG-0b** | **Velith decisions:** (i) real-task adapter prompt contract (B-2); (ii) Stage-1 generation settings, including the T = 0.0 conflict (B-3); (iii) Stage-1 planning δ and reserve R (B-4) | Ratified D-entries in Velith `DECISIONS.md` |
| **FG-0c** | RD freezes this specification | Spec SHA-256 recorded |
| FG-1 | Pool inventory (§4), read-only | N_eligible reported. If < R + 52: **P4-POOL-INSUFFICIENT; stop and report** |
| FG-2 | Partition lottery + exclusion registry | Written once; hashed |
| FG-3 | Adapter and harness implementation + synthetic tests; compatibility check on the 2 compatibility-set tasks (gold only) | Tests pass; Case A works end to end |
| FG-4 | Build and pin `velith-verifier:p4-29fd12f` (§10) | SHAs match; m0 unchanged |
| FG-5 | Phase A admission | ≥ 40 admitted, ideally 50 |
| FG-6 | Preflight (`count_tokens`; extractor in the new image) + PILOT_SET freeze (§6) | PASS; PILOT_SET SHA recorded |
| FG-7 | Commit and push of FG-0…FG-6 artifacts | Remote verified |
| **FG-8** | **RD explicit execution authorization** | Recorded |

After FG-8: Phase B, then the audit, reproduction, semantic review, contamination audit, `P4_REPORT.md`, and SRC review.

## 15. Blockers and what each one decides

| ID | Blocker | Owner | Consequence if unresolved |
|---|---|---|---|
| B-1 | SWE-bench-Live Python shows no tasks after 2025-08-30 | RD (source decision) | P4-POOL-INSUFFICIENT at FG-1. The RD may authorize a new source or a self-curated corpus as a separate decision. |
| B-2 | Stage-1 input interface unspecified; I-3 in tension with D28 D-2 | RD + Velith governance | P4 cannot select a corpus (U-4) |
| B-3 | D31 item 7 (T = 0.0) is impossible for this generator | RD + Velith governance | P4 settings cannot be confirmed as Stage-1 settings (U-5) |
| B-4 | Reserve R (≈ 120–210, illustrative) + 52 may exceed any post-B pool | Stage-1 successor plan | Even a FEASIBLE P4 may not leave enough uncontaminated tasks for a powered Stage 1 |

## 16. Decision log (v0.1 → v0.2)

| ID | RD decision | Where applied | Note |
|---|---|---|---|
| U-1 | Pin `claude-opus-5-5`; record provider, endpoint, parameters, response metadata and date | §2 | |
| U-2 | B = 2026-08-01; never weakened | §3, §7 | Insufficiency is reported, not worked around |
| U-3 | One fixed, versioned SWE-bench-Live Python snapshot; 2-task compatibility check from an excluded set; no silent source change | §4 | **B-1:** the snapshot appears to end at 2025-08-30 |
| U-4 | Match the intended Stage-1 interface; specify it before corpus selection | §5, FG-0b | **B-2:** no Velith real-task adapter yet; I-3 in tension with D28 D-2; I-2 recommended |
| U-5 | `effort = medium`, `max_tokens = 8192`, if equal to the Stage-1 settings | §5 | **B-3:** D31 item 7 conflict |
| U-6 | 0.10 / 0.80 / 90% CP; explicit rule; integer bands reconciled | §8, App. A | Bands identical to v0.1 at n = 50 |
| U-7 | Stop at n = 50 when inconclusive; no automatic extension | §8 | |
| U-8 | Inventory first; reserve R from Stage 1's own plan; P4 and compatibility tasks never reused | §4, FG-1, FG-2 | **B-4:** illustrative R ≈ 120–210 |

## Appendix A — decision bands for realized n_v (90% Clopper–Pearson; p_low 0.10, p_high 0.80)

| n_v | INFEASIBLE | INCONCLUSIVE | FEASIBLE | INCONCLUSIVE | CEILING |
|---|---|---|---|---|---|
| 40 | 0 | 1–7 | 8–27 | 28–36 | 37–40 |
| 41 | 0 | 1–7 | 8–27 | 28–37 | 38–41 |
| 42 | 0 | 1–8 | 9–28 | 29–38 | 39–42 |
| 43 | 0 | 1–8 | 9–29 | 30–39 | 40–43 |
| 44 | 0 | 1–8 | 9–30 | 31–39 | 40–44 |
| 45 | 0 | 1–8 | 9–30 | 31–40 | 41–45 |
| 46 | 0–1 | 2–8 | 9–31 | 32–41 | 42–46 |
| 47 | 0–1 | 2–8 | 9–32 | 33–42 | 43–47 |
| 48 | 0–1 | 2–8 | 9–33 | 34–43 | 44–48 |
| 49 | 0–1 | 2–9 | 10–33 | 34–44 | 45–49 |
| 50 | 0–1 | 2–9 | 10–34 | 35–44 | 45–50 |

*End of draft v0.2. No implementation, download, image build, model call, task execution, commit or push is authorized by this document.*
