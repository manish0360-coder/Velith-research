# P4 sizing probe: protocol (DRAFT v0.2, for RD review; supersedes draft v0.1, kept unchanged)

**Status:** DRAFT.
- **RD PR-0 decision:** conditional approval; this v0.2 incorporates the seven required corrections.
- **PR-1:** offline implementation and synthetic tests only.
- **No live GitHub request is authorized.** PR-2 needs a separate explicit approval after the protocol freeze.

**Previous draft:** `P4_SIZING_PROBE_PROTOCOL.md` v0.1, SHA `f2240b8f…`, block `4a246c00…` (unchanged).

**Frozen inputs (read only, never modified):**

| Input | Identity |
|---|---|
| Census protocol | SHA `a642efdb…` |
| Census code | `supply_census.py`, SHA `23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d` |
| Run 1 cache | Manifest `e6171986f102167419526aed9a3a3c868ea0f98c52c27c0a0267f10337a897fe` |
| Preserved copy | `/home/manish_raj/p4census/run1.preserved-20261016T063538Z` |
| Archive | `/mnt/e/Projects/OpenSourceLab/p4census-archive/p4census-run1-20261016T063538Z.tar.gz` |

## 0. Response to the RD review (v0.1 → v0.2)

| # | RD requirement | Resolution |
|---|---|---|
| 1 | Separate measurement from projection | The **primary result is only M_v** plus its completeness status (§3). Yield projections move to §6, are non-decisive, and label their assumptions. |
| 2 | Audit the 610 rule | **Not defensible, in either direction.** c_10 = 0.82 is the yield at ranks 901–1,000 (6,609–7,420 stars). The unseen pool has 1,000–6,608 stars, which lies outside the observed range. The decile trend falls (1.23 → 0.62/0.82) but is not monotone, so 0.82 is neither a validated upper nor lower bound. **Replaced (§5)** by (a) a **rigorous stop**, using only physical maxima (≤ 4 capped candidates and ≤ 1 candidate-bearing repo per repo), and (b) a **measured-count expansion threshold** in repositories that claims no yield. 0.62 is **not** used as a bound. |
| 3 | Explicit estimand | §3: the union over the enumeration window; search-visible repos; baseline excluded by **numeric id** recovered offline from the frozen cached search items (rename-proof); explicit rules for movers and leavers. |
| 4 | Criteria denominators | §4.8: every tolerance is defined with numerator, denominator and purpose. Baseline recall is the calibration check on a known population. Stable `total_count` is explicitly **not** treated as completeness. |
| 5 | API-limit audit | §4.3 proof of a disjoint, complete tiling (stars and created dates); re-enumeration on shortfall; boundary sweeps for star movers; any unresolved partition → **INCOMPLETE** with a lower bound only. |
| 6 | Governance | §7 gates: live mode is locked in code until PR-2 sets the frozen protocol SHA. |
| 7 | Evidence | v0.1 and spec v0.9 are kept unchanged; corrections go into new version files. All outputs go to new directories with no overwrite. |

## 1. Question

How many distinct repositories match the frozen census query, are visible to GitHub search during the probe window, and were **not** among the 999 searched in census run 1?
- That number is M_v.
- Nothing about eligibility, candidates, admission or Stage-1 feasibility is measured.

## 2. Facts and hypotheses (unchanged from v0.1, abbreviated)

**Verified** (RD-run offline report, 2026-10-16):
- T_p = 4,775 to 4,776; `incomplete_results` False on all 10 pages.
- Stars at rank 1,000: 6,609.
- 999 unique entries.
- Yield by decile: 1.23, 1.31, 1.16, 1.15, 1.12, 0.93, 0.88, 0.75, 0.62, 0.82.

**Hypotheses:** H1, `total_count` is exact; H2, it counts unique repos; H3, about 3,777 unseen repos exist. All are UNVERIFIED.

<!-- PROBE-PROTOCOL-BEGIN -->
## 3. Estimand (primary measurement)

**Window.** W = [t_start, t_end] is the interval between the first and last probe request.

