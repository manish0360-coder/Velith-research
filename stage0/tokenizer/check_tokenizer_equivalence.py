#!/usr/bin/env python3
"""Stage-0 READ-ONLY tokenizer equivalence check for P1 OD-3 decision D-E.

Question: does the offline Hugging Face tokenizer reproduce, token for token,
what the Ollama server (deepseek-coder-v2:16b, Ollama 0.34.4) actually
evaluated for the measured Stage-0 prompts?

Ground truth is NOT a count estimate: every measured /api/generate response
carries `context` = [rendered prompt token IDs] + [generated token IDs].
The prompt part is context[:len(context) - eval_count].

Read-only with respect to the host: it reads run evidence, optionally
memory-maps the GGUF blob read-only, and writes only under ./results/.
The only network access is the optional one-time download of tokenizer.json
from Hugging Face (skipped when --tokenizer-json is given).

Exit codes: 0 PASS, 1 FAIL, 2 ERROR.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import platform
import sys
from typing import Callable

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE.parent / "timing" / "runs"
MANIFEST = HERE / "server_truth_manifest.json"

REPO_ID = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
BOS_TEXT = "<｜begin▁of▁sentence｜>"  # as in the model TEMPLATE
BOS_ID = 100000

# (label, gating, run-file stem). Gating = the four RD-designated measured prompts.
PROMPTS: list[tuple[str, bool, str]] = [
    ("R2#1_pec1752", True, "run-20260929T113401Z/raw/01"),
    ("R2#3_pec3467", True, "run-20260929T113401Z/raw/03"),
    ("R2#6_pec8188", True, "run-20260929T113401Z/raw/06"),
    ("S2b_pec16108", True, "supp16k-coldK-20260929T175204Z/S2"),
    ("R2#0_pec180", False, "run-20260929T113401Z/raw/00"),
    ("R2#5_pec182", False, "run-20260929T113401Z/raw/05"),
    ("S1_pec16108", False, "supp16k-20260929T170742Z/S1"),
]

# Candidate renderings of Ollama's TEMPLATE for a prompt-only /api/generate call.
# Fixed, pre-declared order; the first configuration that matches wins.
RENDERINGS: list[tuple[str, Callable[[str], str]]] = [
    ("messages_branch", lambda p: BOS_TEXT + "User: " + p + "\n\nAssistant:"),
    ("messages_branch_no_bos_text", lambda p: "User: " + p + "\n\nAssistant:"),
    ("else_branch", lambda p: "User: " + p + "Assistant:"),
]
ADD_SPECIAL = (False, True)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ids_sha(ids: list[int]) -> str:
    return sha256_bytes(json.dumps(ids, separators=(",", ":")).encode("ascii"))


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_truth() -> list[dict]:
    out = []
    for label, gating, stem in PROMPTS:
        req = load_json(RUNS / f"{stem}_request.json")
        resp = load_json(RUNS / f"{stem}_response.json")
        prompt = req["prompt"]
        prompt_file = (RUNS / f"{stem}_prompt.txt").read_bytes()
        if prompt.encode("utf-8") != prompt_file:
            raise RuntimeError(f"{label}: request prompt != prompt file bytes")
        ctx = resp["context"]
        n_eval = int(resp["eval_count"])
        L = len(ctx) - n_eval
        server_ids = ctx[:L]
        out.append({
            "label": label,
            "gating": gating,
            "stem": stem,
            "prompt": prompt,
            "prompt_sha256": sha256_bytes(prompt_file),
            "prompt_eval_count": int(resp["prompt_eval_count"]),
            "eval_count": n_eval,
            "context_len": len(ctx),
            "server_prompt_ids": server_ids,
            "server_prompt_len": L,
            "server_prompt_ids_sha256": ids_sha(server_ids),
            "pec_minus_len": int(resp["prompt_eval_count"]) - L,
        })
    return out


def manifest_view(truth: list[dict]) -> list[dict]:
    keep = ("label", "gating", "stem", "prompt_sha256", "prompt_eval_count", "eval_count",
            "context_len", "server_prompt_len", "server_prompt_ids_sha256", "pec_minus_len")
    return [{k: t[k] for k in keep} for t in truth]


def first_diff(a: list[int], b: list[int]) -> int | None:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def get_tokenizer_json(args) -> tuple[pathlib.Path, dict]:
    prov: dict = {"repo_id": REPO_ID}
    if args.tokenizer_json:
        p = pathlib.Path(args.tokenizer_json).resolve()
        prov.update(source="local_file", requested_revision=args.revision)
        return p, prov
    from huggingface_hub import HfApi, hf_hub_download  # network: one-time download
    import huggingface_hub
    sha = HfApi().model_info(REPO_ID, revision=args.revision).sha
    p = pathlib.Path(hf_hub_download(REPO_ID, "tokenizer.json", revision=sha))
    prov.update(source="huggingface_hub", requested_revision=args.revision,
                resolved_commit=sha, huggingface_hub_version=huggingface_hub.__version__)
    return p, prov


def compare_gguf(gguf_path: str, tok_json: dict) -> dict:
    from gguf import GGUFReader
    import gguf
    r = GGUFReader(gguf_path, "r")

    def strs(key: str) -> list[str]:
        f = r.fields[key]
        return [bytes(f.parts[i]).decode("utf-8", errors="surrogateescape") for i in f.data]

    g_tokens = strs("tokenizer.ggml.tokens")
    g_merges = strs("tokenizer.ggml.merges")
    pre = r.fields.get("tokenizer.ggml.pre")
    g_pre = bytes(pre.parts[pre.data[0]]).decode() if pre is not None else None

    hf_id2tok: dict[int, str] = {i: t for t, i in tok_json["model"]["vocab"].items()}
    for a in tok_json.get("added_tokens", []):
        hf_id2tok[int(a["id"])] = a["content"]
    hf_merges = [m if isinstance(m, str) else " ".join(m) for m in tok_json["model"]["merges"]]

    common = [i for i in sorted(hf_id2tok) if i < len(g_tokens)]
    tok_mismatch = [i for i in common if hf_id2tok[i] != g_tokens[i]]
    return {
        "gguf_path": gguf_path,
        "gguf_lib_version": getattr(gguf, "__version__", "unknown"),
        "gguf_pre": g_pre,
        "gguf_n_tokens": len(g_tokens),
        "hf_n_tokens": len(hf_id2tok),
        "hf_ids_missing_in_gguf": len([i for i in hf_id2tok if i >= len(g_tokens)]),
        "gguf_ids_not_in_hf": len([i for i in range(len(g_tokens)) if i not in hf_id2tok]),
        "token_mismatches_on_common_ids": len(tok_mismatch),
        "first_token_mismatches": [(i, hf_id2tok[i], g_tokens[i]) for i in tok_mismatch[:10]],
        "merges_equal": hf_merges == g_merges,
        "hf_n_merges": len(hf_merges),
        "gguf_n_merges": len(g_merges),
        "vocab_equal_on_hf_ids": not tok_mismatch and all(i < len(g_tokens) for i in hf_id2tok),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revision", default="main", help="HF revision to resolve (commit SHA recorded)")
    ap.add_argument("--tokenizer-json", help="use a local tokenizer.json (no network)")
    ap.add_argument("--gguf", help="optional: GGUF blob path for vocab/merges comparison (read-only mmap)")
    ap.add_argument("--build-manifest", action="store_true", help="write server_truth_manifest.json and exit")
    ap.add_argument("--out", default=str(HERE / "results"))
    args = ap.parse_args()

    truth = load_truth()
    if args.build_manifest:
        MANIFEST.write_text(json.dumps({"schema": 1, "prompts": manifest_view(truth)}, indent=2) + "\n",
                            encoding="utf-8")
        print(f"wrote {MANIFEST}")
        return 0

    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["prompts"]
    if manifest_view(truth) != expected:
        print("ERROR: run evidence does not match server_truth_manifest.json", file=sys.stderr)
        return 2

    import tokenizers
    from tokenizers import Tokenizer
    tok_path, prov = get_tokenizer_json(args)
    tok_bytes = tok_path.read_bytes()
    tok_json = json.loads(tok_bytes)
    tok = Tokenizer.from_str(tok_bytes.decode("utf-8"))
    prov.update(tokenizer_json_sha256=sha256_bytes(tok_bytes), tokenizers_version=tokenizers.__version__,
                bos_text_id=tok.token_to_id(BOS_TEXT))

    rows = []
    configs: dict[str, dict] = {}
    for t in truth:
        S = t["server_prompt_ids"]
        for rname, render in RENDERINGS:
            for asp in ADD_SPECIAL:
                key = f"{rname}|add_special_tokens={asp}"
                ids = tok.encode(render(t["prompt"]), add_special_tokens=asp).ids
                fd = first_diff(ids, S)
                rows.append({
                    "label": t["label"], "gating": t["gating"], "config": key,
                    "hf_len": len(ids), "server_prompt_len": t["server_prompt_len"],
                    "prompt_eval_count": t["prompt_eval_count"],
                    "exact_id_match": fd is None, "first_diff_index": fd,
                    "pec_minus_hf_len": t["prompt_eval_count"] - len(ids),
                })
                c = configs.setdefault(key, {"gating_all_exact": True, "offsets": set(), "abs_count_err": []})
                if t["gating"]:
                    c["gating_all_exact"] &= fd is None
                    c["offsets"].add(t["prompt_eval_count"] - len(ids))

    passing = [k for k, c in configs.items() if c["gating_all_exact"] and len(c["offsets"]) == 1]
    chosen = passing[0] if passing else None
    offset = next(iter(configs[chosen]["offsets"])) if chosen else None
    # Count error if the best config were used as a counter (informs margin even on FAIL).
    best_count = {}
    for k, c in configs.items():
        g = [r for r in rows if r["config"] == k and r["gating"]]
        offs = [r["pec_minus_hf_len"] for r in g]
        best_count[k] = {"min_offset": min(offs), "max_offset": max(offs), "spread": max(offs) - min(offs)}

    gguf_result = compare_gguf(args.gguf, tok_json) if args.gguf else None
    verdict = "PASS" if chosen else "FAIL"

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = pathlib.Path(args.out) / f"tokcheck-{ts}"
    out_dir.mkdir(parents=True, exist_ok=False)
    result = {
        "verdict": verdict,
        "rule": "PASS iff one pre-declared config reproduces server prompt token IDs exactly for all 4 "
                "gating prompts AND prompt_eval_count - hf_len is one constant across them",
        "chosen_config": chosen,
        "all_passing_configs": passing,
        "counting_rule": (f"predicted_prompt_eval_count = len(hf_ids) + {offset}" if chosen else None),
        "offset": offset,
        "count_offset_spread_by_config": best_count,
        "provenance": prov,
        "host": {"python": sys.version, "platform": platform.platform()},
        "manifest_sha256": sha256_bytes(MANIFEST.read_bytes()),
        "script_sha256": sha256_bytes(pathlib.Path(__file__).read_bytes()),
        "gguf": gguf_result,
        "rows": rows,
    }
    (out_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"VERDICT: {verdict}   chosen={chosen}   offset={offset}")
    print(f"tokenizer.json sha256={prov['tokenizer_json_sha256']}  commit={prov.get('resolved_commit')}")
    print(f"{'prompt':<14} {'gate':<5} {'pec':>6} {'srv_len':>7} {'hf_len':>6} {'exact':<5} config")
    for r in rows:
        if chosen is None or r["config"] == chosen:
            print(f"{r['label']:<14} {str(r['gating']):<5} {r['prompt_eval_count']:>6} "
                  f"{r['server_prompt_len']:>7} {r['hf_len']:>6} {str(r['exact_id_match']):<5} {r['config']}")
    if gguf_result:
        print("GGUF:", json.dumps({k: v for k, v in gguf_result.items() if k != 'first_token_mismatches'}))
    print(f"result: {out_dir / 'result.json'}")
    return 0 if chosen else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — report and signal ERROR
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
