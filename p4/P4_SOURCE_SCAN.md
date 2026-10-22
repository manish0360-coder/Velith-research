# P4 source-feasibility scan: Python repair corpora for boundary B = 2026-08-01 (read-only)

**Date:** 2026-10-12. **Scope:** public metadata and documentation only. No dataset downloads, image builds, model calls, task runs, governance changes or commits.
**Relation to P4 v0.2:** U-3 (SWE-bench-Live Python) is **unchanged**. Any source named here is a **proposal** for the RD.

## 1. Headline

- **Verified eligible tasks under our rules (§3 of P4 v0.2): 0 in every source examined.**
- **Published tasks dated ≥ 2026-08-01 (any date field): 0** in every public Python source found.
- The issue, earliest-commit, merge and base-commit checks were **not** run, because no candidate passes even the coarse PR-date screen.

## 2. Sources examined: published metadata, not verified eligibility

| # | Source | Python? | Latest published task date (field) | Published post-B count | Images / tests | License / access | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **SWE-rebench leaderboard** (Nebius), monthly splits | Yes | HF splits through **2026_03** (110 tasks). July 2026 split on Harbor Hub (contents not inspected). Live leaderboard window **15/05/2026–01/07/2026** (111 problems, 65 repos). Last site news 2026-07-01. Field: PR `created_at`. | **0** | Pre-built Docker Hub images per task; F2P/P2P; `install_config`; SWE-bench-fork harness | CC-BY-4.0 dataset; per-repository licenses recorded | **Strongest dataset candidate for the future.** Ineligible today. |
| 2 | **SWE-bench-Live** Python (Microsoft) | Yes | Viewer: `created_at` **2024-01-01 → 2025-08-30** (3,688 rows; splits test, lite, verified, full). Monthly Python updates announced 2025-09-17; later news covers MultiLang and Windows only. | **0** | Per-instance images; F2P/P2P | MIT | Structurally ineligible (current U-3) |
| 3 | SWE-bench-Live MultiLang / Windows | **No Python** | Aug 2026 update (MultiLang 1,077 tasks; Windows 66) | n/a | Images | MIT | Out of scope (not Python) |
| 4 | SWE-rebench V2 | Mixed, 20 languages incl. Python | Viewer: `created_at` **2014-11-10 → 2025-10-31** (32,079 rows) | **0** | Pre-built images (≈ 26 TiB total) | CC-BY-4.0 | Ineligible. It is also a **training** corpus, so a contamination source by design. |
| 5 | SWE-rebench (v1 full) | Yes | 21.3k test + 6.54k filtered; last news 2025-08-05 | **0** | Images for about 7,500 tasks | CC-BY-4.0 | Ineligible |
| 6 | SWE-Bench Pro (Scale), incl. "V2" public split (2026-09-22) | Mixed | Public tasks drawn from older repository history; V2 creation dates **not published**. Held-out and commercial sets are private. | Unknown, likely 0 | Containers | Public split GPL repos; held-out not accessible | Not usable: public split exposed; held-out inaccessible |
| 7 | SWE-bench Verified | Yes | 2023 and earlier | 0 | Images | — | Contaminated (P3 F-2) |
| 8 | **Self-curated post-B corpus** using the open SWE-bench-Live curation pipeline + RepoLaunch (MIT) | Yes (we choose) | We set the window ≥ B | **Unknown; must be measured** | Built per repository by RepoLaunch (LLM-agentic setup; reported ≥ 98% build success under its 2026 strategy) | MIT tooling; per-repository licenses | The only route with **non-zero potential today**. Large engineering and reproducibility scope. |

## 3. Requirement and plausibility of a pool ≥ R + 52

**Requirement.** R (the Stage-1 reserve) comes from Stage 1's own power plan.
- Illustrative values (P4 v0.2 §4): **R ≈ 115–210**, so the **admitted** requirement is ≈ **167–262**.

**Expected monthly yield (assumptions, not measurements):**
- Curated tasks per month: SWE-rebench monthly splits 30–110 (2025-07 to 2026-03; mean about 55; the latest window about 70/month). SWE-bench-Live announced 50/month.
- **Issue-date survival:** our rule requires the *issue* also ≥ B, and the providers date only the PR. Many PRs fix older issues. Assumed 40–60%.
- **Admission survival** (gold Case A, budget, leakage, environment): 65–80%. P2 Phase A observed 13/20 = 65%.
- **Net admitted per month ≈ 55–70 × 0.4–0.6 × 0.65–0.8 ≈ 14–34.**

