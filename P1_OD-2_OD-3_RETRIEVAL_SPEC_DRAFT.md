# M2-PV-P1 — OD-2 prompt template, OD-3 context/output limits, M-C retrieval specification (DRAFT)

**Type:** research / decision preparation for P1 only. **Not ratified. No execution, no harness, no Velith change.**
**Author:** Chief Systems Engineer.
**Date:** 2026-09-29.

**RD ruling recorded:** **P1 OD-1 = M-C** (issue plus fixed non-gold source retrieval), for P1 only. Paired M-A/M-C was not chosen. The P1 §24 "two conditions" row therefore does not apply, and P1 §17 measurements are recorded for one condition per task.

**Basis:**
- P1 design `89f931e0…` (§§10–14, 17–18, 21–22, 24, 27);
- OD-1 analysis `5b9fbee7…`;
- `agent/proposer.py`, `llm/client.py`, `task.py` and `experiments/m2_container_prototype/probe.py` at `5452efc`;
- D28 D-2 (`DECISIONS.md:572`).

**Classes:**
- **EXISTING** = code fact;
- **PROPOSED** = a CSE draft for RD ruling;
- **OPEN** = RD decision;
- **EXT** = must be observed on the execution host.

---

## 0. Code facts that constrain OD-2 and OD-3 (EXISTING)

| # | Fact | Location |
|---|---|---|
| F1 | The client sends `POST /api/generate` with `{"model", "prompt", "stream": false, "options": {"seed", "temperature"}}` only. There is no `raw`, `system`, `num_ctx`, `num_predict` or `keep_alive`. | `llm/client.py:92–104` |
| F2 | Because `raw` is absent, Ollama wraps the prompt in the **model's own TEMPLATE and SYSTEM** (from its Modelfile). The effective model input is therefore template(system, prompt). *(Ollama behaviour; confirm on the host with `ollama show --modelfile` — EXT.)* | Ollama API semantics |
| F3 | The client returns only `response`, `model`, `prompt_eval_count` and `eval_count`. **`done_reason` is discarded**, so output truncation is not directly observable through the frozen client. | `llm/client.py:112–116` |
| F4 | Extraction takes the first fenced block (stripping the language tags `diff`, `patch`, `udiff`, `python`). Otherwise it takes raw text **starting with** `diff --git`, `--- ` or `@@`. Otherwise it returns empty (NO_PATCH). | `agent/proposer.py` `_extract_patch` |
| F5 | The probe applies the patch with a plain **`git apply`** (default `-p1`), and exits with code 92 on failure (PATCH_APPLY_FAILED). **Paths therefore need git-style `a/` and `b/` prefixes.** | `probe.py:108` |
| F6 | The client timeout is 120 s, with no retry in the client | `llm/client.py`; P1 §12 |
| F7 | The fixture precedent says: "… Reply with a unified diff patch only" | `task.py:40` |

---

## 1. OD-2 — Exact P1 prompt template (PROPOSED; RD rules)

