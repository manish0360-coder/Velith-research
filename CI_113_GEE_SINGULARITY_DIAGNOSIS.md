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
