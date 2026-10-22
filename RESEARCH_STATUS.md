# Velith-research: current status

**Document type:** living current-state summary for this research repository. It replaces nothing: frozen records,
decision registers and historical drafts keep their own status lines and are not rewritten.
**Last updated:** 2026-10-22. Protocol commit `f57c0c2b8eb38f5b5ed9b916793e2760fced1030`; this file and the Act C launcher/record are committed on top of it.
**Authority:** ratified program decisions live in the main Velith repository's `docs/DECISIONS.md` (for example D31 and D32).
Files here named `*_DRAFT*`, `*_PROPOSED*` or `D31_GOVERNANCE_DECISION_*` are historical inputs to those decisions, not current governance.

## Recent commits (all pushed; repository is public under RD policy DP-1)

| Commit | Content |
|---|---|
| `bf5e9cd` | EPG-14 V0–V5 contract CAND-5: R-ACC recorded (accepted as a software-mechanics validation specification only) |
| `1f02792` | EPG-14 environment evidence (venue A `env.lock`, `env_record.json`, build inputs) |
| `0b36ae6` | EPG-14 M-H0 execution harness (synthetic stages only; WSL acceptance 16/16, criteria 1–8 met) |
| `bc2efbc` | IC-1 reference implementation of the I-2 material/prompt builder (RD-accepted; synthetic tests only) |
| `feae5f0` | P4 governance trail, sizing-probe protocol freeze record (Act A) and offline code |
| `8c18461` | T-1: sizing-probe lock tests made state-independent |
| `f57c0c2` | Act B: frozen sizing-probe protocol activated (`FROZEN_PROTOCOL_SHA` = `f8a7e398…`) |

## Workstreams

- **P4 task-supply measurement (Stage-1 critical path).**
  - Act A (protocol freeze), T-1 and Act B are complete, and the offline readiness checks pass.
  - **Act C (one live sizing-probe run) has not run** and awaits a separate RD authorization.
  - The Act C preflight found that one-run execution was not enforced; the one-shot launcher `p4/probe/act_c_once.sh` was implemented and fixture-tested as the fix.
  - Details, hashes, limitations and remaining conditions: `p4/P4_ACT_C_EXECUTION_RECORD.md`.
- **EPG-14 exact-power grid: parked (RD, 2026-10-22).**
  - The contract is accepted only as a bounded software-mechanics validation specification; it is not frozen.
  - R-MD is pending and R-V5 provisional; V0-7d and P2 (c) are NOT PERFORMED.
  - V0–V5 are neither authorized nor implemented, and the full grid is blocked.
  - The harness (M-H0) is accepted for synthetic stages only.
  - None of the statistical-validity questions (U-2 level-α over the composite null and general Lemma M, U-3 numerical error bounds, U-4 worst-case power) is resolved. By contract, EPG output cannot select δ, g, Δ_true or n.
- **IC-1:** committed; no further work authorized.

## Known documentation gaps (not changed here)

- Main Velith `docs/PROJECT_STATE.md` was last updated 2026-09-28 and does not yet mention D32 (`29fd12f`). By its own rule it is updated at milestone close, not mid-implementation.
- Main Velith `docs/ROADMAP.md` is empty.
- Both need a separately authorized documentation change in the main repository.
