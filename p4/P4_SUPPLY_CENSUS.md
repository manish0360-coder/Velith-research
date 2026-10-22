# P4 supply census: post-cutoff Python issue→PR candidates (read-only)

**Status:**
- §1 (protocol) is **frozen**. Its SHA-256 is embedded in, and checked by, `p4/census/supply_census.py`.
- §2 (results) is **completed** (run 1, T_SEL 2026-10-12T07:55:04Z). Status: **PROVISIONAL, PROCEED-TO-SPIKE as a lower bound**.
- **Scope:** read-only GitHub metadata. No repository clones, image builds, model calls, task execution, governance edits, commits or pushes.

**Purpose.** Measure how many post-cutoff Python *candidate* tasks exist for the self-curation strategy, before any build spike.
- A candidate count is **not** a count of verified eligible tasks.

<!-- PROTOCOL-BEGIN -->
## 1. Frozen protocol (v1, 2026-10-12)

### 1.1 Time constants (unchanged P4 eligibility boundary)
- **B = 2026-08-01T00:00:00Z**. This is the P4 v0.2 cutoff (RD decision U-2), unchanged.
- **T_CUT = 2026-10-12T00:00:00Z**. This is the census window end. Only PRs with B ≤ `mergedAt` < T_CUT count, so the result does not depend on when the script runs.

### 1.2 Repository universe (frozen at run time, then recorded)
- **One GitHub repository search,** executed once at the run instant T_SEL (recorded):
  - query `language:Python stars:>=1000 pushed:>=2026-08-01 archived:false fork:false`;
  - `sort=stars`, `order=desc`, `per_page=100`, pages 1–10;
  - this gives at most 1,000 repositories (the Search API maximum).
- **Repository-level filters,** read from the default-branch HEAD at T_SEL (metadata only):
  - **U1:** the primary language is Python;
  - **U2:** a packaging file exists at the root: `pyproject.toml`, `setup.py` or `setup.cfg`;
  - **U3:** a test signal exists at the root: a directory `tests`, `test` or `testing`, or a file `pytest.ini`, `conftest.py` or `tox.ini`;
  - **U4:** the repository is not a fork and not archived.
- **Recording.** The universe list (search order, star count at T_SEL, filter verdicts) is written to the output and SHA-256-hashed. **The recorded list is the frozen universe.** Search ordering and star counts drift over time, so a later re-run may differ. The recorded list, not the query, is authoritative.

### 1.3 Candidate PR counting rules (funnel; each stage is counted)
For each universe repository, merged PRs are listed by `updatedAt` descending. Paging stops once a whole page has `updatedAt` < B (merged ≥ B implies updated ≥ B). There is a cap of 50 pages (5,000 PRs) per repository, and a cap that is hit is counted as truncation.

| Stage | Rule |
|---|---|
| F0 | Merged PRs with B ≤ `mergedAt` < T_CUT |
| F1 | + PR `createdAt` ≥ B; author is not a bot (login ending in `[bot]`) |
| F2 | + at least 1 closing-issue reference (`closingIssuesReferences`), and **every** referenced issue has `createdAt` ≥ B |
| F3 | + PR commit count ≤ 100, and the earliest commit, min(`authoredDate`, `committedDate`) over all commits, is ≥ B. More than 100 commits counts as UNDETERMINED and is excluded. |
| F4 | + changes at least 1 *test file* and at least 1 *non-test `.py` file*. A test file matches `(^|/)(tests?\|testing)/`, `(^|/)test_[^/]*\.py$`, `_test\.py$` or `(^|/)conftest\.py$`. If there are more than 100 files, classification uses the first 100 (flagged). |
| F5 | + merge-base date ≥ B. The merge base is `merge_base_commit` from REST `compare/{baseRefOid}...{headRefOid}`; its committer date must be ≥ B. Compare failures count as UNDETERMINED and are excluded. |

- **N_cand = |F5|.** This is a candidate count.
- **Additional report:** the number of distinct repositories, and the count under a ≤ 4-per-repository cap (the P4 selection cap), as a sensitivity figure only.

### 1.4 Not checked by the census (deferred to the FG-1 inventory and admission)
- E1–E3 (pre-existing fix, earlier origin, earlier patch-id), which need clones.
- Gold-patch Case A, environment buildability, FAIL_TO_PASS existence, prompt budget, leakage audit.
- So N_cand **over-counts** verified eligible tasks.

### 1.5 Known under-count sources (N_cand may miss real candidates)
- Repositories outside the top 1,000 by stars, or with fewer than 1,000 stars.
- Packaging or tests that are not at the root (monorepos, `src/` layouts with nested tests).
- PRs that fix issues without a closing reference.
- More than 100 commits (UNDETERMINED).
- The 5,000-PR paging cap.
- API failures.

