# P4 sizing probe: protocol-freeze review package (for RD decision; NOTHING FROZEN, NOTHING EXECUTED)

**Date:** 2026-10-16.
- Q1 baseline validation was RD-run and verified: probe `df8aee08…`, `BASELINE_OK`, 999 unique ids = 999 unique names, `COPY_STILL_VERIFIES`.
- That check is **not** authorization to freeze or execute.

## 1. Freeze target

| Item | Value |
|---|---|
| Document | `p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md`, SHA-256 `a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4` |
| Marked block | `<!-- PROBE-PROTOCOL-BEGIN -->` … `<!-- PROBE-PROTOCOL-END -->` (§3–§6). SHA-256 of the exact UTF-8 bytes from the BEGIN marker through the END marker, inclusive: `f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d` |
| Computed by | `sizing_probe.protocol_block_sha()`, and `python3 -B p4/probe/sizing_probe.py identity` |

## 2. Implementation ↔ protocol correspondence

**Every block clause was checked against `p4/probe/sizing_probe.py`.** One documentation-level gap was found and fixed in the code only. The block is unchanged.

| Clause | Implementation | Status |
|---|---|---|
| §4.10: `run_meta.json` holds the request count | v0.3 code omitted it | Fixed: `requests`, `cache_hits_same_phase` and `outcome` added to `run_meta`. `run` also now converts a baseline or output-path `Stop` into a clean `STOP:` and exit 1, instead of a traceback. A new end-to-end test covers the post-freeze CLI path offline. |
| All other clauses: §3; §4.1–4.9 (per-phase sizes, S0, partition, enumeration, sweeps, rechecks, caps, lock, C0–C6, outcomes); §5 thresholds 62/500; §6 projections EXACT-only | Matching code paths, each covered by tests | Correspond |

**Code versions (prior versions kept in `p4/probe/history/`):**

| Version | Code SHA | Test SHA |
|---|---|---|
| PR-1 v0.2 | `6c0c9e46…` | `64d303bc…` |
| v0.3 | `df8aee08…` | `59b40207…` |
| **v0.3.1 (current)** | **`0b0584cee916455f39554270ef96dd31fd747ae4202ed7a0cfd1f169cddb9925`** | **`fdfc97b684752dbcf5c974cda04c671248c0758e8b87a51daf0047c2b54f86e9`** |

**Tests:** 36 probe and 39 census, **75 passed** in the CSE sandbox. Ruff and mypy are clean.

**Note:** Q1 ran the v0.3 code `df8aee08…`. `baseline_summary` and `load_baseline` are byte-identical in v0.3.1, so the Q1 result carries over.

## 3. Diff v0.2 → v0.3 (block)

Full unified diff: `p4/P4_SIZING_PROBE_v0.2_to_v0.3.block.diff`.

| Topic | v0.2 | v0.3 |
|---|---|---|
| **Q2: caching** | T_start and T_end shared one URL, so T_end was served from cache and C3 was vacuous. Sweeps could reuse cached band responses | Distinct `per_page` per phase (1/2/3/1–4/100/99/98/97). A cross-phase URL repeat is a STOP. Same-phase cache hits don't consume the request cap |
| **Q2: exactness** | — | EXACT requires S0 + C0–C6, and is defined as protocol completeness, not index completeness |
| **Q3: server range semantics** | Assumed | **S0 calibration**: 8 `repo:`-pinned queries prove inclusive `stars:` and `created:` endpoints and single-value ranges. A failure → STOPPED |
| **Q3: sweeps** | Gave up when a window had ≥ 900 results | Windows use the full partition rules |
| **Q5: lock** | CLI only | Also library-level: unmarked openers are refused, and `urlopen` is stubbed while not authorized |
| **Q5: output path** | — | Must be new and outside the baseline, `run1` and the archive |
| **Baseline** | — | 1,000 items, integer ids, unique ids = unique names |
| **Thresholds** | "STOP-RIGOROUS", "for any yield" | **STOP-POLICY** at M_v ≤ 62 (cap-4 arithmetic; 25% materiality is policy). **ELIGIBLE-TO-PROPOSE** at M_v ≥ 500 (policy threshold; not a yield bound or task sufficiency). The 610 rule stays withdrawn |

## 4. Network lock and the one-line PR-2 change (NOT applied)

**The lock today (`FROZEN_PROTOCOL_SHA = None`, line 38):**
- **CLI `run`** returns 3 before creating anything (L496–499).
- **Library `probe()`** refuses any opener not marked as a test double, and stubs `urlopen` (L373–385).
- Both hold even with `P4_PROBE_PR2=AUTHORIZED` set (tests).

