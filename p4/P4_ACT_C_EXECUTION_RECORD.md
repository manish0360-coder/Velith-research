# P4 sizing probe: execution record after Act A (append-only)

**Status:** current record, opened 2026-10-22. New entries are appended; earlier entries are never rewritten.
This record edits no frozen artifact. It does not modify the protocol (`P4_SIZING_PROBE_PROTOCOL_v0.3.md`,
`a34a729d…`), its marked block (`f8a7e398…`), the Act-A record (`68b6f301…`), GN1/GN1-r1, the census code
(`23e410ca…`), the probe (`2c4acbcc…`) or the live wrapper (`run_live_probe.sh`, `904692c2…`).

## 1. Completed acts (verified evidence)

| Item | Commit / value | Evidence |
|---|---|---|
| T-1: lock tests made state-independent | `8c18461b43cdfe77194dbf40717a4dfbda55e602`; `p4/probe/test_sizing_probe.py` `e9c97275…` | Strict offline gate in WSL (networking removed): probe 37/37, census 39/39, no skip/xfail/xpass |
| Act B: lock activation | `f57c0c2b8eb38f5b5ed9b916793e2760fced1030`; `p4/probe/sizing_probe.py` `2c4acbcc…` (Act-A expected value) | `identity`: block `f8a7e398…`, `census_code_ok True`, `frozen_protocol_sha f8a7e398…`; same strict gate re-run after the edit |
| Offline readiness (2026-10-22, WSL) | — | Archive directory present; primary baseline `run1.preserved-20261016T063538Z`: exists, `MANIFEST.sha256` verifies, `baseline-check` exit 0 (1000 items, 999 unique), read-only. Alternate `run1`: verifies but writable (informational; not read by the wrapper) |
| DP-1 (RD disclosure policy, 2026-10-22) | "DP-1: owner local filesystem paths accepted in public Velith-research; credentials never" | Per-file disclosure report `c47c7f82…` (14 files, 36 lines) acknowledged exactly; 0 credential hits over all 58 blobs of the push range |
| Push | `bf5e9cd..f57c0c2` (six commits: `1f02792`, `0b36ae6`, `bc2efbc`, `feae5f0`, `8c18461`, `f57c0c2`) | Guarded fast-forward push; remote `main` = `f57c0c2` (GitHub `branches/main`). No push-triggered CI exists in this repository (0 check runs on `f57c0c2`; the only workflow is manual) |

## 2. Act C preflight (2026-10-22): result

All gates passed except one. Remote HEAD, frozen hashes, identity, authorization gates, baseline immutability,
protected roots, output-directory and archive no-overwrite checks, request/credential specification, evidence
preservation, and "no census v2 / no protocol change" all PASS.

**Gate 5a FAIL: one live run was not mechanically enforced.** The wrapper's authorization string is static and
every invocation gets a new timestamped output directory, so a second invocation would silently produce a second
live measurement, contrary to the protocol's PR-2 "one live run".

## 3. One-shot launcher (fix for gate 5a) and its limitation

- **File:** `p4/probe/act_c_once.sh` (new; outside the frozen set). **SHA-256:** `23d524a36408a7286f040ac1a5eb213c224234fc06301555ecda8f5c4c6e8a70`.
- **Behaviour:**
  - all read-only gates run first: environment, RD string `P4_ACT_C_RD_AUTH`, token presence and fine-grained prefix, repository pin, working-tree state, frozen hashes, identity, baseline, protected paths, archive, no previous run;
  - it then claims `~/p4census/ACT_C_PR2.once` with an atomic `mkdir`, writes `claim.txt`, and starts the unchanged wrapper exactly once with `setsid nohup`;
  - the PID, session and console log are recorded in `launch.txt`, and the marker is made read-only;
  - the marker is never removed by the launcher. Any retry requires a new RD decision;
  - the token is read only from `GITHUB_TOKEN` and never printed or written. Because it is non-empty, the census client never falls back to `gh auth token`;
  - the frozen 200-request / 4.5 h caps are enforced by the unchanged probe;
  - `--status` is read-only.
