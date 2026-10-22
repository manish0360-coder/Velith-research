# P4 sizing probe: is the reported unseen search pool real? (DRAFT v0.1, for RD review only)

**Status:** DRAFT. **Nothing here is authorized to run.**
- It is the step the locked rule `P4_BUILD_SPIKE_SPEC.md` §10.4 permits after SCREEN-POSITIVE.
- It is not a census. It does not select tasks and does not authorize the build spike.

**Frozen inputs (read only, never modified):**

| Input | Identity |
|---|---|
| Census protocol | `P4_SUPPLY_CENSUS.md` §1, SHA `a642efdb…` |
| Census code | `p4/census/supply_census.py`, SHA `23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d` |
| Census run 1 cache | Manifest `e6171986f102167419526aed9a3a3c868ea0f98c52c27c0a0267f10337a897fe` (14,051 files) |
| Preserved copy | `/home/manish_raj/p4census/run1.preserved-20261016T063538Z` (read-only) |
| Archive | `/mnt/e/Projects/OpenSourceLab/p4census-archive/p4census-run1-20261016T063538Z.tar.gz` (checksum verified OK) |
| Offline report | `/home/manish_raj/p4census/p4c_report_20261016T063538Z.txt` |

## 1. Question

Does the frozen census query return a real pool of **unique** repositories beyond the 999 already searched?
- The probe only counts and enumerates repositories. It does not measure eligibility, candidates or admission.
- If the pool is real, it is large enough to justify *proposing* a separately frozen census v2 under the §10.4 rule.

## 2. Established facts vs hypotheses

**Verified** (offline report, 2026-10-16, and code):
- `total_count` was 4,775 on pages 1–5 and 4,776 on pages 6–10, fetched 2026-10-12, 07:56–08:06 UTC. `incomplete_results` was False on all 10 pages, and every page held 100 items.
- Because `total_count` exceeded 1,000, those responses were **not capped at 1,000**.
- Search pages were about 69 s apart. That is consistent with the frozen client's rule of sleeping until reset whenever `X-RateLimit-Remaining` < 50 (code lines 249–250), given the search endpoint's small per-minute quota.
- Stars of the 1,000th result: 6,609. So the unseen slice is the matching repos with 1,000 ≤ stars < about 6,609 as of T_SEL.
- 1,000 entries, 999 unique (one duplicate: `s0md3v/Photon`), 589 kept by the filters. Σc_r over unique repos = the as-iterated total = 10,245, so the duplicate added no candidates. 320 repos have candidates, the capped total is 996, and there were 29 offline failures.
- Capped yield per searched repo by rank decile: 1.23, 1.31, 1.16, 1.15, 1.12, 0.93, 0.88, 0.75, 0.62, 0.82. **It declines with rank.**

**Hypotheses (UNVERIFIED):**
- H1: `total_count` is the exact number of matching repositories.
- H2: the matches are unique repositories.
- H3: about 3,777 unseen matching repos existed at T_SEL.
- The filter-pass rate and candidate yield of the unseen repos are unknown, and likely lower given the observed decline.
- The heuristic ΔC_hi = 3,097 (ρ = 3.11) is therefore optimistic (§10.3).

**Drift:** the probe measures the pool **at probe time**, not at T_SEL.
- `pushed:>=2026-08-01` can only gain repos over time.
- Star counts move repos across band boundaries.
- Drift is measured (§4.7), not assumed away.

<!-- PROBE-PROTOCOL-BEGIN -->
## 3. Probe definition (to be frozen by SHA-256 of this block)

### 3.1 Query family

The probe uses the frozen census query with **only the stars qualifier replaced**:

```
Q[A,B] = "language:Python stars:A..B pushed:>=2026-08-01 archived:false fork:false"
Q[A,∞) = "language:Python stars:>=A pushed:>=2026-08-01 archived:false fork:false"
```

- Endpoint: `GET /search/repositories`, with `sort=stars`, `order=desc`, `per_page=100`.
- Requests go through the **frozen `supply_census.Client` unchanged**: same headers, retries, rate-limit sleep, atomic cache and failure recording. It is used through import only, so no census code is modified or duplicated.
- The token is read from `GITHUB_TOKEN` or `gh auth token`, and is never printed or written.

### 3.2 Deterministic band partition

1. **Start** with one band, [1000, ∞).
2. **Sizing call:** fetch page 1 of the band. Its `total_count` is T_b.
3. **If T_b ≥ 900, split the band.** 900 leaves a 10% margin under the 1,000-result ceiling for drift during paging.
   - Finite band [A, B]: split at mid = ⌊(A+B)/2⌋ into [A, mid] and [mid+1, B].
   - Open band [A, ∞): split into [A, 2A−1] and [2A, ∞).
   - Child bands are processed in ascending star order. Recursion depth is at most 20.
4. **One-star band [A, A] with T_b ≥ 900:** sub-partition by `created:` dates. This is a complete, disjoint partition, because every repo has exactly one creation date.
   - Bisect from 2008-01-01 to the probe date.
   - A one-day band that still has T_b ≥ 900 is **UNENUMERABLE**: the band is flagged and its count is treated as a lower bound.
5. **If T_b < 900:** enumerate pages 2…⌈T_b / 100⌉. Stop early on a page with fewer than 100 items.

### 3.3 Records and de-duplication

- **Recorded per item:** `id`, `full_name`, `stargazers_count`, `pushed_at`, `created_at`, `language`, `fork`, `archived`, plus the band and page.
- **De-duplication key:** repository `id`, which survives renames. Different `full_name`s for the same `id`, and the same `full_name` under different `id`s, are both reported.
- **E_b** = unique ids enumerated in band b. **S_now** = unique ids across all bands.