### 1.6 Survival assumptions and statistical scenarios (labelled; not ratified)
- **Survival from candidate to admitted:** a range of **0.40–0.80 (ASSUMPTION).** The only observed reference is P2 Phase A, 13/20 = 0.65.
- **Stage-1 reserve R:** a CSE computation using an exact unconditional (Suissa–Shuster) paired test with McNemar's Z, one-sided α = 0.01, power ≥ 0.80. The nuisance parameter is maximised over a 120-point grid; no Berger–Boos adjustment. **Not ratified.**
  - **Scenario δ = 0.15** (p01 = 0.20, p10 = 0.05): R ≈ 105–115, so the requirement is R + 52 ≈ **157–167**.
  - **Scenario δ = 0.10** (p01 = 0.15, p10 = 0.05): R ≈ 190–200, so the requirement is R + 52 ≈ **242–252**.

### 1.7 Pre-declared decision class (computed mechanically from N_cand)
Let REQ_MIN = 157 and REQ_MAX = 252 (the extremes of §1.6).

| Class | Rule |
|---|---|
| **PROCEED-TO-SPIKE** | N_cand × 0.40 ≥ REQ_MAX, i.e. N_cand ≥ 630 |
| **WINDOW-INFEASIBLE** | N_cand × 0.80 < REQ_MIN, i.e. N_cand ≤ 196 |
| **SPIKE-DECIDES** | otherwise (197 ≤ N_cand ≤ 629) |

**Scenario-specific lines are also reported.** For each δ, the class is computed with REQ = that scenario's upper value, as in §1.6.

The class informs the RD. It authorizes nothing: no spike, no admission and no task selection.

### 1.8 Evidence and reproducibility
- Every API response is cached verbatim under the output directory and listed in a SHA-256 manifest.
- A re-run with the same output directory re-analyses the cache without calling the network.
- Tokens are read from `GITHUB_TOKEN` or `gh auth token`. They are never written or printed.
<!-- PROTOCOL-END -->

## 2. Results (run 1)

**Provenance:**
- Run by the RD in WSL; `gh` account `manish0360-coder`, token not recorded.
- T_SEL = **2026-10-12T07:55:04Z**. Protocol SHA-256 `a642efdb…98e89f` (matches §1).
- Tool: `p4/census/supply_census.py` `23e410ca…`. Output: `~/p4census/run1/`.
- Universe SHA-256 `937414c5e917ad6a…`; cache manifest SHA-256 `e6171986f102167…`.
- The offline `report` reproduced the `run` result exactly: same funnel, N_cand, distributions and manifest SHA.

### 2.1 Status and decision class

| | Value |
|---|---|
| **Status** | **PROVISIONAL** (`complete_data = false`: 29 API failures and 5 page-cap-truncated repositories) |
| **Overall class** | **PROCEED-TO-SPIKE, as a lower bound.** The class is the same at the lower bound (10,245) and the upper bound (10,309). |
| δ = 0.15 (R 105–115, **not ratified**) | PROVISIONAL, PROCEED-TO-SPIKE (lower bound) |
| δ = 0.10 (R 190–200, **not ratified**) | PROVISIONAL, PROCEED-TO-SPIKE (lower bound) |
| Projected admitted, at the 0.40–0.80 **assumption** | 4,098–8,196 (raw); **398–797 under the ≤ 4-per-repository cap** (§2.3) |

**Why PROVISIONAL can't become FINAL here.**
- A FINAL verdict needs complete data. The 5 page-cap truncations are a frozen protocol limit (§1.3), so this run can never be FINAL, even if the 29 failed calls were retried.
- Only PROCEED-TO-SPIKE is admissible from incomplete data, and only as a lower bound (§1.7, plus the RD clarification of 2026-10-12).
- Every counted candidate is deduplicated (`duplicates_skipped = 0`) and positively supported by recorded responses.

### 2.2 Universe and funnel

- **Universe:** 1,000 repositories searched; **589** kept after U1–U4; 0 null filter results. **320** repositories have at least one candidate.

| Stage | Count | Survival from previous |
|---|---|---|
| F0 merged in [B, T_CUT) | 104,937 | — |
| F1 created ≥ B, non-bot | 98,927 | 94.3% |
| F2 all closing issues opened ≥ B | 14,540 | **14.7%** |
| F3 earliest commit ≥ B | 14,453 | 99.4% |
| F4 test + non-test `.py` changed | 10,291 | 71.2% |
| **F5 merge base ≥ B → N_cand** | **10,245** | 99.6% |

**Undetermined or truncated cases, all added to the upper bound:**
- F2 undetermined: 6
- F3 undetermined: 35
- F4 truncated-excluded: 20 (of 29 truncated file lists)
- F5 undetermined: 3

That gives **N_cand_upper_bound = 10,309**.

**Per month (merged):** 2026-08: 2,486; 2026-09: 5,323; 2026-10 (1–11): 2,436, which is roughly 6,900 per month at the October pace.

**Concentration:**
- The top repository accounts for 13.7% of N_cand (NousResearch/hermes-agent, 1,408).
- The top 5 account for 29.8%, and the top 20 for 58.2% (5,963).
- Top 20 repositories:
  - hermes-agent 1,408; kornia 571; omnigent 438; pr-agent 333;
  - home-assistant/core 308; unsloth 298; pydantic-ai 264; repowise 261;
  - Soup 219; litellm 216; opensre 211; semantica 201; headroom 194;
  - vllm-omni 188; vllm 181; agentscope 153; VoiceStudio 145;
  - fastmcp 140; docling 117; posthog 117.

