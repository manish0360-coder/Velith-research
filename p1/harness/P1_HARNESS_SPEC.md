# P1 harness specification: frozen 2026-10-02 (RD ruling R1–R7)

**Scope.** This is an experiment-only harness for M2-PV-P1, kept in the research workspace. It writes nothing to Velith main and nothing to any Velith store.

- **Probe.** The frozen M2 probe (`560834d5…`) is imported unmodified, as a library. This resolves PB-1 by the route in P1 §15.
- **Velith code.** Generation calls Velith's frozen code only: `OllamaClient`, `Proposal`, `_extract_patch`, `Task` and `derive_task_seed`.
- **Status.** P1 evidence is probe-level feasibility evidence, not a verdict of record.

## Authority

| Area | Source |
|---|---|
| Material and prompt | OD-1 = M-C; the OD-2 template exactly as approved (`P1_OD-2_OD-3_RETRIEVAL_SPEC_DRAFT.md` §1). A test checks the template byte-for-byte against that document. |
| Limits | OD-3: `num_ctx` 16384, `num_predict` 1024, M 128, **B_prompt 15232**, the HF tokenizer counting rule (`e434a23f…`, `091b9dad…8714`, tokenizers 0.23.2, messages branch, +1). OD-7: Stage-X timeout 900 s, and 1800 s for slot T5. OD-8: at most 1 retry, for infrastructure failures only. RAM ≥ 4 GiB free. Generation and verification run sequentially. |
| Protected surface | OD-5, already inside the frozen admission specs |
| Retrieval (R1) | BM25 with k1 1.2 and b 0.75. Tokens: `[A-Za-z0-9_]+`, lowercased. No per-file cap. k = 5, taken in ranked order; a file that doesn't fit is skipped. Vendored directories: `extern, externals, _vendor, vendor, vendored, third_party, cextern, _externals, build, dist` |
| Identity and seed (R2) | identity = SHA-256 of the final prompt in UTF-8; seed = `derive_task_seed(identity, 0)` |
| Hints (R3) | `hints_text` is never in the prompt. It is read only by the leakage audit. |
| Registry (R4) | `p1/PILOT_EXCLUSION_REGISTRY.json`, for audit and safety only. It is not a selection rule. |
| Truncation (R5) | `completion_tokens == 1024` gives code **GEN_TRUNCATED** plus a flag. If a patch was extracted, it is still verified. |
| Generation route (R6) | `docker run --rm -i --read-only --cap-drop ALL` on the pinned `velith-verifier:m0` image ID, with no volumes, so the episode store cannot be reached. It reaches Ollama at `host.docker.internal:11434`. **This replaces the Windows-host wording of the OD-4 decision input for the P1 harness.** |
| One shot (R7) | T3 is the real P1 episode. No regeneration once a completion exists. `run` refuses to start if the harness or `p1_gen.py` SHA differs from `PILOT_SET.json`. |

## Implementation choices fixed before any output

These were made before any prompt or completion existed, and none was tuned on a task.

- **Pool.**
  - It is built from `git ls-tree -r -l -z <base_commit>` plus `git cat-file --batch`, run inside the pinned task image with `--network none`.
  - Files are regular `.py` blobs only. Each blob is checked against its git SHA-1.
  - The exclusions apply in this order:
    1. Test files: a directory component `test`, `tests` or `testing`; or a file named `test_*.py`, `*_test.py` or `conftest.py`.
    2. Vendored directories.
    3. OD-5 config basenames.
  - Content that is not valid UTF-8 is excluded and listed.
  - The retriever never reads `patch`, `test_patch`, test IDs or hints.
- **BM25.**
  - idf = ln(1 + (N − df + 0.5)/(df + 0.5)).
  - Query terms are distinct.
  - Documents are file contents.
  - Only scores above 0 are kept. Ties are broken by path, ascending bytewise (UTF-8).
- **Rendering.**
  - Values are concatenated verbatim into the OD-2 template; `str.format` is never used on task text.
  - File blocks are separated by one blank line.
  - A `\n` is added before `=== END FILE` only when the content doesn't already end in one.
  - The prompt ends with a single `\n`.
