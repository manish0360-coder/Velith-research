"""P3 extraction script. Runs INSIDE velith-verifier:m0 with --network none.

Applies the frozen Velith `_extract_patch` (velith/agent/proposer.py, SHA-pinned) to one
completion, so P3 uses exactly the extraction Velith and P2 used. Called, never modified.

stdin : {"completion": str, "expected_proposer_sha256": str}
stdout: one line "P3EXTRACT_RESULT {json}"
"""
import hashlib
import json
import sys
from pathlib import Path


def main():
    req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    import velith.agent.proposer as proposer

    got = hashlib.sha256(Path(proposer.__file__).read_bytes()).hexdigest()
    out = {"proposer_sha256": got}
    if got != req["expected_proposer_sha256"]:
        out["status"] = "MODULE_MISMATCH"
    else:
        patch = proposer._extract_patch(req["completion"])
        has_patch = proposer.Proposal(patch=patch, prompt="", prompt_tokens=0,
                                      completion_tokens=0, latency_seconds=0.0, model="",
                                      model_version="").has_patch  # the frozen property
        out.update(status="OK", patch=patch, has_patch=has_patch)
    sys.stdout.write("P3EXTRACT_RESULT " + json.dumps(out, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