- **Repository pin:** HEAD must contain `f57c0c2`. Later commits and the working tree may differ only in this record, `RESEARCH_STATUS.md` and the launcher itself, plus the two known unrelated modified files.
- **Limitation (verified by code inspection):** the marker binds only runs started through the launcher.
  - **Wrapper:** direct execution of `run_live_probe.sh` is not blocked by the existing mechanism. It requires only `P4_PROBE_RD_AUTH="PR-2 approved f8a7e398…"`, which is published in the repository, plus a credential (`GITHUB_TOKEN` or `gh auth`).
  - **Probe:** direct `sizing_probe.py run` requires only `P4_PROBE_PR2=AUTHORIZED`.
  - Closing this gap needs a change to frozen files, which requires its own review. Procedural mitigations:
    - use a single-purpose fine-grained token with a short expiry and revoke it after the run;
    - never run the wrapper or the probe directly;
    - note that a `gh` login on the host remains a fallback credential for direct invocations.
- **Fixture tests: 33/33 PASS in one complete run.** The run used no network, a fake token, a stub wrapper and a stub baseline-check.
  - **Suite and log:** `act_c_tests.sh` (`c0a6f893…`) and its log (`6e4af881…`), kept with the CSE working files.
  - **Count note:** an earlier uncommitted draft of this record said 31/31 because it omitted the two status-document wiring cases (T10a/T10b). Those cases are now part of the suite, and the 33 below come from one run.
  - **Inventory:**
    - T1: successful path. The wrapper starts once; the recorded PID equals its session id; the stub received the PR-2 string with `P4_PROBE_PR2` unset; the token value appears nowhere; the marker directory is mode 500.
    - T2: rerun after T1, marker present: STOP.
    - `--status` is read-only.
    - T3a–d: previous output directory, log, archive or checksum: STOP (4 cases).
    - T4: marker present in a fresh fixture: STOP.
    - T5a: wrapper hash mismatch: STOP.
    - T5b: frozen probe changed in a later commit: STOP.
    - T5c: HEAD lacks `f57c0c2`: STOP.
    - T5d: HEAD changes a non-allowlisted file: STOP.
    - T5e: frozen census code changed in the working tree: STOP.
    - T6a–c: unexpected untracked file, unrelated file changed, staged change: STOP (3 cases).
    - T7a–d: missing token, classic token, missing RD string, `P4_PROBE_PR2` preset: STOP (4 cases).
    - T8a–f: baseline manifest fails, baseline-check exit 1, baseline writable, archive missing, archive not writable, protected root `run1` missing: STOP (6 cases).
    - T10a: status documents untracked: launches once.
    - T10b: launcher and status documents committed after `f57c0c2`: launches once.
    - T9 rounds 1–5: three concurrent attempts per round; exactly one launch per round (5 cases).
  - **Bug fixed before these results:** the first version matched paths with piped `grep` under `pipefail`, which could falsely reject a valid run under concurrency. It was replaced by a pipe-free comparison; the hash above is the fixed file.

## 4. Remaining conditions for the one live Act C run

1. A separate, explicit RD authorization of Act C (supplied at launch as `P4_ACT_C_RD_AUTH`).
2. A newly created fine-grained token: public repositories read-only, no permissions, short expiry. Exported as `GITHUB_TOKEN` without echoing, and revoked after the run.
3. The launcher started from the repository root in WSL. The machine stays awake for about 2–3.5 h; at roughly one search request per minute, the frozen rate-limit pause makes 200 requests take about 3.3 h.
4. The full console output, the wrapper log and `--status` output are delivered to the CSE for evidence review against the frozen decision rules:
   - M_v ≤ 62 is STOP-POLICY;
   - EXACT with M_v ≥ 500 is ELIGIBLE-TO-PROPOSE census v2;
   - INCOMPLETE gives no census-v2 proposal.

## 5. Not done

Act C has **not** run. No live GitHub search request has been made, census v2 is not authorized, and the protocol is
unchanged.
