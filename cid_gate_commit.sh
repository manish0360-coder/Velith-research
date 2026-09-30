#!/usr/bin/env bash
# C-ID gate + single commit (M8 evaluation identity v2 / M9 VM2 / M10 reconstruction).
# Fail-closed: aborts on the first failed check. NO tag, NO push.
set -euo pipefail
cd /mnt/e/Projects/OpenSourceLab/repos/Velith

BASE=1b0b7a09a41299ade38027cd17215fa42c2a7b09
PATHS=(src/velith/analysis/binder.py src/velith/analysis/executor.py src/velith/analysis/preregistration.py src/velith/evaluation/provenance.py src/velith/evaluation/runner.py src/velith/evaluation/verification_manifest.py src/velith/taskspec/__init__.py src/velith/taskspec/store.py tests/fixtures/corpus_min/corpus.json tests/fixtures/taskspecs/3565badc1bb9378038cba6716343f5657d5fdea8bb083da61d622d12dbba78cc tests/fixtures/taskspecs/65d6c4be5e99b7b85d9d41eadf840e003767d3516824ff07befcab612956af4f tests/fixtures/taskspecs/e0ae04e721b29007ecfb606ce5d7e569e42399c1f72a5d2ec2b2ad273fbaf20b tests/integration/test_m10_heldout_execution.py tests/integration/test_m8_heldout_evaluation.py tests/integration/test_m9_analysis_pipeline.py tests/unit/test_analysis_binder.py tests/unit/test_analysis_executor.py tests/unit/test_analysis_prereg_store.py tests/unit/test_analysis_preregistration.py tests/unit/test_analysis_result_record.py tests/unit/test_evaluation_heldout_safety_invariant.py tests/unit/test_evaluation_provenance.py tests/unit/test_evaluation_runner.py tests/unit/test_identity_v2_acceptance.py tests/unit/test_m9_statistics_unchanged.py tests/unit/test_verification_manifest.py)
PROTECTED=(docs src/velith/analysis/completeness.py src/velith/analysis/decision.py src/velith/analysis/emm.py
  src/velith/analysis/encoding.py src/velith/analysis/gee.py src/velith/analysis/holm.py src/velith/analysis/mcnemar.py
  src/velith/analysis/trend.py src/velith/analysis/wald.py src/velith/analysis/result_record.py
  src/velith/analysis/prereg_store.py src/velith/harness src/velith/task.py src/velith/corpus src/velith/batch
  src/velith/retrieval src/velith/arms src/velith/episodes src/velith/agent src/velith/llm src/velith/runner
  src/velith/core src/velith/evaluation/attempt.py src/velith/evaluation/checkpoint.py src/velith/evaluation/context.py
  src/velith/evaluation/heldout_set.py src/velith/evaluation/record.py src/velith/evaluation/sink.py
  docker docker-compose.yml pyproject.toml constraints experiments .github README.md)
FROZEN_DOCS="47cc1e1c0ae31da0ce7497eef041ece93d89f02d4e1df02e0f2fcaa42b383706  docs/DECISIONS.md
746be5770993b51ad22f71a217f3108aeeab910d73f288dcf811132df4f5285a  docs/M8_IDENTITY_V2_SPEC.md
94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e  docs/M9_SPEC.md
9ddd16d881d7a6123897859ede95d719a8c123ba06b9a6c5337e41bd5db1c093  docs/M8_SPEC.md"
CHANGESET="293ca3ae2c1bc3be22a3cde2a9acdacb45a8e010ca530d6b6f0e6977deb51bcd  src/velith/analysis/binder.py
72ea5f67b006c1ba2e66b8d7c0a55c86bff1ac58a0fbd42f5bdaa43f134fc9e5  src/velith/analysis/executor.py
57cdcaccb236d92b1406d2e29ec193b506692858ba34b2941b0907a606dd9741  src/velith/analysis/preregistration.py
fe619205b61f96ef1dc18176cf0203f605f6786d5df20b77cd004ca416ee8874  src/velith/evaluation/provenance.py
415b972cb5d2e919b6ab6730689d75e531096d0d028abb2e72362723fc9e7a6d  src/velith/evaluation/runner.py
ad3a2357a48664cd29df59ebfc14532938b2805aa441c17e372816255c06ff00  src/velith/evaluation/verification_manifest.py
3ce447e58ccc7b27fe094648fc658959d67a9a56abe7f38ca3e3ba63cfbefe5c  src/velith/taskspec/__init__.py
f8d8f3b495896e4efc89c31efa173823210c97e1e9e9b7ee92105ca3a3262a4d  src/velith/taskspec/store.py
d8727baccdf5c3d7e579ea59605e5732200689a85e4c54fb9d7fd6284ad5f2b6  tests/fixtures/corpus_min/corpus.json
3565badc1bb9378038cba6716343f5657d5fdea8bb083da61d622d12dbba78cc  tests/fixtures/taskspecs/3565badc1bb9378038cba6716343f5657d5fdea8bb083da61d622d12dbba78cc
65d6c4be5e99b7b85d9d41eadf840e003767d3516824ff07befcab612956af4f  tests/fixtures/taskspecs/65d6c4be5e99b7b85d9d41eadf840e003767d3516824ff07befcab612956af4f
e0ae04e721b29007ecfb606ce5d7e569e42399c1f72a5d2ec2b2ad273fbaf20b  tests/fixtures/taskspecs/e0ae04e721b29007ecfb606ce5d7e569e42399c1f72a5d2ec2b2ad273fbaf20b
e61dc4313aabe1dacda962ab28240c718ce68056a7506707b1b9cb03783be46d  tests/integration/test_m10_heldout_execution.py
353dab0f318a2caf79d7a5c67fc10fe19a0a27d6e45e179e2ffbbd05f3091199  tests/integration/test_m8_heldout_evaluation.py
4cdf9e8897ae6cd0d7132e3055ae81bea5648620e38d9d45150130189b120f3d  tests/integration/test_m9_analysis_pipeline.py
46c5c64c4edd569ef9732a7a4853b0d512c46ca59b7357c801e42470f287d413  tests/unit/test_analysis_binder.py
21228a99122b594c782b3212493c8e0a3c0454bd88f26fa3717e4aa2ac373367  tests/unit/test_analysis_executor.py
058935c620497dc07ef6b85dd37c2f0d65bc144b3a52fd1f3ad59f3a28dd3ed5  tests/unit/test_analysis_prereg_store.py
1e3c5bb0e0893da0142001eb9feb5a70a67cefb0217627ea231bd30746a931e2  tests/unit/test_analysis_preregistration.py
b578fbfb9e2d1b2164d5e60368ff8ddac32faaacaec4714885d3b297c7d76872  tests/unit/test_analysis_result_record.py
6ae536e8d1d243e99316520019cc16fd39c9ad0eb2f1e27de154f36fa21830fe  tests/unit/test_evaluation_heldout_safety_invariant.py
c10df05048809f7000e399361a2e8e7793cfe3c437cfaa7467aac973c35cc113  tests/unit/test_evaluation_provenance.py
d7c700ddffbe5c19f01922ed912f01fd3f07251c9f8c542f77da306bdc9d3584  tests/unit/test_evaluation_runner.py
02f824745fa5175cbd4c350d7db48b68e41fc9d4fe3f6474b6b086b81eb03bb6  tests/unit/test_identity_v2_acceptance.py
9c9a6d643402afbeeed4fa3054856608034a1191f5b25ce598596170e9db67b5  tests/unit/test_m9_statistics_unchanged.py
3c82198dde5868459185526c543614f62bcc467eed3f5b395f57548bfb51beed  tests/unit/test_verification_manifest.py"
SUBJ="feat(m8-m9): implement evaluation identity v2"
BODY="Implement the frozen identity-v2 migration (D29; docs/M8_IDENTITY_V2_SPEC.md;
docs/M9_SPEC.md Amendment VM2) as one coordinated M8/M9/M10 change:
- EvaluationProvenance v2: identity_version and verification_manifest_hash (10-key payload)
- held-out VerificationManifest builder (fail-closed) and a schema-agnostic
  content-addressed TaskSpec byte store (no TaskSpec schema)
