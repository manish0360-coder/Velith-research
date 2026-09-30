# CI run #113 (Velith `5452efc`): GEE `SINGULAR_ROBUST_COVARIANCE`. Read-only diagnosis

## Facts

**GitHub CI:** 5 tests fail. All of them get `GeeFailure(SINGULAR_ROBUST_COVARIANCE)` from `fit_gee(..., A1_VS_A0, checkpoint_count=3)` on the unit-test fixture `_a1_vs_a0()` (24 tasks, K = 3).

**Local:** the same commit, in the local `velith-verifier:m0` image, passes (741 tests).

**The frozen rule** (`src/velith/analysis/gee.py:240-247`, `classify_failure`) is:
- non-finite → failure;
- negative diagonal → failure;
- otherwise `np.linalg.cholesky(cov_robust)`, where a `LinAlgError` means SINGULAR.

It is deliberately parameter-free: no tolerance.

## Experiment (CSE sandbox, same physical CPU as the host: Ryzen 5 5500U)

**Environment:** statsmodels 0.15.0 (the pinned version), numpy 2.2.6 and scipy 1.15.3. These are not the pinned 2.5.3 / 1.18.1, because the sandbox has only Python 3.10. OpenBLAS 0.3.29 with DYNAMIC_ARCH.

**Method:** the fixture is rebuilt exactly as in the tests. Only the OpenBLAS CPU kernel is changed, via `OPENBLAS_CORETYPE`.

| Kernel | min eigenvalue of `cov_robust` | Cholesky | `fit_gee` |
|---|---|---|---|
| auto (Zen) / Haswell / Zen | +1.53e-16 | OK | GeeFit |
| Nehalem | +9.71e-17 | OK | GeeFit |
| Sandybridge | −5.55e-17 | FAIL | **SINGULAR_ROBUST_COVARIANCE** |
| Prescott | −5.55e-17 | FAIL | **SINGULAR_ROBUST_COVARIANCE** |

In every run:
- the other eigenvalues are 0.140625 and 0.444444, so the ratio of smallest to largest is about 3e-16, i.e. machine epsilon;
- params = (−1.0986, 0.0, 1.7918);
- converged = True;
- the design matrix has rank 3 of 3.

## Conclusion

**The fixture's robust covariance is singular to machine precision.** Its true smallest eigenvalue is 0. That is a property of the synthetic data: the checkpoint effect is exactly 0 by construction.

**Whether Cholesky passes therefore depends only on the sign of rounding noise.** That sign changes with the BLAS/SIMD kernel, which is selected at runtime from the CPU. The pinned image does not fix the CPU, so it is not a complete reproducibility boundary for this rule.

