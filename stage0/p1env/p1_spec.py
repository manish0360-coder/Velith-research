#!/usr/bin/env python3
"""Build one P1 task spec with the frozen M2 probe, applying the OD-5 protected-config rule.

OD-5 (P1 design §14): protected = test_patch files  U  those of {setup.cfg, pyproject.toml,
tox.ini, pytest.ini, root conftest.py, conftest.py in each test file's directory chain} that
EXIST at the task's base commit (checked inside the pinned image, network off).
The probe is imported as a library and run unmodified (fetch-spec CLI path).

Usage: p1_spec.py <instance_id> <image_repo> <digest> <out_spec.json>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

PROBE_DIR = "/mnt/e/Projects/OpenSourceLab/repos/Velith/experiments/m2_container_prototype"
sys.dont_write_bytecode = True  # never write __pycache__ into Velith main
sys.path.insert(0, PROBE_DIR)
import probe  # noqa: E402  (frozen probe, unmodified)

REPO_DIR = "/testbed"
PYTHON = "/opt/miniconda3/envs/testbed/bin/python"
ROOT_CONFIG = ("setup.cfg", "pyproject.toml", "tox.ini", "pytest.ini", "conftest.py")


def main() -> int:
    instance, image, digest, out = sys.argv[1:5]
    ref = f"{image}@{digest}"
    row = probe.fetch_row("SWE-bench/SWE-bench_Verified", instance)
    base = str(row["base_commit"])
    test_files = probe.patch_files(str(row["test_patch"]))
    candidates = set(ROOT_CONFIG)
    for test_file in test_files:
        for parent in PurePosixPath(test_file).parents:
            if str(parent) != ".":
                candidates.add(f"{parent}/conftest.py")
    check = " ".join(sorted(candidates))
    script = (
        f"cd {REPO_DIR} && test -x {PYTHON} || exit 97; "
        f'git rev-parse --verify -q "{base}^{{commit}}" >/dev/null || exit 96; '
        f'for p in {check}; do git ls-tree --name-only "{base}" -- "$p" || exit 98; done'
    )
    proc = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "bash", ref, "-c", script],
        capture_output=True, text=True, timeout=300, check=False,
    )
    if proc.returncode not in (0, 1):
        print(f"inspection failed (exit {proc.returncode}): {proc.stderr.strip()}", file=sys.stderr)
        return 2
    existing = sorted(line.strip() for line in proc.stdout.splitlines() if line.strip())
    print(f"base_commit={base}; test files={test_files}; existing protected-config={existing}")
    args = ["fetch-spec", "--instance", instance, "--out", out, "--image", image,
            "--digest", digest, "--platform", "linux/amd64", "--repo-dir", REPO_DIR,
            "--python", PYTHON]
    for path in existing:
        args += ["--protected-config", path]
    return probe.main(args)


if __name__ == "__main__":
    sys.exit(main())