**Query.** Q0 is the frozen census qualifier set:
`language:Python pushed:>=2026-08-01 archived:false fork:false`, with `stars:>=1000`.

**S_W** = the set of numeric repository `id`s returned **at least once** during W by any probe query.
- This is a union over the window, not an instantaneous snapshot.
- Repos that change bands or disappear mid-window are still counted if they were returned once.
- Repos that enter mid-window (crossing 1,000 stars, or a new push) are counted if returned.

**B0** = the baseline ids: the `id` field of the items in the 10 frozen cached search responses of run 1, read **offline** from the preserved copy (1,000 items; 999 unique expected).
- If any item lacks `id`, the probe **refuses to run**. Name matching cannot exclude renamed baseline repos.
- Ids survive renames, so a renamed baseline repo is excluded correctly.

**M_v = |S_W \ B0|.**

**Interpretation.**
- M_v counts **search-visible** repos. Repos the search index omits are unobservable, and equally invisible to any census v2 that uses the same search, so they are irrelevant to the decision M_v supports.
- Every id in S_W was actually returned, so M_v is always a valid **lower bound** for the union estimand.
- It is **exact** only if every completeness check in §4.8 passes.

## 4. Procedure

### 4.1 Queries

Only the stars qualifier, and in §4.3 step 4 a `created:` qualifier, are added to Q0's other qualifiers:

```
stars band [A,B]:   language:Python stars:A..B pushed:>=2026-08-01 archived:false fork:false
open band  [A,∞):   language:Python stars:>=A pushed:>=2026-08-01 archived:false fork:false
created sub-band:   <star qualifier for one star value> created:D1..D2   (days, inclusive)
```

- Endpoint: `GET /search/repositories?q=…&sort=stars&order=desc&per_page=P&page=k`.
- Every request goes through the **frozen `supply_census.Client`**, imported unchanged: retries on 403/429/502/503 with back-off, a rate-limit sleep when fewer than 50 requests remain, an atomic cache, and failure recording.
- The token is never printed or written.

### 4.2 Calls

| Call | Parameters |
|---|---|
| Size | page 1, P = 100. It also serves as enumeration page 1 |
| Page | page k ≥ 2, P = 100 |
| Count-only recheck | P = 1. A distinct URL, so it never hits the cache |

### 4.3 Partition: completeness and disjointness

Star counts are integers ≥ 1,000.

1. **Start** with [1000, ∞).
2. **Split rules** (≥ 900 results → split):
   - **Finite [A, B]** → [A, m] and [m+1, B], with m = ⌊(A+B)/2⌋. Disjoint, and their union is [A, B].
   - **Open [A, ∞)** → [A, 2A−1] and [2A, ∞). Disjoint, and their union is [A, ∞).
3. By induction, the final star bands tile [1000, ∞) exactly. This is checked arithmetically on the final list as invariant P1: sorted, contiguous, no overlap, starting at 1,000 and ending open.
4. **A one-star band [A, A] with T ≥ 900** is sub-partitioned by `created:` day intervals tiling [1970-01-01, 2100-12-31], with the same bisection on day ordinals.
   - **P2:** the created sub-bands tile the full day range.
   - Creation dates are immutable, so no repo can move between created sub-bands.
5. **A one-day created sub-band with T ≥ 900** is **UNENUMERABLE**, and the result is INCOMPLETE.
6. **Termination:** every split strictly shrinks a finite interval. The open band reaches a finite upper bound after at most log₂ of the maximum star count. **Recursion depth ≤ 40.** Exceeding it marks the band UNENUMERABLE.

### 4.4 Enumeration of a final band b (T_b < 900)

- **Pages:** 2 … ⌈T_b / 100⌉, so at most 9 pages and never near the 1,000-result ceiling. Paging stops early on a page with fewer than 100 items.
- **E_b** = distinct ids returned in band b.
- **Shortfall rule.** If d_b = |E_b − T_b| exceeds tol_b (§4.8), the band is **re-enumerated once in full**, through count-distinct URLs (P = 99, so not served by the cache). The ids are united.
  - If the shortfall persists, the band is **INCOMPLETE**.
  - Within-band order is by stars and can shift during paging. De-duplication by id removes double counts. Skipped items show up as a shortfall.

