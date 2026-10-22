# P4 build spike: specification (DRAFT v0.11, for RD review only; supersedes v0.10 and v0.9, both kept unchanged)

**Status:** DRAFT. **Nothing here is authorized to run.** SP-0 review is not SP-1 authorization.

## v0.11 change log (pre-freeze audit, 2026-10-16)

| # | Change | Evidence |
|---|---|---|
| L1 | §10.4 now references probe protocol **v0.3**. Wording: "rigorous stop" becomes a **policy stop** (an arithmetic bound under the cap-4 definition; 25% materiality is policy). ≥ 500 is a policy threshold for proposing census v2, **not** proof of task sufficiency. EXACT means protocol completeness, not index completeness. The rule values are unchanged. | `P4_SIZING_PROBE_PROTOCOL_v0.3.md` §00, §4.9, §5 |

## v0.10 change log (RD PR-0 review of the sizing probe, 2026-10-16)

| # | Change | Evidence |
|---|---|---|
| K1 | **§10.4: the census-v2 condition "M_v × c_10 ≥ 500" (the 610 rule) is withdrawn, as RD-directed.** c_10 is a decile-10 yield from outside the unseen star range, and is not a validated bound in either direction. It is replaced by the probe protocol v0.2 §5 rule: a rigorous stop at M_v ≤ 62 (physical maxima), and a measured-count threshold M_v ≥ 500 for eligibility to propose a census, with no yield claim. Yield projections are non-decisive. | `P4_SIZING_PROBE_PROTOCOL_v0.2.md` §0, §5, §6 |

## v0.9 change log (record of the §10 offline screen result; the rule is unchanged)

| # | Change | Evidence |
|---|---|---|
| J1 | §10.5 records the 2026-10-16 offline screen. Result **SCREEN-POSITIVE**, so the permitted next step is a sizing probe only (draft `p4/P4_SIZING_PROBE_PROTOCOL.md`). | RD-run report `p4c_report_20261016T063538Z.txt` |

## v0.8 change log (wider-census rule, SHA of v0.7 `9850b8f6…`)

| # | Change | Evidence |
|---|---|---|
| H1 | **New §10: wider-census decision rule, RD-locked 2026-10-16.** `total_count` is treated as GitHub-reported and UNVERIFIED. The offline screen can recommend at most a sizing probe, never a census. The projection is labelled a heuristic. The ΔC_lo decline-ratio heuristic is withdrawn. | §10 |

## v0.7 change log (census-universe check, SHA of v0.6 `c7d4c4e8…`)

| # | Change | Evidence |
|---|---|---|
| G1 | **Repository de-duplication made explicit**, and the consistency gate split into "as iterated" and "unique-repo" totals. | Code: `build_universe` appends search items with no de-duplication (line 336). `census()` walks every universe entry (lines 478–479) and **sums** the F5 counts (line 494), while `per_repo` is a dict (line 498). If a repo appeared twice across search pages (pagination drift), then N_cand would double-count it, while `distinct_repos` (320) and the cap-4 total (996) would not. Whether this happened in run 1 is **UNVERIFIED** until the offline check runs. Without this correction, v0.6's gate "Σc_r = 10,245" could STOP spuriously. |
| G2 | 10,245 relabelled "as reported (may include duplicate-walk counts)". | Same |

## v0.6 change log (decision-grade validation of v0.5, SHA `273bbe2e…`)

| # | Change | Evidence |
|---|---|---|
| F1 | §9.3 rebuilt to separate rigorous (NP-oracle), planning-grade and normal-approximation results. **No result is SM1-certified.** | Computed this pass |
| F2 | **Correction:** v0.5's g = 0.10 range (421–511) included a p0 = 0.20 case that SM8 never produces in P4's FEASIBLE band. It is now 468–571: SM8-by-k, plus ordering-statistic sensitivity. The required survival becomes 0.58–0.74. | §9.3 |
| F3 | **Infeasibility threshold made statistic-free:** g ≤ 0.064 at N = 1,180 for **any** level-0.01 test (NP oracle). | §9.3 (R) |
| F4 | Fréchet, ordering-statistic and pilot-k sensitivities quantified. The P4 base rate changes n_conf by ≤ 8% across FEASIBLE k. | §9.3 |
| F5 | **Supply bounds re-derived and qualified.** 1,180: components and protocol-relativity stated. 2,356 applies to the frozen 589-repo set only, not to future universes. Cap-1 independence ceiling (320) added. | §9.4 |
| F6 | **D-G recommendation changed:** no floor is ratified; the g_min(N) frontier is used instead (§7). | §9.3; register RD-5 ("no empirical estimate exists") |

## v0.5 change log (Stage-1 feasibility link + audit of v0.4, SHA `d95a75b9…`)

| # | Change | Evidence |
|---|---|---|
| E1 | **The Stage-1 requirement is restated from the frozen records** (§9). | D31 (`DECISIONS.md:680–767`); D31 R1 C10–C20 and N-1/N-2; SRC final statistical review SM1–SM11 (`reviews/src/SRC_2026-09-28_M9-ST1_final_statistical_review.txt`); RD register RD-3 to RD-6. |
| E2 | **v0.4 C9 / U-R corrected.** The hypothesis form is **not** open: D31 fixes it. The planning chain is already SRC-frozen (SM7–SM10): independence discordance, worst-case p0, exact power. The open inputs are RD-3 to RD-6 and the P4 p0 interval. | Same sources. v0.4's "260–290 / 910" figures used the D31 hypothesis, but a non-governing discordance (p01 = 0.05) and a normal approximation. |
| E3 | **Exact, SM-conformant n_conf table** (§9). The recorded R values are reproduced and classified by the hypothesis each one answers. | Computed this pass; method in §9. |
| E4 | **R_max is defined** as the SM-chain n_conf, plus the available-partition demand if that partition is drawn from this corpus (§2.5). | RD-3 consequence in the register: held-out share versus available tasks for A2. |
| E5 | **§3.5 wording corrected.** Only SUFFICIENT and INSUFFICIENT declarations equal the full-run code. INCONCLUSIVE-CURTAILED and INCONCLUSIVE-PARTIAL are not full-run codes. Forced decisions and partial stops are now separated explicitly. | v0.4 said "a declared code always equals the full-run code", which is false for INCONCLUSIVE. |
| E6 | **New invariant I11:** no spike artifact enters any Velith episode store or arm memory. | D31 R1 §5 D1. |
| E7 | **D31 compatibility of task-level spike exclusion stated** (§3.4). | D31 item 10; R1 §5 D2. |

**Inputs (read, unchanged):**
- census run 1: `p4/P4_SUPPLY_CENSUS.md` §2 (doc SHA `3831b084…`; protocol `a642efdb…`; universe `937414c5…`; cache manifest `e6171986…`);
- `p4/census/supply_census.py` (SHA `23e410ca…`);
- P4 v0.2: `p4/P4_SPEC.md` (SHA `81af9ad2…`);
- Velith `docs/DECISIONS.md`: D31.

**Not changed:** the census protocol, code and evidence; P1–P3 evidence; Velith governance; the `m0` image.

## v0.4 change log (comprehensive pre-implementation review of v0.3, SHA `17f32aa4…`)

Each change cites its evidence. Items marked **[RD]** need an RD decision (§7).