**After a separate explicit freeze decision only**, replace line 38 of `p4/probe/sizing_probe.py`:

```
- FROZEN_PROTOCOL_SHA: str | None = None  # set ONLY at PR-2 by a reviewed edit
+ FROZEN_PROTOCOL_SHA: str | None = "f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d"  # PR-2
```

**Expected file SHA-256 after exactly this edit:** `2c4acbcc0fc7bade265475abe1b5db9821bff1b7efd935fa20acd98b008f2494`. It was computed in memory and **not applied**. The wrapper refuses any other value.

**Even after the edit, a live run still needs all of:**
- the protocol block SHA to match;
- the census code SHA to match;
- `P4_PROBE_PR2=AUTHORIZED`, which only the wrapper sets.

## 5. Evidence wrapper (`p4/probe/run_live_probe.sh`; written, syntax-checked, NOT run)

**Preconditions (any failure is a STOP before any network request):**
- not root; `HOME=/home/manish_raj`;
- the RD interlock `P4_PROBE_RD_AUTH="PR-2 approved f8a7e398…"`;
- none of OUT, LOG, COPY, TAR or TAR.sha256 already exists;
- the archive directory exists;
- the baseline copy is present, read-only, and passes its manifest;
- hashes match: census `23e410ca…`, protocol document `a34a729d…`, probe after the edit `2c4acbcc…`;
- `identity` reports the block, the frozen SHA and `census_code_ok True`;
- a GitHub credential is present (never printed).

**Writes (all new, no overwrite):**

| Path | Created by |
|---|---|
| `~/p4census/probe1-<STAMP>/` | The probe (cache, result, meta, manifest) |
| `~/p4census/probe1-<STAMP>.log` | `tee` |
| `~/p4census/probe1-<STAMP>.preserved/` | `cp -a`; then both copies get `chmod -R a-w` |
| `/mnt/e/Projects/OpenSourceLab/p4census-archive/p4probe1-<STAMP>.tar.gz` + `.sha256` | `tar` |

**Never written:** run 1, its preserved copy (read-only, and re-verified at the end), the run-1 archive, or the repo.

**After the run:**
- Partial evidence is preserved even if the probe crashes. A manifest mismatch or a missing manifest is reported, not hidden.
- It prints `OUTCOME`, `M_v`, `M_v_lower_bound`, the decision, the request count and the reason.

## 6. What the live probe can and cannot establish

**Can establish (if EXACT):**
- **M_v**: the number of distinct, search-visible repos matching the frozen query at ≥ 1,000 stars during the window, excluding run 1's 999 by id;
- whether `total_count` agreed with enumeration band by band (C2);
- drift (C3);
- recall on the known baseline (C4);
- mover frequency (C5);
- the star histogram of the unseen repos.

**Cannot establish:**
- index completeness;
- the filter (U1–U4) pass rate, candidate yield, eligibility or admission survival of the new repos;
- any Stage-1 feasibility change;
- E, certified power, or Δ_true.

**Outcomes:**
- **Census v2 may be proposed only on EXACT with M_v ≥ 500.** It then needs a separately frozen protocol, SRC review and an RD freeze.
- **EXACT with M_v ≤ 62** → STOP-POLICY.
- **63–499** → RD judgment.
- **INCOMPLETE** → no proposal by default (G-6).
- **STOPPED** → fix the defect; a new PR-2 is needed.

## 7. Untouched artifacts

| Artifact | SHA-256 / status |
|---|---|
| Census code | `23e410ca…` |
| Census protocol document | `3831b084…` |
| Protocol v0.1 | `f2240b8f…` |
| Protocol v0.2 | `a0f4888c…` |
| Spec v0.9 | `9ef06926…` |
| Spec v0.10 | `da3086c7…` |
| Spec v0.11 | `551c3dc2…` |
| Run 1, its preserved copy, the run-1 archive | Not accessed |

No network access, no task selection, no model call, no build, no commit, no push.

## 8. RD decisions required

1. **Freeze decision** for block `f8a7e398…` in document `a34a729d…`, or request changes.
2. **G-6:** whether INCOMPLETE with M_v,LB ≥ 500 may support a proposal. Default: no.
3. If frozen: authorize the one-line edit (expected SHA `2c4acbcc…`), then separately authorize **one** live run through `run_live_probe.sh`.
4. **SRC (Gemini):** optional for this freeze; required at any census-v2 freeze.
