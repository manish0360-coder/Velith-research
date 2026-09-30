# M9 Specification Amendment Block — VM2 (`m9-spec-frozen-oed7-vm2`)

**Artifact type:** Proposed amendment text (research workspace), 3 of 3 in the amendment package. The engineering repository's `docs/M9_SPEC.md` is **unchanged**.
**Companions:** `M8-IDv2_DECISIONS_ENTRY_PROPOSED.md` (D29, provisional number) and `M8_IDENTITY_V2_SPEC.md`.
**Source specification:** `M2-PV-R3_M8-M9-M10_IDENTITY_AMENDMENT_SPEC.md`, SHA-256 `d2c51ec15aa00f1c5924ea6aaed8e6de3f7ba286bfc27b5860b5d792b375888a`.
**Engineering baseline:** `b14d918f14d4b5bdfab6fb916811320a742eafa3`. **Current M9 lineage:** `m9-spec-frozen-oed7`.
**Drafted:** 2026-09-26. **Ratification date:** pending.

**Placement (for the future, separately authorized repository gate).** This follows the in-place M9 amendment precedent (OED-2 at `m9-spec-frozen-oed2` / `3d98a84`; OED-7 at `m9-spec-frozen-oed7` / `c33cbb9`):
- Part A is inserted immediately after the existing "M9 Amendment OED-7" block.
- Part B replaces the Status line.
- §3.1, §3.3 and §6 item 1 are amended **by reference** from the block; their body text is left as-is.
- **Precedent note:** OED-7 did more than add a block. It also inserted body text (§3.5.11, `M9_SPEC.md:269`). Whether the VM2 amendment should likewise edit the body text of §3.1, §3.3 and §6 item 1, or amend them by reference only as drafted here, is an open placement choice for the RD at the repository gate. It affects the location of the text only, not its content.

---

## Part A — Amendment block (text to insert)

> **M9 Amendment VM2 (ratification date pending).**
>
> *Reason:* the M8 evaluation identity is superseded by **M8 evaluation identity v2** (D29; `M8_IDENTITY_V2_SPEC.md`). That identity binds the verification contract into evaluation identity through `verification_manifest_hash`. Because the pre-registration is "bound to exactly the M8 evaluation identity components" (§6 item 1; §3.1), and because M10 reconstructs the evaluation identity from pre-registration fields, the pre-registration must carry the new component.
>
> *Authority:* Research Director ruling (M2-PV-R3, Q-A to Q-H); Scientific Review Council delta review, APPROVED.
>
> *Amended provisions (only):*
> - **(1) §3.1 — pre-registered experiment design.** The design components additionally include the **verification manifest hash**: `verification_manifest_hash`, the SHA-256 of the canonical mapping `task_identity → TaskSpec digest` over the **held-out evaluation population only**. It is distinct from, and not interchangeable with, the existing held-out split component `manifest_hash`, which keeps its name and meaning (the full-corpus partition manifest hash). "The components of the M8 evaluation identity (M8_SPEC §3.5)" is read as "the components of M8 evaluation identity v2 (`M8_IDENTITY_V2_SPEC.md` §4)".
> - **(2) §3.3 — content-addressed identity.** The declared components hashed into the pre-registration identity include `verification_manifest_hash`. The version component `spec_version` takes the value `"m9-spec-frozen-oed7-vm2"`. The canonical serialization is unchanged. Any change to the verification manifest yields a new pre-registration identity.
> - **(3) §6 item 1 — Definition of Done.** "Bound to exactly the M8 evaluation identity components" is read as bound to exactly the M8 evaluation identity **v2** components. A pre-registration with `spec_version = "m9-spec-frozen-oed7-vm2"` binds only to evaluations under `identity_version = "m8-evaluation-identity-v2"`.
>
> *Binding rules:*
> - The pre-registration does not store `identity_version`; a VM2 pre-registration is reconstructed only into identity-v2 provenance.
> - Mixed-version joins are rejected: a v1 (`m9-spec-frozen-oed7`) pre-registration with v2 evaluations; a VM2 pre-registration with v1 evaluations; and v2 with v2 under a different verification manifest.
> - The verification manifest is constructed under the fail-closed rules of `M8_IDENTITY_V2_SPEC.md` §3.3. An empty held-out population is **rejected** at construction (`VerificationManifestError`). This is distinct from, and does not alter, §3.5.11 (OED-7).
> - M8 identity v2, this amendment and the M10 reconstruction amendment are **one coordinated identity migration**.
> - M8 v1 (`docs/M8_SPEC.md`) remains the immutable historical specification; M8 identity v2 supersedes only its evaluation identity, by versioned supersession (D29).
>
> *Explicitly not changed by this amendment:*
> - **§3.5 in full**, i.e. the frozen M9 statistical procedure: outcome encoding (PASSED = 1, else 0), complete-case handling (§3.5.1), global-incomplete VOID, the hypothesis structure, GEE, EMM and delta-method SE, Wald inference, the trend test, robust sandwich covariance, McNemar (K = 1, §3.5.5), the Holm-Bonferroni family (§3.5.6), model-failure handling, α = 0.01, GO/NO-GO (§3.5.8), researcher degrees of freedom (§3.5.10), and OED-7 empty-dataset VOID (§3.5.11).
> - The OED-2 A0 time-invariance.
> - The arms; the checkpoint-schedule binding; the sealed-from-results invariant (§3.4).
> - This amendment changes identity and version plumbing, not statistical inference.
>
> *Classifier identity* (D27) is **not** a pre-registration component. *Available-task TaskSpec lineage* is **deferred** (an M2-PV provenance concern) and is **not solved** by this amendment. *Fixtures* use the universal v2 path, with deterministic synthetic 64-hex digest handles. *`AnalysisProvenance`* gains no plaintext `verification_manifest_hash`.
>
> *Existing artifacts:* no real M9 pre-registration exists in the repository (verified at `b14d918`). There is therefore no migration and no rehashing. Pre-registrations under `m9-spec-frozen-oed7` remain historical, and every pre-registration created after this amendment's freeze uses `m9-spec-frozen-oed7-vm2`.

