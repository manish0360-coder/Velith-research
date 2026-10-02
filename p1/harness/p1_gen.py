"""P1 Stage G script. Runs INSIDE velith-verifier:m0 (R6), started by p1_harness.py as
`docker run --rm -i --read-only ... --entrypoint python <image-id> -c <this file>`.

stdin : one JSON request (mode, prompt, identity, seed, model, model_digest, host, timeout,
        expected_module_sha256).
stdout: Velith log lines, plus marker lines "P1GEN_SENT", "P1GEN_COMPLETION", "P1GEN_RESULT"
        followed by one JSON object each. Writes no file.

Modes: check    - module hashes, seed, Task construction; no network (harness uses --network none)
       ps       - check + GET /api/ps
       generate - check + /api/version, /api/tags digest, /api/ps (cold rule) + ONE generate call

Generation semantics are exactly ProposerAgent.propose (velith/agent/proposer.py, pinned by
hash): Proposal(patch=_extract_patch(completion.text), ...) from the frozen OllamaClient. The
frozen client and frozen functions are called, never modified, wrapped or monkeypatched; the
propose() body is composed here only so the raw completion text (P1 §13/§19) is retained.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path


def emit(key, obj):
    sys.stdout.write(key + " " + json.dumps(obj, sort_keys=True) + "\n")
    sys.stdout.flush()


def get(host, path):
    with urllib.request.urlopen(host + path, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    mode = req["mode"]
    out = {"mode": mode, "python": sys.version.split()[0]}
    import velith.agent.proposer as proposer
    import velith.batch.provenance as provenance
    import velith.llm.client as client
    import velith.task as task_mod

    mods = {"velith/agent/proposer.py": proposer, "velith/llm/client.py": client,
            "velith/task.py": task_mod, "velith/batch/provenance.py": provenance}
    out["module_files"] = {k: m.__file__ for k, m in mods.items()}
    out["module_sha256"] = {k: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                            for k, m in mods.items()}
    if out["module_sha256"] != req["expected_module_sha256"]:
        out["status"] = "MODULE_MISMATCH"
        return emit("P1GEN_RESULT", out)
    seed = provenance.derive_task_seed(req["identity"], 0)
    if seed != req["seed"]:
        out.update(status="SEED_MISMATCH", seed_in_container=seed)
        return emit("P1GEN_RESULT", out)
    task = task_mod.Task(task_id=req["instance_id"], repo_path=Path("/nonexistent/p1-no-repo"),
                         prompt=req["prompt"], hidden_test_command=("false",))
    if hashlib.sha256(task.prompt.encode("utf-8")).hexdigest() != req["identity"]:
        out["status"] = "PROMPT_MISMATCH"
        return emit("P1GEN_RESULT", out)
    if mode == "check":
        out["status"] = "CHECK_OK"
        return emit("P1GEN_RESULT", out)
    host = req["host"]
    try:
        out["ps"] = get(host, "/api/ps")
        if mode == "ps":
            out["status"] = "PS_OK"
            return emit("P1GEN_RESULT", out)
        out["version"] = get(host, "/api/version")
        tags = get(host, "/api/tags")
    except (OSError, ValueError) as exc:
        out.update(status="OLLAMA_UNREACHABLE", error=str(exc))
        return emit("P1GEN_RESULT", out)
    entry = [m for m in tags.get("models", []) if req["model"] in (m.get("name"), m.get("model"))]
    out["tags_entry"] = entry
    if len(entry) != 1 or entry[0].get("digest") != req["model_digest"]:
        out["status"] = "DIGEST_MISMATCH"
        return emit("P1GEN_RESULT", out)
    if any(req["model"] in (m.get("name"), m.get("model")) for m in out["ps"].get("models", [])):
        out["status"] = "MODEL_ALREADY_LOADED"  # cold-start rule: no cached prefix
        return emit("P1GEN_RESULT", out)

    ollama = client.OllamaClient(host=host, timeout_seconds=float(req["timeout"]))
    emit("P1GEN_SENT", {"model": req["model"], "seed": seed, "temperature": 0.0})
    try:
        completion = ollama.generate(prompt=task.prompt, model=req["model"], seed=seed,
                                     temperature=0.0)
    except client.ModelUnavailableError as exc:
        out.update(status="MODEL_UNAVAILABLE", error=str(exc),
                   error_is_timeout="timed out" in str(exc).lower())
        return emit("P1GEN_RESULT", out)
    proposal = proposer.Proposal(
        patch=proposer._extract_patch(completion.text),
        prompt=task.prompt,
        prompt_tokens=completion.prompt_tokens,
        completion_tokens=completion.completion_tokens,
        latency_seconds=completion.latency_seconds,
        model=completion.model,
        model_version=completion.model_version,
    )
    out.update(status="GENERATED", completion_text=completion.text, patch=proposal.patch,
               has_patch=proposal.has_patch, prompt_tokens=proposal.prompt_tokens,
               completion_tokens=proposal.completion_tokens,
               latency_seconds=proposal.latency_seconds, model=proposal.model,
               model_version=proposal.model_version, seed=seed, temperature=0.0)
    emit("P1GEN_COMPLETION", out)  # persisted by the harness even if anything below fails
    try:
        out["ps_after"] = get(host, "/api/ps")
    except (OSError, ValueError) as exc:
        out["ps_after_error"] = str(exc)
    return emit("P1GEN_RESULT", out)


if __name__ == "__main__":
    main()