**Page-cap-truncated repositories** (their counts are lower bounds): NousResearch/hermes-agent, home-assistant/core, BerriAI/litellm, PostHog/posthog, prowler-cloud/prowler.

### 2.3 `N_cand_cap4_sensitivity = 996`: definition and interpretation

**Code:** `supply_census.py` line 523, `sum(min(4, v) for v in per_repo.values())`.
- `per_repo` holds the deduplicated F5 count for each of the **320** repositories with at least one candidate.
- So the figure is the **largest number of candidates selectable if at most 4 are taken per repository**. That's the P4 selection cap (§1.3: "sensitivity only").
- With 320 repositories the maximum would be 1,280. 996 means a substantial share of repositories have only 1–3 candidates.

**What it does not indicate:** overcounting. It is computed from the same deduplicated, positively supported N_cand. It is a lower-bound figure; the page-capped repositories add nothing extra, because each is already at ≥ 4.

**What it does indicate:** **concentration.** About 90% of N_cand sits in repositories above the cap. The *usable* pool under a per-repository cap is about 1,000, not about 10,000.

**Decision check:** the decision class is unchanged under the cap. 996 × 0.40 = 398 ≥ 252 (REQ_MAX), so PROCEED-TO-SPIKE holds even in the capped interpretation.

**Interpretation risk to carry forward** (not a census defect):
- The heaviest repositories are AI-agent or AI-tooling projects with very high PR rates (hermes-agent, omnigent, pr-agent, repowise).
- Their PRs and gold patches may be partly **AI-generated**, possibly by models of the generator family under test. Their issues may be auto-generated.
- The census cannot detect either. Both affect task quality and representativeness, and admission must consider them.

### 2.4 Why the `run` output shows HTTP 500/504 while `report` shows "not in cache (offline)"

**By design (fix 6 / failure tests), failed responses are never cached.**
- During `run`, the 29 calls failed after retries, and were recorded with their HTTP codes:
  - 3 × HTTP 500 on `compare`;
  - the rest HTTP 504, on `prs` pages and `detail` batches.
- The offline `report` re-walks the cache, finds those 29 requests missing, and records each as `not in cache (offline)`.

**Effects:**
- **Candidate count:** none. Both outputs give N_cand = 10,245 and the identical funnel. The failed calls contributed nothing to either count.
- **Failure record:** the same 29 failures, by tag and in the same order. Only the *error type* is lost offline.
  - The original HTTP codes survive only in the `run` console output.
  - The RD's saved WSL transcript ("Pasted text(20261012-141010).txt") is the record of them, and should be kept with the run outputs.
- **Reproducibility:** the result is fully reproducible offline from the cache (manifest `e6171986…`).
- **Retrying:** re-running `run` would retry only the 29 uncached calls. That could raise N_cand slightly, but it **cannot change the class**, which is already PROCEED-TO-SPIKE at the lower bound.

### 2.5 What is supported, what remains provisional, what is not established

**Supported by the lower bound:**
- Post-cutoff *candidate* supply is **not** the bottleneck for B = 2026-08-01 with self-curation: 10,245 raw, or about 996 under a ≤ 4-per-repository cap.
- Both figures exceed the unratified requirement range (157–252) under both δ scenarios and the 0.40–0.80 survival assumption.
- The window-infeasibility concern (B-1) is resolved **at the candidate level**.

**Provisional:**
- The status itself: FINAL is unattainable under the protocol, because of the page caps.
- The **survival rate 0.40–0.80** is an **assumption, not measured**.
- **R** is not ratified.
- Exact counts for the 5 capped and 29 failed repositories or pages.

**Not established by the census:**
- **Eligibility** under P4 v0.2 §3: E1–E3 (pre-existing fix, earlier origin, earlier patch-id) need clones and were not checked.
- **Buildability**, gold-patch Case A, FAIL_TO_PASS existence and test validity.
- The prompt budget and leakage audit under the (still unratified) I-2 interface.
- Problem-statement quality.
- **AI-generated gold patches or issues** (§2.3).
- Representativeness: there is a bias toward high-star repositories and agent tooling.
- The true SWE-bench-style base commit: F5 uses the `compare` merge base as an approximation.
- **No task is selected, admitted or eligible** as a result of this census.

## 3. How to run (RD, in WSL)

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research
gh auth status            # or: export GITHUB_TOKEN=... (read-only public scope is enough)
python3 -B p4/census/supply_census.py run --out ~/p4census/run1
python3 -B p4/census/supply_census.py report --out ~/p4census/run1
```

- **`run`:**
  - verifies the protocol SHA-256;
  - builds and records the universe;
  - walks the funnel;
  - caches every response. It is resumable: Ctrl+C, then re-run the same command.
- **`report`:** re-analyses the cache offline and prints the result JSON, which includes the funnel, per-repository and per-month distributions, failures, truncations, the decision class, the universe SHA and the manifest SHA.
- **Re-analysis by anyone:** run `report` on a copy of the output directory.