| # | Change | Evidence / reason |
|---|---|---|
| C1 | Each draw is executed **independently**. A duplicated task is re-executed, not counted k times. **[RD, U-S6]** | Restores an exact binomial without assuming deterministic outcomes (§3.3). Expected extra executions: 0.32–0.99 (derived, §8). |
| C2 | **Spike exclusion moved to task level.** F and R are drawn from all 320 repos. **[RD, U-S7]** | Repo-level exclusion of PPS-drawn repos removes 146–169 capacity in expectation, and biases F/R toward light repos. Task-level exclusion removes ≤ 50 and keeps F/R exchangeable with the sampled population (§2.2, §3.4). |
| C3 | **A6 moved from the primary to a secondary outcome.** Primary = A1–A5. | P4 §7 item 4 checks "files the interface reads", which depends on the interface (B-2). A6 checks patched files, which is a different check. Every primary step must be a *necessary* condition of final admission, so that an INSUFFICIENT result is decisive (§3.5). |
| C4 | **Outcome codes renamed** INFRA-SUFFICIENT / INFRA-INSUFFICIENT / INFRA-INCONCLUSIVE. Thresholds unchanged. | The spike measures funnel levels L0→L3, not final admission L4 (B-2, U-S4). "SUPPLY-SUFFICIENT" overclaimed. |
| C5 | **One forced-decision rule** for complete runs, futility curtailment, partial stops and unresolved infrastructure errors (§3.5). | Proved in §3.5: a decision is declared only when it equals the decision of the full 50-draw run. v0.3 treated partial stops as descriptive only, which was valid but needlessly weak. |
| C6 | **Export contract corrected:** it never calls `census()`, and uses a passive recording, read-only client. | Verified in code: `census()` overwrites `census_result.json`, `universe.json`, `census_summary.md` and `MANIFEST.sha256` (lines 473, 537–538, 453). Offline failures are recorded with different error text (line 229; census §2.4). v0.3's "same code path as `report`" would have rewritten evidence. |
| C7 | **The export records the task identity OIDs**: `baseRefOid`, `headRefOid`, merge-base SHA. | They are in cached responses (code lines 313–315, 431–436). Content-addressed registry: D31 item 10. |
| C8 | **Seed bytes and draw strings specified exactly.** The export and partition code must be committed **before** the export is generated (anti seed-grinding). | v0.3 left the byte encoding ambiguous. A changeable export format would let the seed be chosen. |
| C9 | **R_max default removed.** SP-2 needs an RD-recorded value. The mismatch between the R reference values and D31 is recorded. | D31 item 6 tests **H0: Δ20 ≤ δ** with an exact *unconditional* test. All R values in the record (spike, P4 §4, census `SCENARIOS`) test H0: Δ ≤ 0 at a true effect Δ = δ (§7, U-R). |
| C10 | **Draw weights tied to a recorded cap k_draw = 4** (P4 §7). If U-S2 sets a Stage-1 k ≠ 4, the estimand mismatch is stated. | Exact CP holds only for the estimand whose weights match the sampling weights (§3.3). |
| C11 | **Transfer to F and R analysed and quantified.** F adequacy is certified by P4 FG-5, not by the spike. | §3.4. |
| C12 | Corrections of detail. | §1 bound tightened from 36–225 to **50–225** repos with ≥ 4 candidates (uses the fact that no non-top-20 repo exceeds 117). E1–E5 assigned explicitly to A1/A2. INFRA_ERROR and retry rule defined. Compute cap left to the SP-4 authorization (not invented). §0 overclaim removed. Duplicate and repeat bounds tightened (§8). |

History: v0.1 (one task per repo) → v0.2 (capacity-weighted, without replacement) → v0.3 (with replacement, curtailment) → v0.4.

## 0. Purpose and what the spike can and cannot answer

**Program need.** Stage 1 (A0 vs A2, D31) needs:
- an uncontaminated, **admitted** pool for P4: 50 admitted, with P4-POOL-INSUFFICIENT below 40 (P4 §7);
- a Stage-1 reserve R (unratified).

**Funnel levels:**

| Level | Definition | Measured by |
|---|---|---|
| L0 | Raw census candidate (F0–F5, metadata only) | Census run 1: 10,245 (frozen) |
| L1 | Eligible: P4 §3 chronology + E1–E5 | Spike A1–A2 |
| L2 | Infrastructure-admissible: environment builds; FAIL_TO_PASS non-empty; gold Case A passes on the frozen gate | Spike A3–A5 |
| L3 | (= L2 in this spec.) Primary spike endpoint: survival L0 → L2 | Spike |
| L4 | **Admitted under P4/Stage-1 rules**: prompt budget, leakage audit, interface-dependent base-blob check (B-2), AI-authorship policy (U-S4), repository cap | **Not measured.** Requires B-2 and U-S4 |

**What the spike answers.** Capacity-weighted L0 → L2 survival over the frozen candidate population, with an exact interval.
- Because every primary check is a necessary condition of L4, **INFRA-INSUFFICIENT is a decisive negative** for supply.
- **INFRA-SUFFICIENT is necessary, not sufficient.**

It is the dominant cost and risk unknown (environment builds). It is **not** the only unknown before P4 can be frozen: B-1, B-2, B-3 and U-R remain.

## 1. What `N_cand_cap4_sensitivity = 996` means (verified from code)

- **Definition.** `supply_census.py` line 523: `sum(min(4, v) for v in per_repo.values())`.
  - `per_repo[repo]` is the deduplicated F5 count (line 498), set only for the **320** repos with F5 > 0.
- **What it is.** The largest number of census candidates selectable with at most 4 per repo: an **upper limit on capped L0 supply**, not eligible supply.
- **What it excludes:**
  - the 64 undetermined or truncated cases;
  - candidates hidden by the 5 page caps and the 29 failed calls;
  - zero-candidate repos.
- **Derived bound:** **50–225** repos have ≥ 4 candidates.
  - Constraints used: 320 repos; Σc = 10,245; Σmin(4, c) = 996; the top-20 counts (Σ 5,963, minimum 117); every other repo has c ≤ 117.
  - The exact distribution is **UNVERIFIED** until the export.

## 2. From census to partition

### 2.1 Offline candidate export (implemented at SP-1, run at SP-2)

**Verified facts:**
- `census_result.json` does not persist the candidate list. `cands` is built in `walk_repo` (line 441) and only aggregated (line 499).
- The cache (`<run>/cache/*.json`, keyed by SHA-256 of the request, line 221) holds every successful response.
- The 29 failed calls were never cached, by design (census §2.4).
- **Location:** the run directory is `~/p4census/run1` in the RD's WSL home (census §3). It is **outside the repository, not committed, and not visible to the CSE**. Its current integrity is **UNVERIFIED**.

**Contract:**
1. **Read-only source.** The input is a copy of `run1`.
   - The export never calls `census()` or `manifest()`, both of which write into the run directory.
   - It asserts `protocol_sha() == PROTOCOL_SHA256` and the SHA-256 of `supply_census.py` == `23e410ca…`.
   - It recomputes the cache manifest **in memory** with the byte format of line 449, and requires `e6171986…`.
2. **No duplicated logic.**
   - Candidate membership comes **only** from the unchanged `build_universe` + `walk_repo`, run with `Client(offline=True)`.
   - **(v0.7) Repos are de-duplicated by `full_name`, keeping the first search rank.** A repo listed twice never contributes its tasks twice.
   - A passive wrapper records the responses those functions request, so the OIDs are read without re-implementing any funnel rule.
3. **Schema.** One record per candidate, canonical JSON, sorted by (`repo`, `number`). Fields:
   - `repo`, `number`, `merged_month`;
   - `baseRefOid`, `headRefOid` (from the cached detail response);
   - `merge_base_sha` (from the cached compare response, `merge_base_commit.sha`).

   Header fields: the input SHAs, `c_r` per repo, and the failure count.
4. **Output** goes to a new directory: `p4/spike/export/`. Nothing in `run1` is written.