### 3.4 Comparison with the frozen universe

- U0 = the 999 unique `full_name`s in the frozen `universe.json`. The frozen universe stores names, not ids.
- Matching is by case-insensitive `full_name`.
- **M_v** = |S_now| − |S_now ∩ U0|: verified unseen repositories that match the frozen query at probe time.
- **U0_missing** = U0 names not found in S_now. This counts renames, star drops, archival and anything else that left the query.

### 3.5 Rechecks (drift and exactness)

- **Unpartitioned totals:** `per_page=1` calls for Q[1000,∞) at the start (T_now_start) and at the end (T_now_end). `per_page=1` gives a distinct URL, so the cache cannot serve a stale response.
- **Per-band recheck:** after enumeration, one `per_page=1` call per final band gives T_b_recheck.

### 3.6 Failures, incomplete results, limits

- **API failures:**
  - The frozen client retries 403/429/502/503 with back-off and records anything that still fails.
  - A band with any recorded failure is **INCOMPLETE**, and its E_b is a lower bound.
  - **HTTP 422** (query rejected) is an immediate **STOP**, because it means a protocol defect.
- **`incomplete_results = true`** on any page: the band is **INCOMPLETE**, with no silent retry. A re-probe is an RD decision.
- **Hard caps:**
  - **150 search requests in total** (sizing + paging + rechecks); the estimate is about 95.
  - **Wall clock 3.5 h**; the estimate is about 1.8 h at the observed 65–70 s per call.
  - Reaching either cap → **PROBE-INCOMPLETE**.
- **No other endpoint is called:** no GraphQL, PR, compare, clone, build or model calls.

### 3.7 Immutable evidence

- **New output directory:** `/home/manish_raj/p4census/probe1-<STAMP>/`. It must not exist beforehand. It holds:
  - `cache/`, in the frozen client format;
  - `MANIFEST.sha256`;
  - `probe_result.json`;
  - `probe_log.txt`;
  - `run_meta.json` (protocol SHA, code SHAs, start and end UTC, request count).
- **On completion:**
  - a read-only copy;
  - `tar.gz` + `.sha256` in `/mnt/e/Projects/OpenSourceLab/p4census-archive/`, with no overwrite.
- **Never written:** `run1`, its preserved copy, and the census archive.

### 3.8 Validity checks (all must pass for a VERIFIED outcome)

| ID | Check |
|---|---|
| V1 | Every final band was enumerated with T_b < 900, or flagged |
| V2 | **Exactness of `total_count`:** \|E_b − T_b\| ≤ max(3, 0.01·T_b) for ≥ 95% of final bands, and \|E_total − T_now_start\| ≤ max(10, 0.01·T_now_start) |
| V3 | **Drift:** \|T_b_recheck − T_b\| ≤ max(3, 0.02·T_b) per band, and \|T_now_end − T_now_start\| ≤ 0.02·T_now_start |
| V4 | **Universe continuity:** U0_missing ≤ 3% of 999 |
| V5 | No INCOMPLETE or UNENUMERABLE band, no 422, caps not reached |
<!-- PROBE-PROTOCOL-END -->

## 4. Decision rule (applies the locked §10.4 unchanged)

c_10 = 0.82 is the decile-10 capped yield per searched repo, from the frozen run 1.

| Probe outcome | Condition | Consequence |
|---|---|---|
| **PROBE-INVALID / INCOMPLETE** | Any of V1–V5 fails, or a cap is reached | No census-v2 proposal. The RD decides whether to re-probe or stop |
| **VERIFIED-SMALL** | V1–V5 pass and M_v × c_10 < 500, i.e. **M_v < 610** | **Stop expanding** the ≥ 1,000-star slice. Any widening would mean lowering the star threshold, which needs a new decision, or an SRC pause (§9 frontier) |
| **VERIFIED-LARGE** | V1–V5 pass and **M_v ≥ 610** | **May propose census v2:** a separately frozen protocol, an SRC (Gemini) review together with the §9 frontier questions, then an RD freeze. Nothing runs before that |

**Reported, never decisive:**
- The stricter sensitivity using the decline-aware c_min(deciles 6–10) = 0.62: M_v ≥ 807.
- The H1/H2 verdict from V2.

**What is not established even by VERIFIED-LARGE:**
- the filter-pass rate, candidate yield, eligibility and admission survival of the new repos (census v2, then the spike);
- any Stage-1 feasibility change. The §9 frontier would be recomputed only from measured census-v2 counts.

## 5. Gates (each separately authorized)

| Gate | Content |
|---|---|
| PR-0 | RD review of this draft. SRC review optional (it's engineering metadata, not statistics) |
| PR-1 | Implement `p4/probe/sizing_probe.py`: import the frozen Client, plus partition, enumerate, recheck and report. Synthetic tests with a fake opener cover splitting, the created-date fallback, de-duplication, 422 STOP, incomplete flagging, caps and evidence immutability. No network |
| PR-2 | RD freezes this protocol (SHA of the marked block) and authorizes execution. **This is the only network step:** GitHub search, read-only, ≤ 150 calls |
| PR-3 | Report + read-only audit; apply §4 |

## 6. Estimate (assumption-labelled)

| Item | Estimate | Basis |
|---|---|---|
| Current pool | ≈ 4,800 repos | Reported T at T_SEL plus drift |
| Final bands | ≈ 7–12 | — |
| Paging calls | ≈ 55–65 | — |
| Sizing calls | ≈ 15–25 | — |
| Recheck calls | ≈ 10–14 | — |
| **Total** | **≈ 80–105 calls** (cap 150) | — |
| Time | ≈ 1.5–2 h | Observed 69 s spacing in run 1 |
| Money | 0 | — |