### 4.5 Boundary sweeps (star movers)

- **For each internal star boundary s** between adjacent final bands: enumerate the window [max(1000, s − w), s + w − 1], with w = max(5, ⌈0.02·s⌉).
  - Any id not already in S_W is added and counted as **recovered**.
  - A window is enumerated with the same §4.3/§4.4 rules, including splitting, the created-date fallback and re-enumeration.
  - Any unresolved sub-band makes the sweep **SWEEP-INCOMPLETE**, and the result is INCOMPLETE.
- **Created sub-band boundaries need no sweep**, because creation dates are immutable.
- **Residual risk (stated, not hidden):** a repo whose stars moved by more than w across a boundary, between its band's enumeration and its neighbour's, is undetected. The recovery count measures how often movers occur; see check C5.

### 4.6 Rechecks

- Count-only calls for Q0 at the start (T_start) and at the end (T_end).
- One count-only call per final band after enumeration (T_b^re).

### 4.7 Failures, limits, termination

- **HTTP 422** (query rejected): **STOP**. It indicates a protocol defect, and no result is reported.
- **Any other recorded failure** after the frozen client's retries makes the affected band **INCOMPLETE**.
- **`incomplete_results = true`** on any response makes the band **INCOMPLETE**. There is no silent retry.
- **Hard caps:** **200 search requests** and **4.5 h** wall clock. Reaching either stops the probe, and every unfinished band is **INCOMPLETE**.
- **Endpoints:** only `GET /search/repositories`. No GraphQL, PRs, compare, clones, builds or models.

### 4.8 Completeness checks (all must pass for the outcome EXACT)

| ID | Purpose | Numerator / denominator | Pass if |
|---|---|---|---|
| C0 | Partition validity | Invariants P1 and P2 | Both hold |
| C1 | Every band was enumerable | Final bands with T_b < 900, fully paged | All |
| C2 | No pagination loss within a band (enumeration agrees with the independent count) | d_b = \|E_b − T_b\|, where T_b is the page-1 `total_count` | d_b ≤ tol_b = max(3, ⌈0.01·T_b⌉) **for every band** |
| C3 | Population stable over W (the union approximates a snapshot) | Per band \|T_b^re − T_b\|; global \|T_end − T_start\| | ≤ max(3, ⌈0.02·T_b⌉) per band; ≤ ⌈0.02·T_start⌉ global |
| C4 | **Recall on a known population** (calibrates the whole pipeline) | missing = \|B0 \ S_W\|, over \|B0\| = 999 | missing ≤ 9 (≤ 0.9%). Every missing id is listed for the audit |
| C5 | Star movers are rare | recovered, over \|S_W\| | ≤ ⌈0.01·\|S_W\|⌉ |
| C6 | No unresolved partition | Failures, `incomplete_results`, UNENUMERABLE, SWEEP-INCOMPLETE, cap reached | None |

**Why these checks are sufficient, and their limits:**
- C2 compares two different mechanisms, the reported count and the actual enumeration, band by band. **A stable `total_count` alone proves nothing.**
- C4 tests the entire chain (partition, paging, de-duplication, id matching) against 999 repos known to match at T_SEL. Genuine leavers (deleted, archived, made private, language changed) are expected to be few within days, but their rate is UNVERIFIED. The 0.9% tolerance is a judgment.
- C4 covers mainly the high-star region, so C2 is what protects the dense low-star bands.
- C5 bounds drift-induced misses near boundaries. Nothing detects repos absent from the search index. That is acceptable, because M_v is defined as search-visible (§3).

### 4.9 Outcome classes

| Class | Condition | What is reported |
|---|---|---|
| **EXACT** | C0–C6 all pass | M_v, for the union estimand |
| **INCOMPLETE** | Any check fails, or a cap is reached | M_v,LB = \|S_W \ B0\| as a **lower bound only**, never presented as exact, plus every failing check |
| **STOPPED** | HTTP 422, or a protocol or baseline defect | Nothing |

### 4.10 Evidence