### 2.2 Units (C2; **U-S7**)

- **Spike (S): task level.**
  - The 50 draws are taken from all candidates (§2.3).
  - Drawn tasks enter the exclusion registry and are removed from F and R.
  - Their repositories stay in the F/R lottery.
- **F (P4 frame) and R (Stage-1 reserve): repository level.**
  - The 320 repos are split by lottery into F (60) and R (260).
  - No repo is shared between P4 and the Stage-1 reserve. That is stricter than D31 item 10, which requires a task-level registry.
- **Why the spike need not be repo-level:**
  - The spike makes no generator call, and its outcomes never enter P4 or Stage-1 analysis (D31 item 10: "inform design only").
  - Spike tasks are excluded, content-addressed.
- **Why repo-level spike exclusion (v0.3) is worse:**
  - PPS selects heavy repos, so excluding S repos removes **146–169** capacity in expectation, against **≤ 50** under task-level exclusion (derived, §8).
  - It reweights F and R toward light repos. q_F and q_R then differ systematically from q_w whenever survival correlates with repo size.

### 2.3 Seed and draw (exact; **U-S6**)

**Seed.**
```
seed = SHA-256( UTF-8("velith-p4-partition-v1|" + M + "|" + U + "|" + E) )
```
- M, U, E = lowercase hex SHA-256 of the cache manifest, the universe and the export.

**Uniform integer in [0, m) for label ℓ:**
- For j = 0, 1, …: h = int(SHA-256(UTF-8(seedhex + "|" + ℓ + "|" + j)), big-endian).
- Accept `h mod m` at the first j with h < ⌊2^256 / m⌋ · m.
- Labels: `draw|<i>|repo` and `draw|<i>|task`, with i = 1…50 in decimal.

**Draw i:**
- **(a) Repository.** Choose repo r with probability a_r / W.
  - a_r = min(k_draw, c_r), with **k_draw = 4** (P4 §7 cap; C10). W = Σ a_r (996 per census).
  - Use integer cumulative weights over repos sorted by UTF-8 bytes of `owner/name`.
- **(b) Task.** Choose uniformly among r's c_r candidates, sorted by PR number.

**Verified algebra.**
- P(t) = (a_r / W) · (1 / c_r) = w_t / W, with w_t = a_r / c_r.
- Σ_t P(t) = Σ_r c_r · a_r / (c_r · W) = 1.
- Rejection makes each integer exactly uniform, given that SHA-256 behaves as independent uniform outputs (a standard modelling assumption). The seed is fixed by frozen hashes before any outcome exists.

**Duplicates and repeats.** Sampling is **with replacement**:
- Duplicate tasks are possible: expected duplicate pairs **0.32–0.99** (derived).
- Repeated repos are possible: expected repeated-repo pairs **3.89–4.57** (derived).
- Every draw is its own execution (§3.1).
- The partition file records all 50 draws (i, repo, number, OIDs).
- The registry records each distinct task once.

### 2.4 F / R lottery (after U-S7)

1. Order all 320 repos by SHA-256(UTF-8(seedhex + "|repo|" + repo)), ascending.
2. The first 60 → **F**; the remaining 260 → **R**.
3. Remove the drawn spike tasks from F and R.

### 2.5 Capacities and the SP-2 freeze (deterministic, offline)

**Step 1. Consistency gate (any mismatch is a STOP).** The export must reproduce `census_result.json`:
- **(v0.7)** The replayed total *as the census iterated it* (duplicates walked again) = 10,245. Σc_r over **unique** repos is recorded separately; it is ≤ 10,245, with equality iff there are no duplicates. 320 unique repos with candidates; Σmin(4, c_r) over unique repos = 996;
- the top-20 list; the per-month counts (2,486 / 5,323 / 2,436);
- funnel F0–F5;
- failure count 29, with the persisted `first_20` tags in order. `census_result.json` keeps only the first 20 (line 527).