- **Fit rule.** At each candidate file, the whole prompt is re-counted with the pinned tokenizer.
- **Leakage audit: RD EXPLICIT FREEZE (2026-10-02), recorded verbatim in substance.**
  1. A match between prompt text and a line that also appears in the original retrieved file is not, by itself, leakage.
  2. Leakage is gold patch or test material introduced outside the legitimately retrieved original-file corpus. That includes:
     - gold patch content injected independently;
     - `test_patch` content;
     - `test_patch` paths entering the retrieval pool;
     - hint contamination;
     - cross-region or cross-boundary contamination that cannot be attributed to legitimate retrieved source text.
  3. Every raw match is recorded with its provenance and location.
  4. The audit is deterministic and must not be weakened after T3 output is seen, nor reinterpreted once generation begins.

  **How the freeze is implemented.** The legitimate prompt sources are exactly the three that OD-1/OD-2 put in the prompt:
  - the fixed template text;
  - the dataset's `problem_statement`, verbatim;
  - the retrieved base-tree files, blob-verified.

  Matches inside the issue text are recorded under the `issue` region and reported separately, so any overlap between the issue and gold or hint text is visible to the RD.
- **Leakage audit mechanics** (P1 §22 plus the OD-2 extension).
  - The literal needles are:
    - each gold and test-patch `+`/`-` hunk line, stripped and non-empty;
    - every F2P and P2P ID;
    - every 41-character window of `hints_text`;
    - the full gold patch and the full `test_patch` text.
  - Every occurrence of a needle is attributed to the region that contains it:
    - the fixed template text;
    - the issue text from the dataset;
    - a base-tree file's content (blob-verified);
    - a region boundary.
  - **FAIL if any of these hold:**
    - the full gold patch or full `test_patch` text appears;
    - a `test_patch` path is in the pool or the prompt;
    - any occurrence crosses a region boundary.

    Occurrences inside verbatim allowed sources are reported but exempt. *Rationale:* a removed `-` line is base content by definition, and an empty or very short line occurs everywhere. A literal "any line" rule is therefore ill-defined.
- **Stage G.**
  - Before generation, the harness runs `ollama stop` (cold start, no cached prefix) and checks Windows free RAM is at least 4 GiB.
  - Inside the container, before any request:
    - the module SHAs match Velith `HEAD` (`6ca531f…`), so the composed `propose()` body below is pinned;
    - the seed matches;
    - the prompt matches the identity;
    - the `/api/tags` digest equals `e196dcd9…c45c`;
    - the model is not already loaded.
  - The `propose()` body is composed in `p1_gen.py`, only so the raw completion can be retained (P1 §13 and §19).
  - The raw stdout is written to disk before it is interpreted.
  - After the call: the observed `prompt_eval_count` must equal the prediction, otherwise a `TOKEN_COUNT_MISMATCH` flag is recorded; `/api/ps` must report `context_length` 16384. Then the model is unloaded before Stage X.
- **Retries.**
  - A failure before the request is sent is not an attempt, and the run can be repeated.
  - A sent request without a completion counts as an attempt. It can be retried once, except after a timeout.
  - Stage X can be retried once, on `INFRA_ERROR` only, and never after `RESOURCE_KILLED`.
- **§18 code** (first match wins): GEN_INFRA, GEN_TRUNCATED (R5), NO_PATCH, MALFORMED_PATCH or PATCH_DOES_NOT_APPLY (decided from the git-apply stderr in the candidate stdout), BASELINE_UNHEALTHY, EXEC_INFRA, TIMEOUT, RESOURCE_EXHAUSTED, TEST_INTEGRITY (the patch touches a protected path, or the probe removed a runner config), CANDIDATE_FAILED, CANDIDATE_PASSED. The flags and the Stage-X-only code are recorded separately.

## Commands (WSL) and evidence

`prepare T1…T5` → `gencheck` → `freeze` → `selfcheck` are Milestone 1, with no model request. `run T3` is Milestone 2.

| Path | Content |
|---|---|
| `p1/evidence/<slot>/P/` | `prompt.txt`, `material.json`, `leakage_audit.json`, `preflight.json`, `MANIFEST.sha256` |
| `p1/evidence/_gencheck/` | the container check, run with `--network none` |
| `p1/evidence/T3/X-selfcheck-gold/` | Stage X through the harness with the gold patch, compared with the T3 admission evidence |
| `p1/evidence/<slot>/G/attempt-n/`, `X-n/`, `episode.json` | Milestone 2 |
| `p1/PILOT_SET.json`, `p1/PILOT_EXCLUSION_REGISTRY.json` | frozen once and never rewritten |

`test_p1_harness.py` holds offline tests: template fidelity, BOS text, BM25, exclusions, the fit rule, git parsing and blob hashes, the leakage audit, seed equivalence, §18 classification, and `p1_gen.py` check mode against the real Velith source.