**Plausibility:**
- **Today (B → 2026-10-12, about 2.4 months, zero published): not plausible.**
- At 14–34 admitted per month, 167–262 admitted needs **about 5–19 months** of accumulated post-B tasks. That is mid-2027 at the earliest, under optimistic assumptions, and only if a provider keeps publishing Python tasks, or we self-curate at that rate.

## 4. Contamination and reproducibility notes

- **PR-date-only providers.** A post-B PR can fix a pre-B issue whose discussion contains the fix. Our issue, E1 and E2 checks are mandatory on top of any provider's date.
- **Monthly public releases.** Gold patches become public once released. That is harmless for this generator (cutoff June 2026), but it makes the corpus unusable for any later generator.
- **Pre-built images.** They may carry repository history beyond the base commit. That is irrelevant to Velith's single-shot proposer, which has no container access, but must be noted for any agentic arm.
- **Self-curation.**
  - RepoLaunch uses an LLM to build environments, which adds cost and nondeterminism.
  - Images must be built once, pinned by digest, and never rebuilt.
  - Curation choices become our responsibility and must be frozen before P4 selection.
- **Training corpora.** SWE-rebench V2 and v1 are published *for training*. Overlap with any evaluation set must be excluded by ID.

## 5. Ranked shortlist

1. **SWE-rebench monthly stream, splits 2026_08 onward.**
   - Python; SWE-bench-compatible schema; pre-built images; CC-BY-4.0; steady historical cadence.
   - **Gap:** no post-B split is published yet; continuation is not guaranteed.
2. **Self-curated post-B Python corpus** (SWE-bench-Live open pipeline + RepoLaunch).
   - The only non-zero path today.
   - **Cost:** a substantial new research-infrastructure milestone (curation, environment builds, pinning, validation), with LLM API cost and build nondeterminism.
3. **SWE-bench-Live Python (current U-3):** ineligible unless Python updates resume.

**Excluded:** SWE-rebench V2 and v1 (dates; training corpora), SWE-bench-Live MultiLang and Windows (not Python), SWE-Bench Pro (exposed or inaccessible), SWE-bench Verified (contaminated).

## 6. Evidence gaps

1. Contents and date range of the SWE-rebench **July 2026** Harbor split; whether **2026_08+** splits exist or are planned.
2. The real **issue-date survival** fraction for recent PRs (the 40–60% is an assumption).
3. The real **admission survival** for these images under our frozen gate (the 65–80% is an assumption).
4. Whether SWE-bench-Live Python updates have stopped or merely lag publication.
5. **R** itself: Stage 1's power plan is not written.

## 7. Recommendation

- **NO-GO** for P4 execution or FG-1 against any currently published source: the eligible count is 0.
- **GO (bounded, read-only)** for a further metadata inventory that closes gaps 1–3 without downloading full datasets:
  - (a) read the July 2026 SWE-rebench split card and any 2026_08+ announcements;
  - (b) a metadata-only GitHub API sample (about 100 recent merged Python PRs from SWE-rebench repositories, PR-dated ≥ B) to measure the issue-date survival fraction and the E1/E2 exclusion rate.

**Strategic observation for the RD** (not a recommendation to change anything): the eligible pool is governed by the **generator's cutoff**.
- A generator with an earlier documented cutoff would make already-published tasks eligible today.
- For example, Opus 4.8/4.7, documented cutoff January 2026, would make the SWE-rebench 2026_03 split onward eligible (B = 2026-03-01 with the same one-month margin).
- The trade-off is the generator's capability versus pool size. That is a U-1 decision, and it is not proposed here.

## Sources

- SWE-rebench leaderboard site: https://swe-rebench.com/
- SWE-rebench leaderboard dataset (HF card, splits, schema, license): https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard
- SWE-rebench July 2026 Harbor split: https://hub.harborframework.com/datasets/ibragim-badertdinov/swe-rebench-07-2026/latest
- SWE-rebench paper: https://arxiv.org/abs/2505.20411
- SWE-rebench V2 dataset: https://huggingface.co/datasets/nebius/SWE-rebench-V2 ; paper: https://arxiv.org/abs/2602.23866
- SWE-rebench v1 dataset: https://huggingface.co/datasets/nebius/SWE-rebench
- SWE-bench-Live dataset: https://huggingface.co/datasets/SWE-bench-Live/SWE-bench-Live ; repo and news: https://github.com/microsoft/SWE-bench-Live
- SWE-Bench Pro paper: https://arxiv.org/pdf/2509.16941 ; Scale V2 page: https://labs.scale.com/leaderboard/swe_bench_pro_public_v2
- Claude model cutoffs: https://platform.claude.com/docs/en/models/opus-5-5/overview ; https://support.claude.com/en/articles/8114494-how-up-to-date-is-claude-s-training-data
