#!/usr/bin/env bash
# M2 feasibility commit gate. Fail-closed: any failing step aborts before the commit.
# Runs the project's pinned containerized gates (Ruff 0.6.9 from pyproject), re-verifies
# the staged two-file boundary and content hashes, then creates exactly one commit.
# Never pushes.
set -euo pipefail
cd /mnt/e/Projects/OpenSourceLab/repos/Velith

P=experiments/m2_container_prototype/probe.py
F=experiments/m2_container_prototype/FREEZE_RECORD.md
P_SHA=560834d559fbf1063c7ad33afa675abac59535e45469bc0d9da3e8254f138e1f
F_SHA=eef4c3e06faeeb1cdff41f49f4f32d9c20229109854fdcf8cfd61b0612b63007
EXPECTED_HEAD=e04d7f90a742a3c6278a2fd937803abdd1567ac8
MSG="experiment(m2): add container verifier feasibility probe and freeze record"

step() { printf '\n== %s\n' "$*"; }

step "0 preconditions"
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"
echo "HEAD ok: $EXPECTED_HEAD"

step "1 no-cache image build"
docker compose build --no-cache verifier </dev/null

step "2 containerized gates (CI sequence)"
docker compose run --rm -T verifier ruff --version </dev/null
docker compose run --rm -T verifier ruff check . </dev/null
docker compose run --rm -T verifier ruff format --check . </dev/null
docker compose run --rm -T verifier mypy src tests </dev/null
docker compose run --rm -T verifier pytest -q </dev/null

step "3 staged boundary (exactly two files)"
git diff --cached --name-only
test "$(git diff --cached --name-only)" = "$(printf '%s\n%s' "$F" "$P")"

step "4 staged content integrity"
test "$(git show ":$P" | sha256sum | cut -d' ' -f1)" = "$P_SHA" && echo "probe.py  $P_SHA"
test "$(git show ":$F" | sha256sum | cut -d' ' -f1)" = "$F_SHA" && echo "FREEZE_RECORD.md  $F_SHA"

step "5 git diff --cached --check"
git diff --cached --check && echo "rc=0"

step "6 nothing else modified, staged or untracked"
test -z "$(git diff --name-only)"
test -z "$(git ls-files --others --exclude-standard)"
echo "clean outside the two staged files"

step "7 commit"
git commit -m "$MSG" </dev/null

step "8 post-commit report"
echo "commit: $(git rev-parse HEAD)"
git log -1 --format='HEAD: %H %s'
git show --stat --format= HEAD
echo "status:"; git status --porcelain --untracked-files=all; echo "(end status)"
echo "NOT pushed."