- M8 runner pre-attempt identity_version and verification-manifest check
- M9 PreRegistration: SPEC_VERSION m9-spec-frozen-oed7-vm2 and verification_manifest_hash
- M10: both provenance reconstruction sites build v2; pre-flight rejects v1 lineage
- universal v2 fixture path; 18 identity acceptance cases; statistics byte-identity test
M9 statistical modules byte-identical. No production verifier, real-task execution or pilot."

step() { printf '\n== %s\n' "$*"; }

step "0 baseline"
test "$(git rev-parse HEAD)" = "$BASE"
echo "HEAD ok"

step "1 exact working tree: 26 declared paths, pinned SHA-256"
test "$(git status --porcelain --untracked-files=all | cut -c4- | sort)" = "$(printf '%s\n' "${PATHS[@]}" | sort)"
echo "$CHANGESET" | sha256sum -c --quiet && echo "all 26 change-set hashes match"

step "2 frozen documents, statistics modules and protected paths"
echo "$FROZEN_DOCS" | sha256sum -c --quiet && echo "frozen documents match"
git diff --quiet HEAD -- "${PROTECTED[@]}"
test -z "$(git ls-files --others --exclude-standard -- "${PROTECTED[@]}")"
echo "protected paths byte-identical (incl. the nine M9 statistics modules)"

step "3 no-cache container build (pinned Python 3.12 / constraints)"
docker compose build --no-cache verifier </dev/null

step "4 Ruff 0.6.9, format, mypy"
docker compose run --rm -T verifier ruff --version </dev/null
docker compose run --rm -T verifier ruff check . </dev/null
docker compose run --rm -T verifier ruff format --check . </dev/null
docker compose run --rm -T verifier mypy src tests </dev/null

step "5 identity-v2 / VM / statistics-identity tests (verbose)"
docker compose run --rm -T verifier pytest -v tests/unit/test_identity_v2_acceptance.py \
  tests/unit/test_verification_manifest.py tests/unit/test_m9_statistics_unchanged.py \
  tests/unit/test_evaluation_provenance.py </dev/null

step "6 full pytest"
docker compose run --rm -T verifier pytest -q </dev/null

step "7 stage exactly the declared paths"
git add -- "${PATHS[@]}"
test "$(git diff --cached --name-only | sort)" = "$(printf '%s\n' "${PATHS[@]}" | sort)"
git diff --cached --check
git --no-pager diff --cached --stat

step "8 ONE commit (no tag, no push)"
git commit -q -m "$SUBJ" -m "$BODY" </dev/null
C=$(git rev-parse HEAD)

step "9 post-commit verification"
test "$(git rev-parse "$C^")" = "$BASE"
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git show --name-only --format= "$C" | sed '/^$/d' | sort)" = "$(printf '%s\n' "${PATHS[@]}" | sort)"
git diff --quiet "$BASE" "$C" -- "${PROTECTED[@]}"
echo "$FROZEN_DOCS" | sha256sum -c --quiet
echo "commit: $C"
git log -1 --format='subject: %s'
echo "NOT tagged. NOT pushed. C-ID IMPLEMENTED AND VERIFIED (pending your review)."