```
You are fixing a bug in the Python repository `{repo}` at a fixed commit.
You cannot run code or see any files other than those shown below.

## Issue
{problem_statement}

## Source files (retrieved automatically from the repository; may be incomplete)
{files}

## Instructions
Reply with exactly one fenced ```diff block containing a single unified diff that fixes the issue.
Use git-style paths relative to the repository root, prefixed a/ and b/
(for example: --- a/pkg/module.py and +++ b/pkg/module.py).
Copy unchanged context lines exactly as they appear in the files above.
Do not modify or add test files. Do not include any text outside the diff block.
```

**Where `{files}` is**, for each retrieved file in rank order:

```
=== FILE: {path} ===
{verbatim file content, no line numbers}
=== END FILE: {path} ===
```

**Design notes (derived from the code facts):**
- **N1 — delimiter.** P1 §11 proposed `--- FILE: <path> ---`. That begins with `--- `, which is a raw-diff prefix in `_extract_patch` (F4). An echoed delimiter at the start of an unfenced reply would be **mis-extracted as a patch**. The `=== FILE ===` delimiter avoids the collision. This corrects a PROPOSED item, not a frozen one.
- **N2 — paths.** The explicit `a/` and `b/` instruction follows from F5. Without it, a correct edit with bare paths fails `git apply -p1`, which would confound format with capability.
- **N3 — no line numbers.** Line-numbered content invites numbers leaking into diff context lines. Their effect on `git apply` hunk offsets is not asserted here.
- **N4 — never in the prompt** (unchanged from P1 §11 and §22): TaskSpec contents, gold `patch`, `test_patch`, F2P/P2P ids, `hints_text` (OD-11), image digest, verifier or probe internals, exclusion metadata, other tasks' data.
- **N5 — `{repo}`** is the SWE-bench `repo` field (for example `astropy/astropy`). The base-commit hash is **not** included. It is not leakage, but it adds nothing the model can use without repository access.
- **N6 — the model TEMPLATE and SYSTEM wrap this text (F2).** They are part of the effective configuration and must be recorded (§2).

**Leakage-audit extension.** The P1 §22 automated audit runs on the **final prompt, including retrieved content**. Any gold `+`/`-` hunk line, any `test_patch` text, any F2P/P2P id, or any hint substring longer than 40 characters makes the task `INADMISSIBLE_LEAKAGE`.

---

## 2. OD-3 — Context and output limits (analysis; RD rules)

**The problem under M-C.** Retrieved source makes long prompts the norm. The client cannot set limits (F1). Truncation of the **input** is silent (P1 §12). Truncation of the **output** is not directly observable (F3).

| Option | Mechanism | Consequences |
|---|---|---|
| **(a) Server defaults plus an inadmissibility rule** | Keep the server's default `num_ctx`/`num_predict`. A task whose prompt plus output reserve exceeds the effective context is inadmissible (§9 item v). | No new model identity. If the default context is small (EXT), the retrieval budget becomes tiny or many tasks become inadmissible, which weakens M-C. The default value is **version-dependent (EXT)**. |
| **(b) A Modelfile-derived model** | `FROM <pinned base>` with explicit `PARAMETER num_ctx` and `num_predict`, inheriting TEMPLATE and SYSTEM. It is recorded as a **distinct model identity** (its own digest). | Limits are explicit and reproducible. Memory use and latency grow with `num_ctx`, which interacts with the 120 s timeout (OD-7/OD-8). The derived identity must be recorded in the evidence. |
| **(c) A server-level context setting** | For example an environment variable, if the installed Ollama version supports one (**EXT**; not asserted) | Affects every model on the server. Must be recorded. Less self-describing than (b). |

**Whichever option is chosen, the following must be fixed:**
1. **Budget identity:** B_prompt ≤ num_ctx − R_out − M, where R_out is the output reserve (= `num_predict` under (b)) and M is a safety margin.
2. **Token counting.** `prompt_eval_count` **cannot** detect truncation, because prefix caching lowers it (P1 §17 caveat; the shared header is a common prefix across tasks). Prompt length must be counted **offline with the exact model tokenizer** (EXT: how the tokenizer is obtained and pinned), or bounded conservatively. An over-budget prompt means fewer retrieved files (§3.6), never silent truncation.
3. **Output-truncation rule.** Because `done_reason` is unavailable (F3), a completion with `eval_count == num_predict` SHALL be classified as generation-truncated. This needs a P1 §18 failure-taxonomy line, pre-declared before execution. It is added **before** any result exists, so it complies with P-2.
4. **Recorded model identity (EXT):** weights digest, `ollama show --modelfile` (TEMPLATE, SYSTEM, PARAMETERs), Ollama server version, effective `num_ctx` and `num_predict`.
5. **Timeout interaction.** Expected latency at B_prompt must be checked against 120 s. A timeout is GEN_INFRA, retried up to 2 times per P1 §21 (OD-8), and it must not be systematic.

**Values are not chosen here.** num_ctx, R_out, M and the option all depend on EXT facts: the model's context limit, the host's memory, and the server default.

---

## 3. The fixed non-gold retrieval mechanism — required specification

Every field must be fixed **before execution**, **without tuning on any non-excluded task**. The retriever code is part of the evidence (its SHA-256 is recorded).

| # | Field | Must specify | PROPOSED default (RD rules) |
|---|---|---|---|
| 3.1 | Algorithm | Name, parameters, implementation and version | Okapi BM25, k1 = 1.2, b = 0.75 (standard defaults, untuned). A pure-Python deterministic implementation in the research workspace, pinned by file hash. |
| 3.2 | Corpus / pool | The source of the files and the snapshot | Files tracked at `base_commit` (`git ls-files`), read from the admitted, digest-pinned task image's repository (Stage 0), on the trusted side, before any candidate runs |
| 3.3 | Inclusion | File types and size | `.py` files only. Files above a per-file size cap are excluded (the cap value is OPEN). |
| 3.4 | Exclusion rules | Generic rules that need **no** reading of `test_patch` (P1 §22 item 2) | (i) test files by path pattern: any path component `test`/`tests`/`testing`, `test_*.py`, `*_test.py`, `conftest.py`; (ii) the OD-5 protected configs; (iii) vendored or generated directories (list OPEN). **Audit assertion:** after pool construction, the leakage audit (which may read `test_patch`) asserts that no `test_patch` path is in the pool. A violation makes the task INADMISSIBLE. |
| 3.5 | Query | Construction and tokenization | `problem_statement` verbatim (no `hints_text`, per OD-11). Tokenizer: lowercase `[A-Za-z0-9_]+`, and the same tokenizer for documents. |
| 3.6 | k and token budget | Maximum file count, budget, and the fit rule | Top-k files in rank order while the running prompt stays ≤ B_prompt. A file that does not fit is **skipped** and the next is tried, up to k. k and B_prompt are OPEN, tied to OD-3. |
| 3.7 | Ordering and ties | A fully deterministic order | Score descending, then path ascending (bytewise UTF-8). Files with score 0 are excluded. |
| 3.8 | Empty result | Disposition | Zero retrieved files gives an inadmissible task, not a silent M-A fallback. Otherwise the task would drift into an unruled condition. |
| 3.9 | Determinism and identity | What the material is a function of | material = f(base tree at the image digest, `problem_statement`, retriever hash, parameters). **pilot_task_identity = SHA-256(material)** (P1 §10), recorded in the registry together with `instance_id`. |
| 3.10 | Caching and run order | Effect on observations | Single condition, so there is no paired prefix issue. A common header prefix across tasks still affects `prompt_eval_count` and latency through KV caching. Rule: a **fixed task order** (lottery order T1…T5), recorded. `prompt_eval_count` is recorded as-is, with the caveat. Optionally the model is reloaded between tasks (engineering; server-level keep-alive is EXT). |

**Considered alternative (not proposed): published SWE-bench BM25 retrieval sets.** They would remove the custom code. Their exact contents, their test-file handling and their coverage of Verified are **unverified** here, and they would not apply the D-2-aligned exclusions in 3.4.

---

## 4. Contradiction check

| Source | Finding |
|---|---|
| D28 D-2 | P1 builds no D28 real-task `Task`s, so D-2 does not bind it. The 3.4 exclusions keep the M-C material D-2-aligned (no test data, hidden tests, gold or protected surface). **No contradiction.** |
| P1 §22 item 2 (the retriever never reads `test_patch`) | Respected. The exclusions are generic, and only the audit reads `test_patch`. **No contradiction.** |
| P1 §11 proposed delimiter | Corrected by N1. It was a PROPOSED item, so **no frozen contradiction**. |
| P1 §17, §18, §24; P-2, P-3 | A single condition. The output-truncation line is added before execution. Raw counts only. **Consistent.** |
| D30.3 | The retriever is experiment-side research code, not a Velith platform mechanism. The OD-4 harness authorization must still carry the D30 posture statement (AM-3). **No contradiction.** |
| D31; RD-0 (unratified); RD-2b | P1 still supplies no p0 and does not bind the confirmatory material function (RD-13, proposed). **No contradiction.** |
| M2-PV-R §9; BC-1 / BC-2; D26 / D27 | P1 remains feasibility evidence before production-verifier automation. Nothing touches the production specification. **No contradiction.** |

**Result: no contradiction.**

---

## 5. Must be frozen before P1 execution

- OD-1: **ruled (M-C)**.
- **OD-2:** the §1 template text (delimiter, path instruction).
- **OD-3:** the option; num_ctx, R_out, M; the token-counting method; the output-truncation rule; the recorded model identity.
- **The retrieval specification**, every field in §3, plus the retriever code hash.
- **OD-5:** the protected-config set (also a pool exclusion).
- **OD-11:** hints excluded.
- **OD-12:** the seed rule.
- **OD-6:** the replacement rule, **including the empty-retrieval case**.
- **OD-7 / OD-8:** timeouts and retries under long prompts.
- **OD-9:** the registry format.
- **OD-10:** the anchor.
- **The fixed task-order rule.**
- **OD-4:** harness authorization and location (PB-1), with the D30 posture statement.
- **The Stage-0 EXT inventory**, with its authorization.

## 6. Remains open

- **RD rulings needed:** OD-2 to OD-12; the §3 numeric fields (per-file cap, k, B_prompt, vendored list); and the OD-3 option and values, which need EXT facts first.
- **Outside P1:** RD-13 (confirmatory material; proposed, not entered in the register); RD-0 ratification; PV-freeze; the production verifier; the BRP; δ and the power chain; the successor specification.

## 7. Next RD decision after OD-2 / OD-3

**OD-5: the protected-config set and the retrieval-pool exclusion rule (§3.4).** It is the remaining input that fixes both the sealed-execution protected surface and the M-C pool. The retriever specification cannot be frozen without it.

---

## RD rulings recorded after this draft

- **OD-2 = approved as drafted** (§1).
- **OD-3 principles frozen:**
  - no silent input truncation;
  - no over-budget prompt;
  - the exact tokenizer and model identity are recorded;
  - `eval_count == num_predict` counts as generation truncation;
  - prompt length is measured independently of `prompt_eval_count`;
  - the effective TEMPLATE and SYSTEM are part of the recorded configuration.
- **OD-3 context regime = 16384 (RD, 2026-09-29), for P1 M-C.**
  - **Rationale:** 4096 leaves too little room for non-gold retrieval once the issue text is included.
  - **Execution constraint:** generation and task-container execution run **sequentially**, so the 13.6 GB model footprint does not compete with Docker.
  - **Evidence:** Stage-0 evidence §§14–15.
- **Still open:** output reserve (`num_predict`), margin M, retrieval budget B_prompt, the mechanism that applies 16384 on the Velith client path (a derived Modelfile or `OLLAMA_CONTEXT_LENGTH`; the frozen client sends no `num_ctx`), OD-7 (timeout) and OD-8 (retries).
- **Pending evidence:** the cold 16k prompt-evaluation time (supplemental S2, `timing/Invoke-Stage0Supplemental16kCold.ps1`, not run).
