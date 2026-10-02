# M2-PV-P1 final report: five-task real-task feasibility pilot

**Date:** 2026-10-03.
**Status:** FINAL. All five P1 generation episodes (T1–T5) are complete, one generation each, and final. No further P1 model episode will run.
**Pilot question** (P1 design §2): *Can the current proposer produce usable patches on real software-engineering tasks under the proposed sealed-task execution architecture?*
**Condition:** a single condition, M-C (OD-1 ruled 2026-09-29: issue text plus fixed non-gold retrieval). The design's paired M-A/M-C row does not apply.

**Frozen inputs** (all re-verified unchanged at report time):

| Artifact | SHA-256 |
|---|---|
| `M2-PV-P1_PILOT_DESIGN.md` (pre-declared §17 measurements, §18 failure table, §24 C1–C4) | `89f931e0dc37c2a1…` |
| `p1/PILOT_SET.json` | `0f0e8715511ad262…` |
| `p1/PILOT_EXCLUSION_REGISTRY.json` | `9fc0157b3c21b99a…` |
| `p1/harness/p1_harness.py`, `p1_gen.py`, `P1_HARNESS_SPEC.md` | `c4ad73e3…`, `c84a614c…`, `d99840d5…` (equal to `PILOT_SET.json`) |
| Frozen M2 probe / Velith commit | `560834d5…` / `6ca531f5…` |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`, manifest digest `e196dcd9…c45c`, temperature 0.0, `num_ctx` 16384, `num_predict` 1024 |

**Episode records** (the sole sources for §3):

| Record | SHA-256 |
|---|---|
| `p1/P1_T1_EPISODE_RECORD.md` | `ae5fd351978eac94…` |
| `p1/P1_T2_EPISODE_RECORD.md` | `1e0334d890fd715e…` |
| `p1/P1_T3_EPISODE_RECORD.md` | `4242c5f81e6c53a1…` |
| `p1/P1_T4_EPISODE_RECORD.md` | `2ac69b9cc4a1b6d1…` |
| `p1/P1_T5_EPISODE_RECORD.md` | `1f39c0aac4ee27b0…` |

Every episode evidence directory passes `sha256sum -c` on its `MANIFEST.sha256`.

---

## 1. Observed facts (raw counts; P-3: counts only, no percentages, ranks or scores)

| Measure | Count |
|---|---|
| Admitted tasks (Stage 1, §9) | 5 of 5 slots |
| Admissible at Stage P (within budget, leakage audit PASS, non-empty retrieval) | 5 of 5 |
| Interpretable episodes (`interpretable` = true) | 5 of 5 |
| `patch_produced` = true | **5 of 5** |
| `patch_applies` = true | **0 of 5** |
| Probe `verified_outcome` | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY: **5 of 5** |
| §18 failure-table code | PATCH_DOES_NOT_APPLY: **4** (T1, T2, T3, T5); MALFORMED_PATCH: **1** (T4) |
| Infrastructure failures: GEN_INFRA, EXEC_INFRA, BASELINE_UNHEALTHY, RESOURCE_EXHAUSTED, TIMEOUT, HARNESS_FAILURE | **0** each |
| Generation retries / Stage X retries / pre-request STOPs recorded | 0 / 0 / 0 |
| Flags (GEN_TRUNCATED, TOKEN_COUNT_MISMATCH, CONTEXT_LENGTH_NOT_CONFIRMED, TEST_INTEGRITY) | **0** on every episode |
| Candidate tests run | 0 of 5 episodes. Every candidate stopped at `git apply` (exit 92), `mapped_required` = 0. |
| Baseline health | 5 of 5 RAN. All required IDs mapped. Every P2P passed and no F2P passed (the frozen `classify` precondition). |

**Per-episode primary measurements (P1 §17):**

| Slot | instance_id | patch_produced | patch_applies | verified_outcome (classification / reason) | §18 code | prompt / completion tokens | latency (s) | Patch SHA-256 |
|---|---|---|---|---|---|---|---|---|
| T1 | `pallets__flask-5014` | true | false | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY | PATCH_DOES_NOT_APPLY | 15197 / 87 | 910.27 | `3a4bb3927e0149e00f66b8dc142f49cee02e93e004a7f9a8086ce259ddefe9c0` |
| T2 | `matplotlib__matplotlib-24970` | true | false | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY | PATCH_DOES_NOT_APPLY | 15129 / 171 | 962.45 | `f9d63f09cc031385b9973c47f6ab5d4e5093f1ef146183ba459c4b6aa6546c3a` |
| T3 | `scikit-learn__scikit-learn-14629` | true | false | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY | PATCH_DOES_NOT_APPLY | 14892 / 154 | 927.85 | `1a8b91d8bcbe7914398efa88c053eabe3dc81283c5d35e726c4d0dc781e0b015` |
| T4 | `astropy__astropy-7336` | true | false | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY | MALFORMED_PATCH | 15227 / 116 | 933.34 | `54273a36cab2ed2efec363880a8f6580ee9fc6c81c75c440d846f504ca1519e7` |
| T5 | `pydata__xarray-7393` | true | false | PATCH_APPLY_FAILED / CANDIDATE_PATCH_DID_NOT_APPLY | PATCH_DOES_NOT_APPLY | 14953 / 143 | 852.22 | `9dae249b6fb21420aee73e143a8826c83e2b897e42a4ac931d5aadf44c353ae2` |

- **Token counts:** in every episode the observed `prompt_eval_count` equals the pre-flight prediction exactly. `/api/ps` confirmed `context_length` 16384. Every request started cold.
- **Completions:** each completion is a single fenced `diff` block, and no completion reached `num_predict`.

---

## 2. Pre-declared conclusion (P1 §24, applied exactly as written)

**Governance note.** §24 is marked in the design as "[RATIFIED principle; rules PROPOSED]". The rules were content-addressed in `89f931e0…` before any execution. They are applied here exactly as written, per the RD's instruction to treat them as frozen. No new threshold or criterion is introduced.

| Rule | Pre-declared condition | Observed | Holds? |
|---|---|---|---|
| **C1** The proposer produced no usable patch on the admitted pilot population (per condition) | ≥ 3 admissible tasks **and** none with `patch_applies = true` | 5 admissible; 0 with `patch_applies = true` | **YES** |
| **C2** The proposer can produce usable patches on at least some selected tasks | ≥ 1 admissible task with `patch_applies = true` | 0 | no |
| **C3** Infrastructure prevents interpretable completion | < 3 admissible tasks after replacement, **or** unresolved GEN_INFRA/EXEC_INFRA on ≥ 3 tasks | 5 admissible; GEN_INFRA 0, EXEC_INFRA 0 | no |
| **C4** A specific architecture component blocks feasibility | (i) systematic INADMISSIBLE_LEAKAGE from context overflow; (ii) PB-1 unresolved; (iii) persistent GEN_INFRA | (i) 0 INADMISSIBLE_LEAKAGE: every prompt was within budget and passed the audit; (ii) PB-1 resolved by the authorized harness; (iii) GEN_INFRA 0 | **no**, as written |

### Frozen P1 conclusion

> **C1: under condition M-C, the proposer produced no usable patch on the admitted pilot population. Observed: 0 of 5 admissible (task, condition) pairs with `patch_applies = true`.**

**Why it follows.**
- §4 defines "usable patch" as a produced patch that applies cleanly with `git apply` in the sealed container.
- All five admissible episodes produced a patch, and all five failed `git apply`.
- C1's two pre-declared conditions are both met: at least 3 admissible tasks, and none applies.
- C3 is excluded because all five episodes were interpretable, with no infrastructure failure.

**Scope** (P1 §24, "explicitly not concluded"): this is **not** a solve rate, a model ranking, an A0/A1/A2 or memory claim, a statement about production-verifier correctness, or a generalization beyond these five tasks and this model configuration.
- It is an existence statement for n = 5 (RS-P6).
- Because no patch applied, no candidate test ran. **Semantic correctness was not established for any episode, in either direction.**
- PATCH_APPLY_FAILED episodes are not semantic failures and are not relabelled as such.

---

## 3. Forensic observations (from the five episode records; not verdicts)

The three failure dimensions are kept separate. "n/a" means the evidence cannot speak to that dimension.

| Slot | (A) Context / file size: was the edited file in the prompt? | (A) Was the gold file in the prompt? | (B) Diff-output reliability: hunk well-formed? | (B) Context lines match base? | (C) Semantic correctness |
|---|---|---|---|---|---|
| T1 | yes (`src/flask/scaffold.py`) | not assessed (gold not in T1 evidence) | yes (5/5 counts consistent) | no: the old-side block omits base lines 3–6 | not established |
| T2 | no (`lib/matplotlib/colors.py` = gold; BM25 rank 1; skipped by the fit rule at 29,222 tokens) | no | yes (7/7) | no (unsourced) | not established |
| T3 | no (`sklearn/model_selection/_validation.py`; rank 21; skipped at 29,045) | no (`sklearn/multioutput.py`; rank 6; skipped at 19,146) | yes (7/7) | no (unsourced) | not established |
| T4 | yes (`astropy/units/decorators.py` = gold) | yes | **no**: header 7/7 vs body 4/4, so `corrupt patch at line 9` | no (by inspection; `git apply` never reached context matching) | not established |
| T5 | no (`xarray/core/dataset.py`; rank 4; skipped at 101,682) | no (`xarray/core/indexing.py`; skipped at 23,401) | yes (7/7) | no (unsourced) | not established |

Observation counts, stated as counts only:
- **The edited file was not in the prompt in 3 of 5 episodes** (T2, T3, T5). In each, BM25 had ranked that file within its top 21, and the frozen whole-file, no-truncation fit rule excluded it as larger than the 15232-token budget allows.
- **The gold file was not in the prompt in 3 of the 4 assessed episodes** (T2, T3, T5). T1 is not assessed.
- **The edited file was in the prompt in 2 of 5 episodes** (T1, T4), and the patch still did not apply:
  - T1: the context lines did not match the verbatim file shown;
  - T4: the hunk was malformed.
- **Well-formed hunks: 4 of 5.** Malformed: 1 of 5 (T4).
- **Location relative to the gold file** (assessed T2–T5):
  - same file: 2 (T2, T4);
  - different file: 2 (T3, T5).
  - This says nothing about semantic correctness.

---

## 4. Component attribution (analysis; NOT a C4 conclusion)

C4 does not hold as written: none of its three pre-declared conditions occurred. The following is therefore an analytical attribution from §3, offered as design input. It is not an additional pre-registered conclusion.

1. **Context and file-size limitation of the M-C contract at 16k.** The frozen policy is whole-file retrieval, a 15232-token budget, and skip-if-it-doesn't-fit. It withheld the edited file in 3 of 5 episodes and the gold file in 3 of the 4 assessed episodes, even when BM25 ranked it highly. In those episodes the model could not have copied valid diff context from the prompt.
2. **Patch / diff-output reliability of the raw unified-diff contract.** Even with the target file present (T1, T4), the model wrote context lines that did not match the shown file. In one case (T4) it also wrote an inconsistent hunk header. The output contract requires exact line numbers and verbatim context, and those were not produced reliably in this pilot.
3. **Semantic correctness: not attributable.** It was never observed, because no patch applied. Nothing in P1 supports a claim about the model's semantic repair ability, in either direction. The public-fix contamination residual (RS-P1) remains unquantified.
4. **Verified as not blocking (infrastructure):**
   - sealed digest-pinned execution, network none, baseline control;
   - the frozen probe as a library (PB-1 resolved);
   - exact HF-tokenizer pre-flight (5 of 5 exact);
   - model identity and context pinning;
   - cold-start and unload discipline;
   - evidence manifests.

   Cost per generation at about 15k prompt tokens on this host was 852–962 s.

---

## 5. Successor design inputs (research inputs only; P1 is not modified)

These are requirements for a **separately designed, separately pre-registered** successor. They are not changes to P1. The successor must not reuse any of the 11 registry instance IDs as held-out or evaluation tasks.

- **S-1 (context).** Make the edit target available without exceeding the window. Options: function- or section-level retrieval instead of whole files; a larger context; or a two-stage locate-then-edit design. Any retrieval must stay non-gold (P1 §22 discipline).
- **S-2 (output contract).** Remove the dependence on model-authored line numbers and verbatim context. Options: search/replace or whole-symbol replacement edits applied by the harness with exact-match checks; or harness-side diff synthesis from an edited region. The format must be fixed before any task is seen.
- **S-3 (measurement).** Pre-declare separate measurements for target localization, output-format validity and application, so that each layer above is observable. Semantic correctness requires a patch that applies.
- **S-4 (reuse).** Keep the P1 infrastructure contract unchanged in substance: digest pins, exact token pre-flight, frozen probe library path, sealed execution, manifests, one-shot generation.
- **S-5 (governance).** A new task lottery and admission, exclusion of all P1 registry IDs, and an RD ratification before any execution.

---

## 6. Exclusion registry: final bookkeeping (no membership change)

`p1/PILOT_EXCLUSION_REGISTRY.json` (SHA-256 `9fc0157b3c21b99a…`) is **final as frozen and is not rewritten.** It lists 11 entries:
- **5 admitted**, with `pilot_task_identity` equal to each episode's prompt identity: `pallets__flask-5014` `e2671b01…`, `matplotlib__matplotlib-24970` `fe8e73c9…`, `scikit-learn__scikit-learn-14629` `115f516e…`, `astropy__astropy-7336` `4d82ad43…`, `pydata__xarray-7393` `c3109b06…`.
- **6 rejected at admission (exposed):** `matplotlib__matplotlib-24570`, `-26466`, `-26342`, `-24149`, `-22719`, `pydata__xarray-6721`.

This report changes neither membership nor eligibility. The registry remains an audit and safety registry (R4), not a selection rule. Its code enforcement remains a future amendment (P1 §10, OD-9).

---

## 7. Binding statements

1. P1 is **closed**. T1–T5 are final one-generation evidence. None may be rerun or regenerated.
2. The official episode classifications are preserved exactly (§1). PATCH_APPLY_FAILED is not reinterpreted.
3. **No post-hoc tuning is authorized:** no harness, prompt, retrieval, token-budget, model, generation-parameter, extraction or verifier change. The P1 artifacts and Velith main are unchanged.
4. Any successor (§5) is a new experiment that requires its own design, pre-registration and RD ratification.
