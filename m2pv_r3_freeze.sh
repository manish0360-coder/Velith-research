#!/usr/bin/env bash
# M2-PV-R3 governance freeze: gate 18 (no-cache container gate) -> ONE docs-only commit ->
# two annotated tags on that commit -> push -> remote verification.
# Fail-closed: any failing check aborts. Nothing is committed unless every gate passes.
set -euo pipefail
cd /mnt/e/Projects/OpenSourceLab/repos/Velith

BASE=b14d918f14d4b5bdfab6fb916811320a742eafa3
SHA_DEC=47cc1e1c0ae31da0ce7497eef041ece93d89f02d4e1df02e0f2fcaa42b383706
SHA_M8V2=746be5770993b51ad22f71a217f3108aeeab910d73f288dcf811132df4f5285a
SHA_M9=94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e
SHA_M8V1=9ddd16d881d7a6123897859ede95d719a8c123ba06b9a6c5337e41bd5db1c093
T8=m8-identity-v2-frozen
T9=m9-spec-frozen-oed7-vm2
PATHS=(docs/DECISIONS.md docs/M8_IDENTITY_V2_SPEC.md docs/M9_SPEC.md)
UNTOUCHED=(docs/M8_SPEC.md src tests docker docker-compose.yml pyproject.toml constraints experiments .github)
SUBJ="docs(governance): freeze M8 identity v2 and M9 VM2"
BODY="Enter ratified D26, D27, D28 (M2-PV-R) and D29 (M8 evaluation identity v2) into
docs/DECISIONS.md. Add docs/M8_IDENTITY_V2_SPEC.md, the successor to the M8 v1
evaluation identity (docs/M8_SPEC.md unchanged). Insert M9 Amendment VM2 after
OED-7 and re-freeze M9 (SPEC_VERSION m9-spec-frozen-oed7-vm2); M9 statistical
procedure unchanged. This commit is the freeze event. Docs-only: no source,
test, schema or implementation change. Source specification: M2-PV-R3
(d2c51ec15aa00f1c5924ea6aaed8e6de3f7ba286bfc27b5860b5d792b375888a)."

step() { printf '\n== %s\n' "$*"; }
sha() { sha256sum "$1" | cut -d' ' -f1; }

step "0 baseline: local and remote at b14d918, tags absent"
test "$(git rev-parse HEAD)" = "$BASE"
git fetch origin --quiet </dev/null
test "$(git rev-parse origin/main)" = "$BASE"
for t in "$T8" "$T9"; do
  if git rev-parse -q --verify "refs/tags/$t" >/dev/null; then echo "ABORT: tag $t already exists locally"; exit 1; fi
done
test -z "$(git ls-remote --tags origin "$T8" "$T9" </dev/null)"
echo "ok"

step "1 exact working tree (three paths, pinned hashes, everything else untouched)"
test "$(git status --porcelain --untracked-files=all | sort)" = "$(printf ' M docs/DECISIONS.md\n M docs/M9_SPEC.md\n?? docs/M8_IDENTITY_V2_SPEC.md\n' | sort)"
test "$(sha docs/DECISIONS.md)" = "$SHA_DEC"
test "$(sha docs/M8_IDENTITY_V2_SPEC.md)" = "$SHA_M8V2"
test "$(sha docs/M9_SPEC.md)" = "$SHA_M9"
test "$(sha docs/M8_SPEC.md)" = "$SHA_M8V1"
git diff --quiet HEAD -- "${UNTOUCHED[@]}"
echo "ok"

step "2 gate 18: no-cache container gate (pinned toolchain)"
docker compose build --no-cache verifier </dev/null
docker compose run --rm -T verifier ruff --version </dev/null
docker compose run --rm -T verifier ruff check . </dev/null
docker compose run --rm -T verifier ruff format --check . </dev/null
docker compose run --rm -T verifier mypy src tests </dev/null
docker compose run --rm -T verifier pytest -q </dev/null

step "3 gate 19: final diff before commit"
git add -N docs/M8_IDENTITY_V2_SPEC.md
git --no-pager diff --stat
git reset -q -- docs/M8_IDENTITY_V2_SPEC.md

step "4 stage exactly three paths"
git add -- "${PATHS[@]}"
test "$(git diff --cached --name-only | sort)" = "$(printf '%s\n' "${PATHS[@]}" | sort)"
git diff --cached --check
test "$(git show :docs/DECISIONS.md | sha256sum | cut -d' ' -f1)" = "$SHA_DEC"
test "$(git show :docs/M8_IDENTITY_V2_SPEC.md | sha256sum | cut -d' ' -f1)" = "$SHA_M8V2"
test "$(git show :docs/M9_SPEC.md | sha256sum | cut -d' ' -f1)" = "$SHA_M9"
echo "ok"

step "5 ONE docs-only governance commit"
git commit -q -m "$SUBJ" -m "$BODY" </dev/null
C=$(git rev-parse HEAD)
echo "commit: $C"

step "6 tags on the governance commit"
git tag -a "$T8" -m "M8 evaluation identity v2 frozen (D29; docs/M8_IDENTITY_V2_SPEC.md)" "$C"
git tag -a "$T9" -m "M9 specification re-frozen after the VM2 amendment (SPEC_VERSION m9-spec-frozen-oed7-vm2)" "$C"
test "$(git rev-parse "$T8^{commit}")" = "$C"
test "$(git rev-parse "$T9^{commit}")" = "$C"
echo "ok"

step "7 post-commit verification"
test "$(git rev-parse HEAD)" = "$C"
test "$(git rev-parse "$C^")" = "$BASE"
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git show --name-only --format= "$C" | sed '/^$/d' | sort)" = "$(printf '%s\n' "${PATHS[@]}" | sort)"
git diff --quiet "$BASE" "$C" -- "${UNTOUCHED[@]}"
test "$(sha docs/M8_SPEC.md)" = "$SHA_M8V1"
for p in "${PATHS[@]}"; do printf '%s  %s\n' "$(git show "$C:$p" | sha256sum | cut -d' ' -f1)" "$p"; done
echo "ok"

step "8 push commit, then both tags"
git push origin main </dev/null
git push origin "$T8" "$T9" </dev/null

step "9 remote verification"
test "$(git ls-remote origin refs/heads/main </dev/null | cut -f1)" = "$C"
test "$(git ls-remote origin "refs/tags/$T8^{}" </dev/null | cut -f1)" = "$C"
test "$(git ls-remote origin "refs/tags/$T9^{}" </dev/null | cut -f1)" = "$C"
git fetch origin --quiet </dev/null
test "$(git rev-parse origin/main)" = "$C"

step "REPORT"
echo "commit:  $C"
git log -1 --format='subject: %s' "$C"
echo "$T8 -> $(git rev-parse "$T8^{commit}")"
echo "$T9 -> $(git rev-parse "$T9^{commit}")"
echo "remote main -> $(git ls-remote origin refs/heads/main </dev/null | cut -f1)"
git status --short; echo "(working tree clean)"
echo "DONE. Next: implementation-handoff authorization (not started)."
