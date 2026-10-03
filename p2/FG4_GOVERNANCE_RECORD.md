# P2 FG-4 governance record (implementation and evidence conventions)

**Date:** 2026-10-03.
**Scope:** FG-4 Phase-A admission implementation, `p2/harness/p2_admit.py`.
- `P2_SPEC.md` (`b2d29c5c…`) is **not** modified.
- This record only fixes operational parameters and evidence conventions that the frozen specification leaves to implementation.

## 1. Case-A gold execution timeout (SRC ruling, accepted by RD)

| Item | Frozen operational value |
|---|---|
| Case-A gold run (admission step 3) | **hard timeout 1800 s** (`ADMISSION_CASE_A_TIMEOUT = 1800.0`) |
| Stage-X timeout (G-4, unchanged) | 900 s if the Case-A candidate container took ≤ 300 s, otherwise 1800 s |

**Reason.** The specification states "Case A once per candidate" but no admission timeout.
- An admission timeout below 1800 s would reject tasks that the G-4 rule explicitly provides for: gold runs of more than 300 s receive the 1800 s Stage-X timeout.
- The initial FG-4 draft reused the P1 admission value of 900 s. It was replaced by this ruling before any real admission ran.

**Production path.**
- `admit_candidate` passes exactly 1800.0 to `Ops.case_a`.
- `DockerOps.case_a` forwards it unchanged as `--timeout 1800.0` to the frozen probe CLI (`run --case A`), with a 2400 s subprocess guard.
- `test_case_a_gold_timeout_is_exactly_1800_on_the_production_path` verifies this.

## 2. Evidence directory convention (implementation only)

- Admitted tasks: `p2/evidence/P2-NN/` (`A/`, `P/`, `SELF-S/`, `record.json`), numbered in admission order.
- Rejected candidates: `p2/evidence/_admission/<rank>-<instance_id>/`.
- Summary: `p2/evidence/_lottery/admission_log.json`.

This convention does **not** affect eligibility, admission, replacement, arm assignment, endpoints or the population.

## 3. G-10 (unchanged)

The gold-derived S self-check is diagnostic only. It runs only after the admission decision has been fixed and recorded, and only for admitted tasks. It never alters admission, eligibility, order, substitution, arm assignment, endpoints or the population. An A-1 alarm halts the run after the record is written and the image removed.
