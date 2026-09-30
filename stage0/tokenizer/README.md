# Stage-0 tokenizer equivalence check (D-E). READ-ONLY. Not yet run on the host.

**Purpose.** This check gates the RD freeze of D-E (the Hugging Face tokenizer counts tokens before sending) and D-C (M = 128).

**Ground truth.** The ground truth is the token IDs the server actually evaluated. Each measured `/api/generate` response carries `context`, which holds the prompt IDs followed by the generated IDs. The prompt IDs are `context[:len(context) - eval_count]`. They are frozen by SHA-256 in `server_truth_manifest.json`, and the script refuses to run if the evidence no longer matches.

**Pass rule, pre-declared.**
- One configuration must reproduce the server prompt IDs **exactly, for every token**, for all 4 gating prompts (1,752, 3,467, 8,188 and 16,108 tokens). A configuration is a rendering plus an `add_special_tokens` setting.
- `prompt_eval_count − len(hf_ids)` must be one constant across those 4 prompts.
- The renderings are tried in a fixed order. Exact equality over up to 16k IDs leaves no room for a chance match.

**Supplementary, not gating (`--gguf`).** Compares the Hugging Face vocabulary and merges with those embedded in the GGUF blob, which Ollama actually uses. The blob is memory-mapped read-only.

**Network.** One download of `tokenizer.json` from `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`. The resolved commit and the file's SHA-256 are recorded, and later runs pass `--revision <commit>` or `--tokenizer-json`. It does not touch Ollama, the models, Docker or Velith main. Output goes to `results/` only.

**Why it runs on the host.** The CSE sandbox cannot reach huggingface.co (the proxy returns 403), and the GGUF blob on D: is not mounted there.

**Sandbox validation of the script**, using a synthetic tokenizer and a synthetic GGUF:
- the PASS path gives exit 0, the correct configuration and offset +1, and GGUF vocabulary and merges equal;
- the FAIL path on the real ground truth gives exit 1;
- a tampered manifest gives exit 2.

**Run in WSL.** The first `pip install` and the tokenizer download need network access.
```bash
python3 -m venv ~/.venvs/velith-tokcheck
~/.venvs/velith-tokcheck/bin/pip install "tokenizers==0.23.2" "huggingface_hub==1.33.0" "gguf==0.19.0"
cd "/mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/tokenizer"
~/.venvs/velith-tokcheck/bin/python check_tokenizer_equivalence.py \
  --gguf /mnt/d/ollama/models/blobs/sha256-5ff0abeeac1d2dbdd5455c0b49ba3b29a9ce3c1fb181b2eef2e948689d55d046
```
Upload the printed output and the `results/tokcheck-*/result.json` file.
