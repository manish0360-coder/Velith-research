# P2 Phase A report (FG-4 evidence)

**Date:** 2026-10-10.
**Run:** `p2/harness/p2_admit.py run` at Velith-research HEAD `7c039ca6`. One crash (HF datasets-server HTTP 502 during a row fetch), then one resume; final `exit=0`.
**Velith main:** HEAD `6ca531f5…`, the same commit as P1, clean.
**Model calls:** none.

## 1. Outcome

| Item | Value |
|---|---|
| Status | **OK**: n = **13** ≥ n_min 10 (target 20; ceiling 16) |
| Per repository | scikit-learn 4 (cap), astropy 4 (cap), xarray 4 (cap), matplotlib 1, flask 0 (no eligible tasks) |
| `admission_log.json` SHA-256 | `eba7b68f28c09f9a37793fcb321814ecedb137a54dbb5aaaa347be7011a286c2` |
| FG-3 artifacts | pool `8c870348…`, order `d9199f2c…`, unchanged |
| A-1 harness-integrity alarms | **0** |
| Images remaining | none (every record ends in `remove`, except PULL_FAILED, which never pulled) |

## 2. Admitted tasks (slot order = admission order)

All 13 admitted tasks have the following in common:
- all five admission steps true;
- both leakage audits PASS;
- Case-A candidate time of 4.6–20.3 s, so the Stage-X timeout is **900 s** for every task (G-4);
- G-10 self-check: parse OK, resolution OK, gate **true**, no missing-final-newline marker.

| Slot | Instance | Tokens U / S | Arm order |
|---|---|---|---|
| P2-01 | astropy__astropy-12907 | 3497 / 3486 | S, U |
| P2-02 | scikit-learn__scikit-learn-13496 | 5712 / 5701 | S, U |
| P2-03 | scikit-learn__scikit-learn-25931 | 6667 / 6656 | U, S |
| P2-04 | pydata__xarray-4966 | 5040 / 5029 | U, S |
| P2-05 | scikit-learn__scikit-learn-14141 | 1048 / 1037 | U, S |
| P2-06 | astropy__astropy-13579 | 5359 / 5348 | U, S |
| P2-07 | scikit-learn__scikit-learn-14496 | 10938 / 10927 | U, S |
| P2-08 | pydata__xarray-4075 | 3410 / 3399 | U, S |
| P2-09 | astropy__astropy-14365 | 6821 / 6810 | S, U |
| P2-10 | astropy__astropy-13453 | 7475 / 7464 | S, U |
| P2-11 | pydata__xarray-3151 | 8596 / 8585 | S, U |
| P2-12 | pydata__xarray-7233 | 12018 / 12007 | S, U |
| P2-13 | matplotlib__matplotlib-20859 | 13726 / 13715 | S, U |

Arm order follows the frozen §13 hash rule (6 tasks U first, 7 tasks S first). Under the containerd image store, the image ID equals the manifest digest for every task.

## 3. Rejected candidates (all appended to the P2 registry at FG-6)

| Rank | Instance | Reason | Cause |
|---|---|---|---|
| 1 | pydata__xarray-2905 | F_OVER_BUDGET | 28200 tokens > 15232 |
| 4 | scikit-learn__scikit-learn-14983 | F_OVER_BUDGET | 23465 tokens |
| 12 | pydata__xarray-6744 | CASE_A_NOT_PASSED | BASELINE_UNHEALTHY (pass_to_pass not passed) |
| 14 | pydata__xarray-4695 | PULL_FAILED | **infrastructure**: pull and retry both failed |
| 24 | matplotlib__matplotlib-25311 | SPEC_FAILED | **infrastructure**: HF datasets-server HTTP 502 inside the frozen spec builder |
| 32 | matplotlib__matplotlib-25332 | F_OVER_BUDGET | 22616 tokens |
| 49 | matplotlib__matplotlib-20676 | F_OVER_BUDGET | 34062 tokens |

All other pool entries were skipped because their repository had reached the cap, or (matplotlib) the pool was exhausted.

## 4. Deviations and threats (recorded, not corrected)

1. **Two rejections were caused by infrastructure, not by task properties** (xarray-4695, matplotlib-25311). The frozen rules treat them as inadmissible: a pull gets one retry (§14), and spec building has no retry. No post-hoc re-admission is made (no post-hoc changes, no backfill).
   - Effect on xarray: the cap was still reached, but the composition changed. Without the failure, xarray-4695 could have been admitted in place of xarray-7233.
   - Effect on matplotlib: n could have been 14 instead of 13, if 25311 also fit the token budget, which 3 of the 4 matplotlib candidates did not.
2. **Inconsistent HTTP 502 handling in the FG-4 harness (defect, for the record).**
   - A 502 in `stage_p` → `fetch_row` stops the run, which is then resumable.
   - The same 502 inside the spec-builder subprocess is recorded as SPEC_FAILED, which is a rejection.
   - Fix for future pilots: treat a transient dataset-API failure in any admission step as a pilot-level stop. This is not applied to P2 (frozen).
3. **Interrupted attempt preserved.** `_admission/22-matplotlib__matplotlib-20859.interrupted-1/` is the attempt that crashed on the 502 (undecided, image removed). On resume, the task was re-evaluated from scratch and admitted (P2-13), under the approved resume rule.

## 5. Next gates

- FG-5: `p2_phaseb.py gencheck`.
- FG-6: `p2_phaseb.py freeze`.
- FG-7: no `/api/generate` request in the Ollama log since FG-0.
- FG-8: one commit and RD review.
- Then Phase B: `p2_phaseb.py run --pilot-sha <PILOT_SET SHA>`.