**Classification** (by the question's labels a–d):
- It is not (a) dependency drift. The flip happens with identical software.
- It is (b) platform/BLAS numerical behavior.
- It exposes (d) a **test-oracle defect**: five frozen tests assert `GeeFit` on a mathematically singular case.
- The production rule behaves as specified. On a singular matrix, SINGULAR is the correct verdict.

**Scientific implication (RD/SRC):** near exact singularity, the frozen parameter-free rule is not cross-machine deterministic. This is concrete counter-evidence to the D27 cross-machine determinism acceptance requirement, which has not been demonstrated yet.

**Gaps:**
- I did not observe which kernel GitHub's runner used (CPU detection at runtime).
- The exact-pin confirmation (numpy 2.5.3 / scipy 1.18.1) is still pending. See the next action.

## Next action (read-only, local image, no pull, no repository change)

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith && docker compose run --rm -T --pull never -e OPENBLAS_CORETYPE=Prescott verifier sh -c 'python -c "import numpy,scipy,statsmodels;print(numpy.__version__,scipy.__version__,statsmodels.__version__)"; pytest -q tests/unit/test_analysis_gee.py tests/integration/test_m9_analysis_pipeline.py'
```

**Prediction:** the pinned versions are printed, and the same 5 tests fail. Without the `-e` override they pass. That result would reproduce CI's failure locally, with the exact pinned stack.

## Fix options (the RD decides; none applied)

1. **Recommended.** Replace the degenerate fixture with a non-degenerate one. This is a test-only change that needs RD authorization, because the tests are M9 evidence. Production code and frozen behavior are unchanged. Also add a regression test asserting that an exactly singular fixture classifies as SINGULAR under every kernel.
2. Force a BLAS kernel in the image (`OPENBLAS_CORETYPE`). Not recommended: it masks the knife-edge and ties results to one kernel.
3. Add a tolerance to `classify_failure`. **Rejected:** it changes frozen M9 behavior.

## Update 2026-09-30: RD reproduction with the pinned stack did NOT reproduce CI

**Command:** `-e OPENBLAS_CORETYPE=Prescott`, pinned image (numpy 2.5.3, scipy 1.18.1, statsmodels 0.15.0). **Result:** every GEE unit and integration test **passed**.

**Status corrections:**
- The "root cause" wording above is **withdrawn**. It remains a hypothesis.
- **Proven only for the sandbox stack** (numpy 2.2.6, scipy 1.15.3, OpenBLAS 0.3.29): the fixture's `cov_robust` has a smallest eigenvalue at machine precision, and the verdict flips with the OpenBLAS kernel.
- **Unverified:**
  - whether `OPENBLAS_CORETYPE` took effect inside the pinned image (no runtime core was printed);
  - whether the pinned stack's fixture is also knife-edge (eigenvalues not measured there);
  - which CPU and kernel GitHub's run #113 used.

## Update 2: runner image observed; pinned stack is knife-edge; GitHub CPU unknown

**Observed** from the "Set up job" section of run #113:
- runner 2.337.0; Hosted Compute Agent 20260828.587; region centralus;
- Ubuntu 24.04.5 LTS; image `ubuntu-24.04`, version 20260920.314.1.

**Observed locally** with the pinned stack (Python 3.12.7, numpy 2.5.3, scipy 1.18.1, statsmodels 0.15.0):
- the smallest eigenvalue of `cov_robust` is about 1e-16, so the matrix is singular to machine precision;
- auto (Haswell) gives GeeFit; forced Prescott (reported as Katmai) also gives GeeFit.

**Unresolved:** run #113's CPU and BLAS/SIMD dispatch. They were not logged and cannot be recovered. Hosted runners draw from a mixed CPU pool, and #1–#112 passed.

**Smallest diagnostic:** `.github/workflows/ci113-env-probe.yml` in **this** repository.
- Manual trigger; 8 independent `ubuntu-24.04` jobs.
- Each job builds Velith's **unchanged** image at `5452efc` and runs `ci113_eig_probe.py` (CPU model and flags, NumPy SIMD features, numpy and scipy OpenBLAS cores, versions, eigenvalues, `fit_gee`).
- Each job then runs the two GEE test files.
- It pairs CPU/core with pass/fail. Velith itself is not modified.

## Update 3: ROOT CAUSE ESTABLISHED on real GitHub runners (ci113-env-probe run #2; logs `stage0/logs_99522463703.zip`)

**Setup:** 8 jobs, `ubuntu-24.04`, Velith `5452efc` built with its unchanged image. In every job: Python 3.12.7, numpy 2.5.3, scipy 1.18.1, statsmodels 0.15.0, `*_NUM_THREADS=1`.

| Job | CPU | AVX-512 exposed | numpy / scipy OpenBLAS core | min eigenvalue of `cov_robust` | `fit_gee` | 5 GEE tests |
|---|---|---|---|---|---|---|
| 1, 2, 7 | EPYC 7763 | no | Haswell / Haswell | +4.16e-16 | GeeFit | pass |
| 6, 8 | EPYC 9V74 | no | Haswell / Haswell | +4.16e-16 | GeeFit | pass |
| 3, 4, 5 | EPYC 9V74 | **yes** | **SkylakeX / SkylakeX** | **−9.71e-17** | **GeeFailure** | **fail** |

**The correlation is 8/8.** When the runner exposes AVX-512, OpenBLAS selects SkylakeX kernels and numpy selects its AVX-512 SIMD paths. The rounding sign of the near-zero eigenvalue then turns negative, Cholesky fails, and the rule returns `SINGULAR_ROBUST_COVARIANCE`. Runners without AVX-512 exposed get Haswell kernels, a positive sign, and a pass.

The EPYC 9V74 appears both with and without AVX-512 exposed, so the determinant is **AVX-512 exposure**, not the CPU model. Run #1 of the probe (2/8 failures) and CI #113 are consistent with this. Across both probe runs, 5 of 16 jobs failed.

**Classification (final):**
- not dependency drift (identical pinned versions everywhere);
- **platform numerical behavior**: the AVX-512 dispatch path;
- exposed by a **degenerate test fixture**: the true smallest eigenvalue is 0.

The frozen production rule behaves as specified: SINGULAR is mathematically correct for this matrix.

**Unresolved (not needed for the verdict):** the split of contribution between OpenBLAS SkylakeX and numpy's AVX-512 SIMD. Both switch together.

**Implication:** on any genuinely degenerate input, M9 classification is not cross-machine deterministic. This is observed counter-evidence to the D27 cross-machine determinism acceptance requirement. It is an RD/SRC item.

## Governance record: SRC ruling and test-only repair (2026-09-30)

**SRC ruling:** archived as `reviews/src/SRC_2026-09-30_CI113_GEE_SINGULARITY_ruling.txt`. The SRC finds:
- the behavior is a **demonstrated violation of D27** at the singular boundary;
- D27 is not amended;
- `fit_gee` and the frozen M9 rules stay unchanged;
- a future, focused spec amendment will be required to define a singularity tolerance before any production execution.

**RD authorization:** a TEST-ONLY repair implementing SRC acceptance criteria 1–3.

**Repair, uncommitted in Velith main.** Changed files: `tests/unit/test_analysis_gee.py` and `tests/integration/test_m9_analysis_pipeline.py` (+82/−11). No production, spec, CI or Docker change.
- **Criterion 1:** new well-conditioned fixtures.
  - Unit: `_a1_vs_a0_trend` (A1 passes iff `t % 6 < index + 2`).
  - Integration: `_kgt1_trend_rule`, the same A1 rule, with A0 and A2 unchanged.
  - They are used by exactly the five failing tests. Measured: checkpoint effect 0.79, smallest eigenvalue of `cov_robust` 5.0e-2 (ratio 0.11). A2_VS_A1 under the trend rule has smallest eigenvalue 2.0e-2.
  - The unit fit test now also asserts |β_checkpoint| > 0.5 and smallest eigenvalue > 1e-3.
- **Criteria 2–3:** permanent `test_singular_boundary_outcome_is_documented_as_hardware_dependent`, on the degenerate `_a1_vs_a0()`:
  - it asserts equal A1 pass counts per checkpoint (a data property);
  - it then accepts GeeFit (with β_checkpoint ≈ 0) **or** `SINGULAR_ROBUST_COVARIANCE`.
- **Unresolved, and NOT satisfied by a green CI:** production determinism at the singular boundary (D27 cross-machine).

**Additional finding, not in SRC scope, no change made:** `test_gee_failure_contributes_p_one_and_yields_no_go` asserts GeeFailure on a *rank-deficient* one-task design. That is the mirror-image knife-edge. It passed on all 16 GitHub jobs and locally with the pinned stack. In the CSE sandbox (numpy 2.2.6, auto/Haswell) it returned GeeFit. This is recommended for SRC review.
