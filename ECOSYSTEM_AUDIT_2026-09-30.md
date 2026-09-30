# Ecosystem Audit — 2026-09-30 (read-only; evidence-based)

Scope: `E:\Projects\OpenSourceLab\repos\{mini-flywire, Noetica-agent-lab, Velith, mini-prometheus, Velith-research}`. Nothing was modified.

## 1. Verified repository state

| Repo (layer) | HEAD | Working tree | What is actually built |
|---|---|---|---|
| mini-flywire (L1, research lab) | `6b0fbc3` (165 commits) | 79 "modified" files are **CRLF-only** (`diff --ignore-cr-at-eol` is empty); 10 untracked probe and draft files | JS cognitive-mechanism experiments (FutureScore V2.3 studies, M6/M7 characterization) |
| Noetica-agent-lab (L2, platform) | `44d380b` (56 commits) | clean | Platform Engineering PE-1…PE-21 frozen (`platform-engineering-v1`); **`noetica` 1.0.0 released (tag `v1.0.0`, DN-9)** |
| Velith (L3, engineering intelligence) | `5452efc` (113 commits) | clean | M0–M9 complete (`m9-complete`) plus identity v2; 741 tests pass. **No real M8 evaluation, M9 pre-registration or M10 artifact exists** (PROJECT_STATE §1). M10 in progress (D31 successor). **No `EngineeringTask`/`EngineeringResult`/`DesignArtifact` API; not published** (D30). |
| mini-prometheus (L4, manufacturing) | `b0c25a0` (42 commits) | 30 "modified" files are **CRLF-only**; `uv.lock` untracked | RM1–RM14 deterministic manufacturing planning and scheduling (`rm14-complete`). The Velith seam is a **stub**; waiting for Velith and Noetica packages. |
| Velith-research (outside git history until now) | `git init`, 0 commits | 29 untracked items (4.7 MB, no secrets found) | Governance, P1 Stage-0, OD-3/OD-4, OD-ENV records |

## 2. Where the stack actually stands

- **Noetica** (L2) is released.
- **Velith** (L3) is the bottleneck. It has not measured the program's spine (Handbook §1.7: compounding under verification), and it exposes no engineering API.
- **Mini Prometheus** (L4) is built ahead of its supplier and waits on Velith.

**Ratified order (D5, D12; D30 keeps both in force):**
1. Software-loop Stage-1 go/no-go (M10).
2. Then electronics/PCB.
3. Then HDL.
4. Then mechanical/FEA.
5. Then manufacturing.

A first machined-part result would require an explicit superseding decision (D30 open question).

## 3. Critical path to the spine (Stage-1 A0 vs A2)

1. P1 feasibility pilot (5 real tasks). **Status:**
   - storage GO (Phase 1, `results/phase1-20260930T093235Z`);
   - model identity pinned (F2);
   - OD-3, OD-4 and OD-7/OD-8 frozen.
   - **Open:**
     - Stage-0/1 image admission;
     - Windows Python 3.12 plus tokenizer check;
     - OD-5, OD-6, OD-9…OD-12;
     - harness authorization (PB-1).
2. P1 output: per-episode cost and apply rate for the real-task loop on this CPU-only host. These are the inputs that decide whether a powered Stage-1 is feasible locally. The measured 16k-context generation costs **≈19–25 min** worst case.
3. BRP and the production verifier (RD-0/RD-2b), then the Stage-1 run and M10 go/no-go.

## 4. Housekeeping findings (low priority, no action taken)

- **CRLF noise** in mini-flywire and mini-prometheus. The Windows system `core.autocrlf=true` makes both trees look modified. The content is unchanged.
- **Stale text in the mini-prometheus README:** it says "Noetica not published". Noetica 1.0.0 is now released.
