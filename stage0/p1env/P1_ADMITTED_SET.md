# P1 admitted task set: frozen 2026-10-02 (RD)

Admission is complete. On the RD's instruction, all further lottery and admission work has stopped.

This set was selected under:
- `M2-PV-P1_PILOT_DESIGN.md` §7 lottery and §9 admissibility;
- OD-5 and OD-6, ratified prospectively in `P1_RD_RATIFICATION_2026-10-01.md`.

Provenance:
- dataset revision `78f471bf655a3137b2e8a75af1501690ec009ec3`;
- pool of 98;
- frozen probe SHA-256 `560834d5…138e1f`.

## Admitted set (Case A, gold patch)

All five passed: `PASSED / ALL_REQUIRED_PASSED`.

| Slot | Instance | Pinned linux/amd64 image digest | Case A | Evidence dir | MANIFEST.sha256 (sha256, first 16) |
|---|---|---|---|---|---|
| T1 | pallets__flask-5014 | `sha256:eaf597005c159361cb8ee26018fb3741b320f331065f0c95726d83ccf2f1fba4` | 60/60 | `results/t1-admission/` (M2 spec) | `06c7ef93c0829c51` |
| T2 → R5 | matplotlib__matplotlib-24970 | `sha256:a38f22a0f44eab9328d76624c27667b807bb7b0e994dd537f7a2b5919b4e8800` | 254/254 | `results/admission-T2R1R1R1R1R1/` | `a9610083f974a7be` |
| T3 | scikit-learn__scikit-learn-14629 | `sha256:de0579911863656a0331adc8d2dd6080ccc2543d0a5fd2bd68d753c8df1ec7c8` | 27/27 | `results/admission-T3/` | `7db5a164bc18d982` |
| T4 | astropy__astropy-7336 | `sha256:481ebd12ef496853db01765b1dd57d9aebdedd056c22656b9f483fc1c8379da9` | 340/340 | `results/admission-T4/` | `75fdb81316ab8d64` |
| T5 → R1 | pydata__xarray-7393 | `sha256:15d79e643a94b7fba2a8138cdc5daf011bc2d99f61a7ce30508689a90ab9042f` | 73/73 | `results/admission-T5R1/` | `0970ab8a69b5d0a1` |

All five manifests were checked with `sha256sum -c` before the freeze commit, and all were OK.

The task spec used by the P1 harness is the `<slot>.spec.json` file in each evidence directory. For T1, it is the M2 spec referenced in `T1_ADMISSION_RECORD.md`.

## Inadmissible tasks (evidence preserved, not used)

Every one failed at Case A with `INFRA_ERROR / RESULT_MAPPING`. The cause in each case was required test IDs that the dataset truncates at a space inside a parametrization.

| Slot | Instance | Unmapped required IDs | Evidence |
|---|---|---|---|
| T2 | matplotlib-24570 | 1 | `results/admission-T2/` |
| T2R1 | matplotlib-26466 | 7 | `results/admission-T2R1/` |
| T2R1R1 | matplotlib-26342 | 10 | `results/admission-T2R1R1/` |
| T2R1R1R1 | matplotlib-24149 | 28 | `results/admission-T2R1R1R1/` |
| T2R1R1R1R1 | matplotlib-22719 | 11 | `results/admission-T2R1R1R1R1/` |
| T5 | xarray-6721 | 3 (`test_setitem_using_list_errors[var_list0-data0-Different` etc.) | `results/admission-T5/` |

Each replacement was the immediately next eligible task of the same repository, per OD-6 literal; see `results/lottery_replacement_*.json`. `p1_extra_tasks.txt` holds only the last replacement line (T5R1). The task line for every earlier replacement is kept in its `lottery_replacement_*.json`.

## Tooling note

The T3 first attempt stopped at the OD-5 inspection with exit 128; its output is preserved as `results/admission-T3/03_spec_attempt1_exit128.txt`.

- **Cause:** the `for` loop's exit status leaked from `git cat-file -e` on the last candidate, which was absent at base.
- **Fix:** `p1_spec.py` now uses `git rev-parse --verify` plus `git ls-tree --name-only`, so an absent path gives empty output and a git error stops the run with exit 96 or 98.
- **What the fix does not change:** the OD-5 semantics.
- **Specs built before the fix:** the matplotlib specs were built with the old loop. Their last candidate (`tox.ini`) existed at base, so the existing set is identical.