---

## Part B — Replacement Status line (text for the future repository gate)

**Current (at baseline):**
> **Status:** FROZEN (OED-7 amendment) — re-ratified by the Research Director on 2026-09-18; supersedes the prior freezes `m9-spec-frozen-oed2` (`3d98a84`) and `m9-spec-frozen` (`36659cb`). Immutable; the M9 implementation is extracted from it and never redesigns it.

**Proposed:**
> **Status:** FROZEN (VM2 amendment) — re-ratified by the Research Director on ‹ratification date›; supersedes the prior freezes `m9-spec-frozen-oed7` (‹commit›), `m9-spec-frozen-oed2` (`3d98a84`) and `m9-spec-frozen` (`36659cb`). Immutable; the M9 implementation is extracted from it and never redesigns it.

The date line gains "**Re-freeze date (VM2):** ‹ratification date›". The ‹…› values are filled at the repository gate, not before.

---

## Part C — Consistency with companions

| Item | This block | `M8_IDENTITY_V2_SPEC.md` | D29 entry |
|---|---|---|---|
| `SPEC_VERSION` | `m9-spec-frozen-oed7-vm2` | §8.1 | Decision 3 |
| `identity_version` | `m8-evaluation-identity-v2` (reconstruction only) | §4.1, §8.1 | Decision 2 |
| New pre-registration field | `verification_manifest_hash` | §8.1 | Decision 3 |
| Population | held-out-only | §3.1 | Decision 1 |
| Statistics | unchanged (§3.5 in full) | §11 | Decision 10 |

**Acceptance cases.** The 18 identity cases in `M8_IDENTITY_V2_SPEC.md` §12 are specification-level (a design/adversarial audit, not execution evidence). They become implementation acceptance tests; none is implementation-validated.

**Proposed freeze tag:** `m9-spec-frozen-oed7-vm2`, created only at the separately authorized repository gate.