- **New directory:** `/home/manish_raj/p4census/probe1-<UTCSTAMP>/`. If it already exists, the probe refuses to run. It holds:
  - `cache/` (frozen client format);
  - `probe_result.json` (bands, counts, ids per band, checks, outcome);
  - `run_meta.json` (protocol block SHA, code SHAs, UTC start and end, request count, caps);
  - `MANIFEST.sha256`.
- **Then:** a read-only copy, and a `tar.gz` + `.sha256` in `/mnt/e/Projects/OpenSourceLab/p4census-archive/`, with no overwrite.
- **Never written:** run 1, its preserved copy, or its archive.

## 5. Decision rule (replaces the 610 rule; no yield claim)

**Materiality reference:** the §10 notion of +25% / +50% relative gain over run 1, i.e. 996 capped candidates, 320 candidate repos and 999 searched repos.

| Outcome | Condition | Consequence | Basis |
|---|---|---|---|
| **STOP-RIGOROUS** | EXACT and M_v ≤ 62 | Stop expanding the ≥ 1,000-star slice | Physical maxima: added capped ≤ 4·M_v ≤ 248 < 0.25·996, and added candidate repos ≤ M_v ≤ 62 < 0.25·320. Holds **for any yield** |
| **RD-JUDGMENT** | EXACT and 63 ≤ M_v ≤ 499 | No automatic proposal. RD decides, using §6 as context only | — |
| **ELIGIBLE-TO-PROPOSE census v2** | EXACT and M_v ≥ 500 | May propose a separately frozen census v2, with SRC review and an RD freeze. Nothing runs before that | A **measured-count** threshold: at least +50% more repos than run 1 examined. A judgment threshold on the measurement itself. **Not a yield bound** |
| **INCOMPLETE** | Any check fails | **No proposal by default.** The RD may decide whether a lower bound M_v,LB ≥ 500 suffices (G-6) | A lower bound can support "≥ threshold" but never "≤ threshold" |
| **STOPPED** | — | Fix the defect; a new PR-2 is needed | — |

The 500 threshold is numerically below v0.1's 610. It is not a relaxation of a validated bound, because 610 rested on an unvalidated yield. The real safeguard is that census v2 measures yield before any spending decision.

## 6. Projections (separate, non-decisive, assumption-labelled)

- **Formula:** ΔC_proj(c) = M_v × c, for c ∈ {0.82 (decile 10), 0.62 (decile 9), the decile range 0.62–1.31}.
- **Assumption:** unseen repos (1,000–6,608 stars) yield like the observed ranks. They lie **outside the observed star range**, so this is extrapolation, not a bound in either direction.
- **Context:** the probe's star histogram of the S_W \ B0 repos shows how far below the observed range they lie.
- These projections never enter §5.
<!-- PROBE-PROTOCOL-END -->

## 7. Gates (each separately authorized)

| Gate | Content | Status |
|---|---|---|
| PR-0 | RD review | Conditionally approved; this v0.2 addresses the conditions |
| PR-1 | Offline implementation `p4/probe/sizing_probe.py` plus synthetic tests (fake opener, no network). Live mode stays locked (`FROZEN_PROTOCOL_SHA = None`) | Authorized after these corrections (RD condition); results reported separately |
| PR-2 | RD freezes the marked block by SHA-256, sets the frozen SHA in code through a reviewed edit, and explicitly authorizes **one** live run (read-only GitHub search, ≤ 200 calls, ≤ 4.5 h) | **Not authorized** |
| PR-3 | Report, read-only audit, apply §5 | — |

## 8. Estimate (assumptions)

| Item | Estimate |
|---|---|
| Pool | ≈ 4,800 |
| Final bands | ≈ 8–12 |
| Paging | ≈ 55–65 calls |
| Sizing | ≈ 15–25 calls |
| Rechecks | ≈ 12–14 calls |
| Sweeps | ≈ 8–15 calls |
| Contingency re-enumeration | ≤ 30 calls |
| **Total** | **≈ 95–150** (cap 200) |
| Time | ≈ 1.8–3 h at the observed ≈ 65–70 s per search call |
| Money | 0 |