**Step 2. Capacities** (computed after removing the spike tasks):
- **C_F** = Σ_{r∈F} min(4, c'_r);
- **C_R(k)** = Σ_{r∈R} min(k, c'_r), reported for k ∈ {1, 2, 4, uncapped}, with k* = the U-S2 value.
- c'_r = c_r minus the distinct spike tasks in r.

**Step 3.** s_req = max(50 / C_F, R_max / C_R(k*)).
- **R_max must be an RD-recorded value (U-R). There is no default** (C9).
- **v0.5: R_max = n_conf + E.**
  - n_conf comes from the SRC-frozen chain SM7–SM10 (§9), with the RD's planning inputs.
  - E is the number of available-partition (A2 experience) tasks, if those are drawn from this corpus. E is OPEN: no value is recorded anywhere.
- If s_req > L(50; 50) = 0.9418, INFRA-SUFFICIENT is unreachable: **do not run** (step 4).

**Step 4.** x_min = the smallest x with L(x; 50) ≥ s_req, or ∞; x_ins = the largest x with U(x; 50) < s_req, or none (§3.5).
- If x_min = ∞, INFRA-SUFFICIENT is unreachable at n = 50: report to the RD and **do not run**.

**Step 5.** Write the partition file: inputs, draws, F, R, c_r, C_F, C_R(k), s_req, x_min, x_ins and the code SHAs. Hash it; it is **frozen before any spike execution**.

**Estimates, before the export** (assumption: capped weight proportional to repo count):

| Quantity | Value |
|---|---|
| C_F | ≈ 60/320 × 996 ≈ 187, so 50 / C_F ≈ 0.27 |
| C_R(4) | ≈ 260/320 × (946 to 996) ≈ 769–809, so 200 / C_R ≈ 0.25–0.26, *if* R_max were 200 |
| Exact bound | C_F + C_R(4) ∈ [946, 996], derived because the spike removes at most 50 capped units |

**Selection-policy note** (P4 §7: a frozen-order walk, cap ≤ 4, no backfill). The wording is ambiguous: the cap could apply to attempts or to admissions.
- With a random within-repo order, expected F yield is C_F · q_F if the cap applies to attempts, and ≥ C_F · q_F if it applies to admissions.
- **s_req is therefore never anti-conservative.**
- Assumption: P4's within-repo order is randomized by its lottery. That is a P4 clarification, not a spike blocker.

### 2.6 Invariants (tests at SP-1, re-checked at SP-2)

| ID | Invariant | Test |
|---|---|---|
| I1 | Deterministic, offline export | Two runs over the same cache give byte-identical output. A network opener that raises on any call is never invoked. |
| I2 | Census consistency | §2.5 step 1, on real data at SP-2. On synthetic caches, mismatches raise STOP. |
| I3 | Partition correctness | F ∩ R = ∅ and F ∪ R = all 320 repos. Spike tasks ∉ F ∪ R task lists. Every draw is a census candidate. |
| I4 | Reproducibility | Same M, U, E → identical partition SHA. Changing any one input changes the seed. |
| I5 | No reuse (D31 item 10) | Registry IDs = SHA-256 of canonical JSON {repo, number, baseRefOid, headRefOid}, covering every spike task and every F task. A planted conflict is refused by the reserve loader. |
| I6 | Frozen before use | The pipeline refuses to start unless the partition SHA matches and s_req, x_min and x_ins are present. |
| I7 | Draw law | On synthetic populations: χ² agreement with w_t / W over many seeds; rejection bound checked; duplicates recorded per draw; fixed seed → identical draws. |
| I8 | Read-only evidence | The cache manifest is unchanged before and after. No file in the run directory is created or modified. `census()` and `manifest()` are never called. |
| I9 | Anti-grinding | The export and partition code SHAs are committed and recorded **before** E is generated. A re-export with different code is a STOP. |
| I11 | Design-only (D31 R1 §5 D1) | No spike output (logs, patches, verdicts) is ever written to a Velith episode store, arm memory or evaluation sink. Spike paths sit outside every M3/M4 store root, and the guarded writer refuses them. |
| I10 | CP correctness | A stdlib bisection on exact binomial tails reproduces L(19; 50) = 0.2651, L(25) = 0.3762, U(25) = 0.6238, L(50) = 0.9418 and U(0) = 0.0582 to 4 decimal places. |

## 3. Spike method (pre-registered)

### 3.1 Draws and execution independence (C1)

- **n = 50 draws**, executed in order i = 1…50. Each draw is a separate execution, so a duplicated task runs again.
- **No redraws.** Failures are outcomes.
- **Independence rule.** Each execution starts from nothing:
  - its own clone and its own environment build;
  - no Docker layer cache, build artifacts or LLM context from any other execution, including the same task or the same repo.

### 3.2 Per-draw pipeline

The first failing step decides the outcome.

| Step | Check (necessary condition of L4, with source) | Tooling (authorized at SP-4) |
|---|---|---|
| A1 | Chronology, P4 §3: issue, PR, earliest commit, merge and base commit all ≥ B. E5 (an unretrievable timestamp fails) | GitHub metadata |
| A2 | E1–E4, P4 §3 | Clone of that repo |
| A3 | Executable environment at the base commit, P4 §7 items 1–2 | RepoLaunch. The LLM ≠ `claude-opus-5-5` (U-S3); back-ends UNVERIFIED |
| A4 | FAIL_TO_PASS / PASS_TO_PASS derived; FAIL_TO_PASS non-empty (precondition of Case A) | RepoLaunch or SWE-bench-Live harness |
| A5 | Gold Case A on the frozen gate (P1 `stage_x`, network none), P4 §7 item 3 | Frozen gate |
| A6 (secondary) | Base blob = working tree for the patched files | Frozen admission check |
| T (tag) | Likely AI-authored gold or issue | Metadata |

**Base commit and gold/test split: SP-3 definitions.** The export records both `baseRefOid` (SWE-bench convention) and `merge_base_sha` (the commit checked by census F5). SP-3 must freeze:
- which one is the base;
- the gold/test split, using the census `TEST_RE` classifier (line 41).

**INFRA_ERROR.** A failure not attributable to the task:
- GitHub API 5xx or timeouts;
- Docker daemon or disk errors;
- an LLM provider API error, rate limit or timeout.

RepoLaunch completing without a working environment is a **task failure**, not an INFRA_ERROR.
- **Retry:** up to 2 retries per step, for INFRA_ERROR only.
- A draw still failing is **UNRESOLVED (u)**. It is never imputed (§3.5).

### 3.3 Estimand and why Clopper–Pearson is exact

**Estimand:**
```
q_w = Σ_t (w_t / W) · μ_t
    = Σ_r a_r q_r / W
```
- The population is the 10,245 frozen census-run-1 candidates.
- μ_t = P(one independent execution of t passes A1–A5 under the frozen pipeline).
- q_r = mean of μ_t over r's candidates.
- C · q_w is the expected admitted count at L2 for a capped attempt set of the same composition.

**Why the CP interval is exact.**
- The draws D_i are i.i.d. with P(D_i = t) = w_t / W.
- Executions are independent given the draws, so P(draw i passes) = Σ_t (w_t / W) μ_t = q_w, independently across i.
- Hence **x ~ Binomial(50, q_w) exactly**, without assuming deterministic outcomes, and CP has coverage ≥ 90% two-sided, with each tail ≤ 5%.

**Why duplicates and repeats do not violate this:**
- Repeated *selection* of a task or repo is part of the i.i.d. design.
- Re-execution means a repeat is a new measurement of the per-execution success probability, not a copied one. So no measurement is counted twice as if it were independent evidence.
- Within-repo similarity is captured by μ_t and q_r, and by the with-replacement variance the binomial already reflects.

**Assumptions:**

| ID | Assumption | Status |
|---|---|---|
| S1 | The draw follows §2.3 exactly, with the seed frozen before outcomes | Enforced by I4, I6, I9 |
| S2 | Executions are independent (§3.1). There is no common-cause shock shared across draws, such as a PyPI outage | Partly controllable: INFRA_ERROR retries; shocks noted in the report |
| S3 | μ_t is stationary over the spike period | Assumption. Dependency drift over weeks is UNVERIFIED |
| S4 | The pipeline is frozen at SP-3 | Enforced by SHAs |

**Weights versus cap.** If U-S2 sets a Stage-1 cap k* ≠ 4, the R requirement needs q_w(k*), which this sample does not estimate exactly. Its use then rests on an extra assumption: q_r uncorrelated with c_r. This is the reason for recommending k* = 4 (§7).

**Levels.**
- [L, U] is the 90% two-sided interval.
- L is the one-sided 95% lower bound, and U the one-sided 95% upper bound.
- Expected admitted counts (C · q_w), and their lower confidence bound C · L, are **expectations**.
- Realized counts are random around them, and **no realized count is guaranteed before admission**.

### 3.4 Transfer from q_w to F and R (C11)

**Facts:**
- The CP interval covers q_w, over the whole frozen population.
- F and R are random repo subsets of that population, under U-S7.

So q_F and q_R are unbiased in expectation, but each realized subset deviates. The deviation is **not** in [L, U].

**Size of the deviation** (derived; normal approximation; worst case: q_r ∈ {0, 1} at q = 0.5, i.e. all-or-nothing repo buildability, with weight design effect ≤ 1.19 from §8):

| Set | Size | SD(q − q_w) |
|---|---|---|
| F | 60 of 320 repos | ≈ 0.064 |
| R | 260 of 320 repos | ≈ 0.015 |

**Consequences:**
- **R:** the spike's statement transfers well. The deviation is small compared with the CP half-width of about 0.12.
- **F:** the spike **does not certify** P4 supply.
  - If q_w ≈ s_req, then q_F < s_req is likely.
  - F adequacy is certified by the **existing P4 FG-5 rule**: ≥ 40 admitted, or P4-POOL-INSUFFICIENT.
  - The spike's s_req uses 50, giving a 20% planning buffer.
  - P4 FG-5 runs before any generation, so an F shortfall costs admission effort only, never validity.
- **D31 compatibility of task-level spike exclusion (U-S7 a).**
  - D31 item 10 and R1 §5 D2 require pilot tasks to be excluded from the confirmatory held-out population by a content-addressed registry. Task-level exclusion (I5) satisfies this literally.
  - The spike produces no A0 or A2 outcome, and its information is design-only (I11).
  - A spike task sharing a repo with a held-out task creates no dependence among held-out outcomes, so C17 (the task is the independent unit) is unaffected.
  - Within-repo correlation among the **held-out tasks themselves** is a separate matter: the cap, U-S2.
- **Stage-1 independence.** With within-repo clustering, D31 item 7's task-level uncertainty is anti-conservative if outcomes correlate within repos.
  - The cap k* bounds the cluster size; k* = 1 removes clustering.
  - C_R(1), C_R(2), C_R(4) and uncapped are reported at SP-2 for U-S2. The spike cannot measure generator-outcome correlation (it involves no generation).

### 3.5 Decision rule: forced-decision form (C4, C5)

**Notation:** p = passes, f = failures, u = unexecuted or UNRESOLVED draws, with p + f + u = 50. The full-run count x ∈ [p, p + u].

| Code | Condition (thresholds unchanged from v0.1) |
|---|---|
| **INFRA-SUFFICIENT** | L(p; 50) ≥ s_req, i.e. p ≥ x_min |
| **INFRA-INSUFFICIENT** | U(p + u; 50) < s_req, i.e. p + u ≤ x_ins |
| **INFRA-INCONCLUSIVE** | Otherwise. Qualified as *complete* (u = 0), *curtailed* or *partial*. No automatic extension |

**Proof (v0.5 wording, corrected).** All 50 draws are fixed by the seed, and every draw's outcome is a random variable on the same probability space, whether or not it is ever executed. Let x* be the full-run count.
- L(·; 50) and U(·; 50) are strictly increasing in x, and p ≤ x* ≤ p + u holds for **every** completion.
- If p ≥ x_min, then x* ≥ x_min, so the full run is SUFFICIENT.
- If p + u ≤ x_ins, then x* ≤ x_ins, so the full run is INSUFFICIENT.
- **Only these two declarations equal the full-run code.** Their validity uses no information about unexecuted outcomes; it holds for all of them. So it holds whatever the reason for stopping, including outcome-dependent stops.
- Error control follows by inclusion:
  - {declared SUFFICIENT} ⊆ {x* ≥ x_min}, so P(declared SUFFICIENT | q_w < s_req) ≤ 0.05;
  - {declared INSUFFICIENT} ⊆ {U(x*) < s_req}, so P(declared INSUFFICIENT | q_w ≥ s_req) ≤ 0.05.
- With u = 0 the rule reduces exactly to v0.1's rule.

**What is not a forced decision.**
- **INFRA-INCONCLUSIVE-CURTAILED:** futility stop, neither bound forced. The full run could still have been INSUFFICIENT or INCONCLUSIVE, so this code is **not** a full-run code.
- **INFRA-INCONCLUSIVE-PARTIAL:** a budget, compute, infrastructure or SHA stop with neither bound forced. Such stops reveal nothing about future outcomes.
  - No outcome is imputed and no completed-run code is claimed.
  - The interval on the executed draws is **descriptive only**: the stopping may depend on outcomes, and the executed count is not the pre-registered n.

**Confidence-level language.**
- The equal-tailed two-sided 90% CP interval [L, U] is exactly the pair of one-sided 95% bounds.
- Its coverage is ≥ 90% (conservative, because the binomial is discrete).
- The rule uses each bound one-sidedly: SUFFICIENT uses L (error ≤ 5%) and INSUFFICIENT uses U (error ≤ 5%). The two errors apply under disjoint truths, so neither exceeds 5%.

**Futility curtailment.** Stop once p + u < x_min, where u includes the draws not yet executed. INFRA-SUFFICIENT is then impossible. Report INSUFFICIENT if p + u ≤ x_ins; otherwise INCONCLUSIVE (curtailed).

**Operating characteristics at n = 50** (derived; exact binomial):

| s_req | x_min | x_ins | P(SUFF) at q_w = 0.4 / 0.5 / 0.6 |
|---|---|---|---|
| 0.25 | 19 | 7 | 0.66 / 0.97 / 1.00 |
| 0.27 | 20 | 7 | 0.55 / 0.94 / 1.00 |
| 0.31 | 22 | 9 | 0.33 / 0.84 / 0.99 |
| 0.35 | 24 | 11 | 0.16 / 0.66 / 0.97 |
| 0.52 | 33 | — | P(SUFF) at q_w = 0.6 / 0.7 / 0.8: 0.24 / 0.78 / 0.99 |
| 0.66 | 39 | — | P(SUFF) at q_w = 0.6 / 0.7 / 0.8: 0.01 / 0.14 / 0.71 |

The last two rows are the s_req range implied by gap 0.10 (§9).

- At q_w ≈ s_req + 0.1, an INCONCLUSIVE result is likely: the n = 50 power limit, stated and not changed.
- The v0.1 "≥ 31 failures" stop was invalid whenever s_req ≤ L(19) = 0.2651, and s_req can be as low as 50/240 = 0.2083.

**Interpretation:**
- **INFRA-SUFFICIENT** means only this: with one-sided 95% confidence, q_w ≥ s_req. The **expected** L2 yields of capped attempt sets of size C_F and C_R would meet their requirements.
  - It is not a guarantee of realized counts (§3.3).
  - It is not certification of F (§3.4).
  - It is not L4 feasibility (B-2, U-S4 can only remove tasks).
- **INFRA-INSUFFICIENT** is decisive for the self-curated supply at this n, cap and requirement, because L4 ⊆ L2.
  - This holds **provided** P4/Stage-1 admission uses the same frozen A1–A5 tooling.
  - A later, better build tool would void it, and that would be a new decision.
  - Fallbacks go to the RD.
- **Reported, descriptive only:**
  - C_F · L and C_R · L, labelled "lower confidence bound on expected admitted";
  - L1 survival;
  - per-step failures;
  - A6 and T rates;
  - flakiness: disagreements between executions of a duplicated task;
  - cost and time per execution.
- **Later L4 extension.** Once I-2 is ratified, the prompt-budget and leakage checks can be applied to the same 50 frozen draws. That gives an exact L4 interval with no new sampling, which requires retained records, and images for the interface base-blob check (U-S5).

## 4. Budget and stop rules

**Budget** (estimates or caps; actual costs are UNVERIFIED):
- **LLM (RepoLaunch):** hard cap $50.
- **Compute:** about 20–60 minutes per execution, about 17–50 hours in total (ESTIMATE). **A hard compute cap is set in the SP-4 authorization** (not set here).
- **Storage:** the P1 free-space gate. Images are pinned by digest and deleted unless U-S5 retains them.

**Stops** (each is reported; every stop is evaluated by §3.5, never by redraw):
1. Futility curtailment (§3.5).
2. The LLM or compute cap is reached.
3. Any write to frozen evidence, the `m0` image or Velith governance.
4. Any invocation of `claude-opus-5-5`: an immediate stop.
5. INFRA_ERROR left unresolved on ≥ 5 consecutive draws.
6. A partition or pipeline SHA mismatch (I6).

## 5. Evidence and review

- **Layout:**
  - `p4/spike/export/`;
  - `p4/spike/partition.json` + SHA;
  - `p4/spike/draw-NN/`: raw logs, build records, Case A evidence, tags, `MANIFEST.sha256`;
  - `SPIKE_REPORT.md`.
- **Review:** a read-only audit (P3 pattern); SRC review of the report before any P4 freeze.

## 6. Gates and prerequisites (each gate separately authorized)

| Gate | Content | Prerequisites |
|---|---|---|
| **SP-0** | RD review of v0.4 | — |
| *(v0.5)* | **Feasibility pre-check (v0.6):** the RD/SRC accepts that a Stage 1 detecting only g ≥ g_min(N_achievable) is worth running, *or* the supply ceiling is raised first (§9.4). Otherwise the spike is not run | D-G frontier decision; E; U-S2 |
| SP-1 | Implement `p4/spike/spike_partition.py` (export with recording client, seed, draw, F/R lottery, capacities, x_min/x_ins, stdlib CP) and `test_spike_partition.py` (I1–I10 on synthetic caches). No network, no real cache | **U-S6, U-S7** decided |
| SP-2 | Commit the SP-1 code (I9); run the export on a verified copy of `run1`; partition; freeze | **Cache preserved and its manifest verified** (RD action); **U-S2, U-R (R_max)** recorded |
| SP-3 | Implement A1–A5 + A6/T, with synthetic tests; freeze the base-commit and gold/test definitions | U-S3; U-S4 (tag semantics) |
| **SP-4** | **RD execution authorization**: clones, RepoLaunch, builds, gold runs, LLM spend, compute cap | U-S5 |
| SP-5 | Report, audit, decision | — |

## 7. Blockers and RD decisions (none resolved here)

| ID | Item | Needed by | Options and consequences |
|---|---|---|---|
| **U-S6** | Sampling design | SP-1 | **(a, recommended)** PPS with replacement, k_draw = 4, each draw executed independently, forced-decision rule: exact CP for q_w; about 1 extra execution expected. **(b)** As (a), but a duplicate is executed once and counted k times: exact only if outcomes are deterministic; otherwise variance inflation ≤ 0.50 / (50 q_w (1 − q_w)), i.e. about 4–6% for q_w ∈ [0.2, 0.5] (derived). **(c)** v0.1, one task per repo: estimates the repo-weighted mean, which the capacity rule does not use. |
| **U-S7** | Spike exclusion level | SP-1 | **(a, recommended)** Task level: capacity loss ≤ 50; F/R exchangeable with the population. **(b)** Repo level (v0.3): loss 146–169 in expectation; F/R tilted toward light repos. Neither option affects generator contamination (no generation). |
| U-S2 | Stage-1 cap k* | SP-2 | **k* = 4 (recommended):** one estimand serves both F and R; cluster size ≤ 4. **k* = 1:** no clustering, but C_R ≈ 260 attempts, and R needs an extra assumption (q_r ⟂ c_r). **Uncapped:** largest C_R, strongest clustering (task-level inference at risk). |
| **U-R** | R_max = SM-chain n_conf (+ E) (v0.5, corrected) | SP-2 | The hypothesis form is **frozen** (D31 item 6) and the planning chain is SRC-frozen (SM7–SM10). The open inputs are RD-4 (δ, after the P4 pilot), RD-5 (Δ_true), RD-6 (scenario; the SRC concurs with independence), RD-3 (N_avail), E, and the P4 p0 interval. **n_conf depends mainly on the gap Δ_true − δ** (§9). |
| **D-G (v0.6)** | **Planning floor on g: NOT recommended.** Use the g_min(N) frontier (§9.3) instead | Before SP-4 | **Floor 0.15:** n_conf 201–266 (independence), 423 (Fréchet). Feasible only if s ≳ 0.29 with no experience set from this corpus. But no record supports g ≥ 0.15, and if the true g is 0.10, power is about 0.40, risking the uninterpretable NO-GO that C20 exists to prevent. **Floor 0.10:** n_conf 468–571 (independence), 1,018 (Fréchet). Needs s ≥ 0.58–0.74 and no experience set from this corpus, so it is effectively infeasible here. **No floor (recommended):** feasibility is stated as 'this corpus detects only g ≥ g_min(N_achievable)', with no effect assumption. |
| U-S1 | The spike supersedes the 2-task compatibility check | P4 freeze | Partition design |
| U-S3 | RepoLaunch LLM back-end | SP-3 | Feasibility, cost |
| U-S4 | AI-authored gold/issue admission policy | L4; P4 | Tag only in the spike |
| U-S5 | Retain spike images | SP-4 | Enables the later L4 extension on the same draws (§3.5) |
| B-1 | P4 v0.2 U-3 still names SWE-bench-Live; adopting the self-curated corpus is not yet an RD decision | P4 freeze | The spike is a feasibility study for a proposed source |
| B-2 | I-2 Stage-1 input interface | L4; P4 | Spike limited to L0 → L2 |
| B-3 | Temperature amendment (D31 item 7) | P4/Stage-1 generation | None on the spike |

## 8. Evidence ledger

**Verified (file or code read this pass):**
- census run 1 figures (§2 of the census doc): 320 repos, 10,245 candidates, W = 996, top-20 counts summing to 5,963, per-month counts, 29 failures, 5 page caps;
- code lines 221, 229, 441, 449, 453, 473, 498–499, 523, 537–538;
- that `report` rewrites run-directory files;
- D31 items 6, 7, 9, 10;
- P4 §3, §4, §7;
- frozen SHAs: `supply_census.py` `23e410ca…`, census doc `3831b084…`, P4 `81af9ad2…`.

**Derived (computed this pass; reproducible arithmetic):**
- 50–225 repos with c ≥ 4;
- E[duplicate task pairs] = 1,225 · Σ_r(a_r² / c_r) / W² ∈ [0.32, 0.99] (v0.3's ≤ 1.23 was a looser valid bound);
- E[repeated-repo pairs] = 1,225 · Σa_r² / W² ∈ [3.89, 4.57];
- weight design effect 1.02–1.19;
- repo-level spike removal 146–169 (expected);
- CP values and the operating characteristics (§3.5);
- conditional exact sign-test R: 114 (δ 0.15) and 208 (δ 0.10);
- transfer SDs 0.064 / 0.015 (worst-case model);
- U-R normal-approximation illustrations.

Ranges come from continuous relaxation under the census constraints, so they are valid bounds.

**Assumptions:**
- S1–S4 (§3.3);
- the worst-case heterogeneity model (§3.4);
- P4's within-repo walk order is random (§2.5);
- capacity estimates proportional to repo count (§2.5).

**UNVERIFIED:**
- the c_r distribution (needs the export);
- the integrity and current location of `run1`;
- prowler-cloud/prowler's c_r: it is page-capped and not in the top 20, so if < 4 its weight is understated;
- RepoLaunch back-ends, cost and build success;
- the stationarity of μ_t;
- ~~the previously computed unconditional R values (105–115 / 190–200; not recomputed here)~~ **v0.5: reproduced** (§9);
- (v0.5) the sensitivity of n_conf to the still-open ordering statistic (N-1a). Here the Tango score statistic was used;
- (v0.5) the available-partition demand E.

**RD decisions:** §7.

## 9. Stage-1 requirement and corpus feasibility (v0.5)

### 9.1 Frozen requirement (verified from the records)

| Element | Frozen content | Source |
|---|---|---|
| Estimand | Δ20 = P(A2 pass at final checkpoint K) − P(A0 pass), paired over held-out tasks | D31 item 6; R1 C9 |
| Hypotheses | **H0: Δ20 ≤ δ vs H1: Δ20 > δ, δ > 0** (a strict positive margin) | D31 item 6; R1 C10 |
| Test | Exact unconditional paired test; Berger–Boos γ = 0.001; p = min(1, U_cert + η + γ); certified B&B supremum; shortcut p = 1 if Δ̂ ≤ δ | D31 item 6; SM1–SM5 |
| α, power | One-sided α = 0.01; power ≥ 0.80 at the maximum usable held-out n, else **VOID** (never NO-GO) | D31 item 9; C13, C20 |
| Unit | The held-out task (T = 0, N = 1, task-level uncertainty) | D31 item 7; C17 |
| Power planning | Exact trinomial power over the certified rejection region | SM7 |
| Discordance | Conditional independence: ψ = p0(1 − p2) + p2(1 − p0), with p2 = p0 + Δ_true | SM7 |
| Planning p0 | The power-minimizing p0 inside the pilot's two-sided 95% CP interval | SM8 |
| Chain | pilot → p0 CI → δ → Δ_true → discordance → n_conf → compare with N_avail → VOID if n_conf > N_avail | SM10 |
| **OPEN** | δ (RD-4, after the pilot), **Δ_true (RD-5; must exceed δ)**, governing scenario (RD-6), N_avail (RD-3), the ordering statistic (N-1a), the available-partition size E | Register; R1 §8 |

### 9.2 What each recorded R value answers (verified this pass)

| Recorded value | Hypothesis actually tested | D31-conformant? |
|---|---|---|
| 105–115 / 190–200 (census §1.6; spike v0.1–v0.4) | H0: Δ ≤ 0 (margin 0), McNemar-Z Suissa–Shuster, alternative p10 = 0.20 / 0.15, p01 = 0.05. **Reproduced here:** power first crosses 0.80 at n ≈ 105–110 and 190–200 | No: wrong null, non-SM discordance |
| 114 / 208 (v0.4) and 115–120 / 205–210 (P4 §4) | H0: Δ ≤ 0, exact *conditional* sign test, same alternatives | No: wrong null, conditional test |
| 260–290 / 910 (v0.4) | H0: Δ ≤ δ (correct), but normal approximation with fixed discordance p01 = 0.05 (positive correlation, not SM7). Exact check at δ = 0.10, Δ_true = 0.20, p01 = 0.05: 268 | Hypothesis yes; planning scenario no |

### 9.3 n_conf: rigorous bounds, planning-grade values, sensitivities (v0.6)

**Result classes:**
- **(R) Rigorous.** Exact trinomial sums. Neyman–Pearson (NP) oracle bound: for any null point on the boundary p10 = p01 + δ, the most powerful level-0.01 test against the alternative bounds the power of **every** level-0.01 test, including the frozen SM1–SM5 test. The minimum over the null points used, and over the p0 values used, is still a valid upper bound. No supremum approximation is involved.
- **(P) Planning-grade.** Tango or observed-difference ordering, Berger–Boos γ = 0.001, p = sup + γ + η, Δ̂ ≤ δ shortcut. The supremum is taken over a uniform grid: 300 vs 600 vs 1,000 points gave identical power to 4 decimal places. **Not SM1-certified.**
- **(N) Normal approximation.** Bracketing only.
- **Certified SM1 results: none.** The B&B procedure is not implemented. Every planning-grade n is therefore provisional until the certified test exists.

**Common settings:** independence (SM7, the SRC-concurred gate scenario), α = 0.01, power 0.80. p0 is the worst case over [0.05, 1 − Δ_true − 0.05], unless stated otherwise.

**(P) n_conf by gap g = Δ_true − δ** (Tango ordering):

| g | δ = 0.05 | δ = 0.10 | δ = 0.15 |
|---|---|---|---|
| 0.20 | 128 | 126 | 124 |
| 0.15 | 227 | 224 | 222 |
| 0.10 | 511 | 506 | 496 |
| 0.05 | — | > 1,957 (power 0.785 at 1,957) | — |

n_conf is nearly invariant to δ at fixed g (±3%).

**(P) Sensitivities at δ = 0.10:**

| Factor | g = 0.10 | g = 0.15 | Status |
|---|---|---|---|
| Ordering = observed difference (instead of Tango) | 571 | 266 | N-1a is OPEN (an SRC scientific parameter) |
| Discordance = Fréchet maximum (SM9, mandatory sensitivity) | 1,018 | 423 | RD-6 designates the gate scenario |
| Positive correlation, p01 = 0.05 | 268 | — | Sensitivity only |

**(P) Effect of the pilot base rate** (SM8: the power-minimizing p0 inside the 95% CP interval of a k/50 pilot):

| k / 50 | 5 | 10 | 15 | 20 | 25 | 30 | 34 | 40 |
|---|---|---|---|---|---|---|---|---|
| n_conf, g = 0.10 | 436 | 498 | 506 | 506 | 506 | 501 | 468 | 358 |
| n_conf, g = 0.15 | 201 | 224 | 225 | 225 | 225 | 218 | 201 | 143 |

- Across P4's FEASIBLE band (k = 10–34), the base rate moves n_conf by **≤ 8%**. A 50-task pilot does **not** materially reduce the reserve requirement.
- **Correction:** v0.5's "421 if p0 = 0.20" is not an SM8 outcome for any FEASIBLE k.
- Whether P4 is the SM8 pilot depends on SM11 configuration equivalence (B-2, B-3) and on the RD-0 BRP amendment, which awaits ratification. **UNVERIFIED.**

**(R/P) Minimum detectable gap g_min(N)** at worst-case p0, δ = 0.10, with N admitted independent held-out tasks:

| N | 79 | 100 | 118 | 158 | 197 | 237 | 276 | 320 | 395 | 500 | 552 | 650 | 789 | 1,180 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g_min (P, Tango) | 0.254 | 0.224 | 0.207 | 0.179 | 0.160 | 0.146 | 0.135 | 0.126 | 0.113 | 0.101 | 0.096 | 0.088 | 0.080 | 0.065 |
| NP oracle (R) | | | | | | | | 0.124 | | | | | | > 0.064 |

- The Tango ordering is within 0.002 of the oracle, so **no ordering statistic can materially lower n_conf**. N-1a only matters if a weaker ordering is chosen.
- **(R) At N = 1,180, the oracle power at p0 = 0.40 is 0.793 for g = 0.064 and 0.733 for g = 0.06.** So every level-0.01 test is underpowered at g ≤ 0.064.
- **(R) A design planned for g = 0.15 (n = 224)** has worst-case power 0.40 if the true gap is 0.10, 0.10 at 0.05, and 0.008 at 0. These are hypothetical power scenarios, not predictions of the real effect.
- **(N) Normal-approximation ratio:** α = 0.05 would need about 0.62 × n. α is frozen (D31 C13); this is reported only as the size of that governance lever.

**Inputs and who sets them:**

| Input | Status | Can be set now? |
|---|---|---|
| α, power, test family, SM chain | Frozen | — |
| Ordering statistic (N-1a) | OPEN | Yes (SRC). Little effect if Tango |
| Governing discordance scenario (RD-6) | OPEN | Yes (RD). Large effect: × 2 for Fréchet |
| E: source and size of the experience set | OPEN; **no value recorded anywhere** | Yes (RD / SRC design decision) |
| Cap / independence unit (U-S2) | OPEN | Yes (RD; SRC if uncapped) |
| p0 | Needs the SM8 pilot | No. Small effect (≤ 8%) |
| δ (RD-4) | Recorded after the pilot (D31 item 8) | No |
| Δ_true (RD-5) | **No empirical estimate exists; the pilot cannot estimate A2** (register RD-5) | Only as an assumption. **No record supports g ≥ 0.15** |

### 9.4 Supply versus requirement (census run 1)

**Supply categories (kept separate):**

| Category | Count | Status |
|---|---|---|
| Raw candidates (L0) | 10,245 | As reported. It may include duplicate-walk counts (v0.7 G1, UNVERIFIED). 996 and 320 are unaffected |
| Cap-adjusted (≤ 4 per repo) | 996 | Verified |
| Independent units if cap = 1 | 320 repos with ≥ 1 candidate | Verified |
| History-eligible (L1: chronology + E1–E5) | — | **Unmeasured** |
| Buildable and gold-test-validated (L2) | — | **Unmeasured** |
| Final independent admitted (L4) | 0 | Unmeasured; also needs B-2 and U-S4 |

**Cap-adjusted upper bounds (derived; valid only under the frozen census protocol: F0–F5 definitions and the U1–U4 universe query). Neither bound says anything about admission.**
- **Frozen window: ≤ 1,180.**
  - 996 counted.
  - + 4 × 29 failed calls. Each failure lies in one repo, a failed PR page stops that repo's walk, and no repo can exceed 4. This covers zero-candidate repos too.
  - + 64 undetermined cases, ≤ 1 each.
  - + 4 for the one page-capped repo with unknown c_r (prowler). The other four page-capped repos already have c ≥ 117.
  - The 29 failures were 3 compare and 26 PR-page/detail calls; there were 0 search failures and 0 null filter results.
  - The bound double-counts some cases (failed detail batches are also F3-undetermined), so it is conservative.
- **Frozen 589-repo set, any window: ≤ 2,356** (4 × 589).
  - A later census would re-select the universe, so this is not a bound on future universes.
  - Neither bound covers protocol exclusions such as repos outside the top 1,000 search results, which census §1.5 lists as under-counts.

**Achievable N** = s × C_R(k) − E_same. Here s is the unmeasured L0 → L4 survival and E_same is the part of the experience set drawn from this corpus. The table uses C_R(4) ≈ 789 (estimate) and hypothetical s values, **not predictions**:

| s (hypothetical) | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 |
|---|---|---|---|---|---|
| N if E_same = 0 → g_min | 158 → 0.18 | 237 → 0.15 | 395 → 0.11 | 552 → 0.10 | 789 → 0.08 |
| N if E_same = N (illustrative even split) → g_min | 79 → 0.25 | 118 → 0.21 | 197 → 0.16 | 276 → 0.14 | 395 → 0.11 |
| Cap = 1 (independent repos, 320 × s, E_same = 0) → g_min | 64 → > 0.25 | 96 → ≈ 0.23 | 160 → 0.18 | 224 → 0.15 | 320 → 0.126 |

**Verdict (v0.6).** Under the frozen D31/SM chain and the independence gate scenario:
- The census-run-1 corpus **cannot power Stage 1 for g ≤ 0.064 with any test**, at cap 4, even at 100% survival. This is rigorous.
- Under realistic, unmeasured survival and any experience set drawn from the same corpus, it can detect only g ≳ 0.11–0.21.
- If independence requires cap 1, then g ≳ 0.126 even at s = 1.
- Feasibility is therefore **UNRESOLVED**, and conditional on an effect assumption that **no existing evidence supports**.
- The binding constraint is the **number of independent repos**, not time or the base rate.
- The 0.40–0.80 survival assumption is not used.


## 10. Wider-census decision rule (RD-LOCKED 2026-10-16; changes only by a new recorded RD decision)

### 10.1 What `total_count` is and is not

**Verified from code:**
- The census never persists `total_count`. It reads only `items` and `incomplete_results` (lines 333–336).
- The offline checker reads `response.total_count` from the 10 cached search files, keyed exactly as the frozen client keys them (line 221). Page 1 is `70e2f5fb14ea759d…` and page 10 is `dcc2f11aa5e71fc4…`.

**Documented:** the search endpoint returns at most 1,000 *results*. That limits *retrievable items*. It does **not** establish what `total_count` counts.

**Not verified (CSE understanding):** `total_count` reports all matches, can exceed 1,000, and may be approximate.

**Treatment:** `total_count` is GitHub-reported. M_rep = max_p T_p − U is **UNVERIFIED**.
- If all T_p = 1,000, or T ≤ U, the count is **CAP-SUSPECT**: uninformative, and possibly capped.
- A value T > 1,000 falsifies "capped at 1,000" for that response, but it does not verify exactness or uniqueness.
- **M can only be verified by enumeration:** star-band sub-queries, each with T < 1,000, fully paged and de-duplicated by `full_name`, with the enumerated count compared to T per band. This requires network access, i.e. a separately authorized sizing probe.

### 10.2 Variables

| Symbol | Definition | Unit |
|---|---|---|
| T_p | `total_count` on search page p | repos (reported) |
| U | Unique `full_name` among the searched entries (≤ 1,000) | repos |
| M_rep | max_p T_p − U | repos (UNVERIFIED) |
| s_last | stargazers of the last searched entry | stars |
| n_d | Unique searched repos in rank decile d, by first rank | repos |
| c_d | Σ min(4, c_r) over kept repos in decile d, divided by n_d | capped candidates per searched repo |
| r_d | Kept repos in decile d with ≥ 1 candidate, divided by n_d | fraction |
| ΔC_hi | M_rep × c_10 | capped candidates |
| ρ | ΔC_hi / 996 | relative ceiling gain |

### 10.3 Status of the projection: HEURISTIC, not a statistical rule

ΔC_hi extrapolates beyond the observed star range with no sampling model: the unseen repos are not a sample of the observed deciles. It is **optimistic** for three reasons:
- it assumes no further yield decline below rank 1,000;
- it takes T at face value;
- candidates are not eligible tasks, and eligible tasks are not admitted tasks.

The thresholds express a relative ceiling gain. They map to the detectable gap (g_min ∝ N^−½, consistent with §9.3) only if survival and the experience-set fraction are equal for the new repos, which is an assumption.

### 10.4 Rule (offline screen → probe → census; each step separately authorized)

| Offline result | Outcome | Permitted next step |
|---|---|---|
| Integrity check fails | **STOP** | Nothing; report |
| CAP-SUSPECT, missing pages, or `incomplete_results` | **UNDETERMINED** | RD may authorize a sizing probe, or decide not to widen |
| ρ < 0.25 | **SCREEN-NEGATIVE** for the ≥ 1,000-star slice. Safe in this direction, because ΔC_hi is optimistic, provided the count is not CAP-SUSPECT | Widening only by lowering the star threshold, which the cache cannot inform: probe, or SRC pause |
| 0.25 ≤ ρ < 0.5 | **SCREEN-GREY** | RD judgment on a probe |
| ρ ≥ 0.5 | **SCREEN-POSITIVE** | Propose a sizing probe **only** |

- ~~Census v2 may be proposed only after the probe verifies M by enumeration (M_v), with M_v × c_10 ≥ 500 (heuristic).~~ **(v0.10, RD-directed; v0.11 wording)** Census v2 may be proposed only if the sizing probe (`P4_SIZING_PROBE_PROTOCOL_v0.3.md`) returns **EXACT with M_v ≥ 500**: a policy threshold on a measured count, not a yield bound and not proof of task sufficiency. EXACT means protocol completeness, not index completeness. **EXACT with M_v ≤ 62** is a **policy stop**: under the cap-4 definition, the unseen pool cannot add 25% to either baseline. Values in between go to RD judgment. **INCOMPLETE** gives no proposal by default. Census v2 requires its own frozen protocol, SRC review and an RD freeze.
- **SRC (Gemini) review is required** at the census-v2 protocol freeze, together with the §9 frontier questions: E source, cap/independence, and whether a large-gap Stage 1 is acceptable.
- Steep decline (c_10 < c_1 / 2) is reported, and the RD must weigh it.
- A screen result never authorizes the build spike.

### 10.5 Offline screen result (RD-run 2026-10-16; recorded, rule unchanged)

**Integrity (cache verified intact):**
- All three fingerprints equal `e6171986f102167419526aed9a3a3c868ea0f98c52c27c0a0267f10337a897fe`.
- 14,051 listed = 14,051 present, 0 tmp.
- The original still verifies.
- Copy: `/home/manish_raj/p4census/run1.preserved-20261016T063538Z`.
- Archive: `/mnt/e/Projects/OpenSourceLab/p4census-archive/p4census-run1-20261016T063538Z.tar.gz` (OK).

**Search metadata:**
- T_p = 4,775–4,776, with `incomplete_results` False and 100 items on every page. Stars at rank 1,000: 6,609.
- 999 unique entries; one duplicate (`s0md3v/Photon`, no candidates).
- M_reported_UNVERIFIED = 3,777. CAP_SUSPECT False.

**Replay** (matches the frozen report exactly):
- as-iterated total = Σ over unique repos = 10,245;
- 320 repos with candidates;
- capped total 996;
- 29 failures.

**G1 resolved:** no duplicate double-count.

**Yield and screen:**
- Decile yield c_d declines from 1.23 to 0.62–0.82.
- ΔC_hi = 3,097 and ρ = 3.11 (heuristic, optimistic).
- **SCREEN-POSITIVE**, which permits proposing a sizing probe only. **No census and no spike is authorized.**
