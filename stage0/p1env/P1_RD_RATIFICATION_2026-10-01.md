# P1: RD ratification for the remaining execution (2026-10-01) and the T2 admission observation

## RD ratification (verbatim in substance; prospective, effective 2026-10-01)

The ratification is effective **prospectively**. OD-5 and OD-6 were **not** ratified before the T2 run.

1. §7 lottery and five-task acceptance, as written in `M2-PV-P1_PILOT_DESIGN.md` (SHA-256 `89f931e0…b203`).
2. §9 admissibility, as written.
3. OD-5, the protected-files rule, as written (§14).
4. OD-6, the replacement rule, exactly as written (§8):
   - if a task is inadmissible at admission, before generation, it is replaced by the next eligible task of the same repository in the pre-fixed lottery order;
   - T1 has no replacement;
   - there is no replacement after generation starts.
5. No additional test-ID space or bracket pre-check is authorized.
6. No eligibility rule may be added or modified on the basis of the observed T2 result.

## T2 admission observation (operational, not a scientific performance result)

**Run:** `results/admission-T2/` (RD-run 2026-10-01). The spec was built with the OD-5 rule, which was then still proposed.

| Item | Observed |
|---|---|
| Identity | pinned digest `sha256:5d932722…b323c`, linux/amd64: PASS |
| Execution | baseline and candidate both RAN, exit 0, `network_mode=none`, network probe blocked |
| F2P | `test_packers[bottom]` and `test_packers[top]`: failed at baseline, passed with the gold patch |
| Required-ID mapping | 2 F2P + 267 P2P = **269 required IDs; 268 mapped; 1 unmapped**. The unmapped ID is the dataset entry `lib/matplotlib/tests/test_offsetbox.py::test_picking[axes`, which is truncated |
| Probe classification | `INFRA_ERROR / RESULT_MAPPING / "1 required ids unmapped"` |
| Disposition | inadmissible under the subsequently ratified §9 (iii), "every required id mapped". Replacement follows OD-6 as ratified |

## Lottery resolver (`p1_lottery.py`)

The resolver selects the immediately next eligible task with no post-hoc filter. It STOPs unless:
- the dataset revision starts with `78f471bf`;
- the pool has 98 tasks;
- the first task per repository reproduces T2–T5.

It pulls nothing and admits nothing.

## OD-6 replacement chain (operational admission observations under the ratified gate)

Lottery resolver runs: both passed revision `78f471bf655a…`, pool 98, and T2–T5 reproduction. Each selected the immediately next eligible matplotlib task.

| ID | Instance | Image digest | Required IDs | Mapped | Unmapped | Classification |
|---|---|---|---|---|---|---|
| T2 | matplotlib-24570 | `5d932722…b323c` | 269 | 268 | 1 | INFRA_ERROR / RESULT_MAPPING, inadmissible |
| T2R1 | matplotlib-26466 | `35be1078…29784` | 101 | 94 | 7 | INFRA_ERROR / RESULT_MAPPING, inadmissible |
| T2R1R1 | matplotlib-26342 | `a5f37bb4…d376e` | 82 | 72 | 10 | INFRA_ERROR / RESULT_MAPPING, inadmissible |
| T2R1R1R1 | matplotlib-24149 | `14294abc…0d402` | 768 | 740 | 28 | INFRA_ERROR / RESULT_MAPPING, inadmissible |
| T2R1R1R1R1 | matplotlib-22719 | `7a369057…18ef9` | 69 | 58 | 11 | INFRA_ERROR / RESULT_MAPPING, inadmissible (RD-reported) |

**Mechanism, in all three:** the unmapped IDs are dataset test IDs truncated at a space inside a parametrization, e.g. `test_contour_shape_error[args0-Length`.

**Next in frozen order after 22719** (from the resolver's information-only listing): 24970 (F2P 1 / P2P 253 / suspicious 0), 25960 (1/137/4), 24637 (1/29/9), 26113 (1/812/36).

**C: free** before the 24149 pull: 37,337,509,888 B. Not re-measured since the 24149 and 22719 pulls.

**Storage stop (RD, 2026-10-01):** C: free before the T2R1R1 pull was 22,645,944,320 B, below the 25,442,795,777 B readiness threshold. The value after the T2R1R1 pull was not measured.
