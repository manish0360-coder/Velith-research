cd /testbed || exit 96
BASE=41fef6f1352be994cd90056d47440fe9aa4c068f
echo "VELITH_HEAD $(git rev-parse HEAD)"
echo "VELITH_PARENT $(git rev-parse HEAD^1)"
[ "$(git rev-parse HEAD^1)" = "$BASE" ] || exit 90
[ -z "$(git status --porcelain)" ] || exit 91

if [ -s /tmp/velith/candidate.patch ]; then
  git apply /tmp/velith/candidate.patch || exit 92
fi

for p in conftest.py pyproject.toml setup.cfg xarray/tests/conftest.py xarray/tests/test_indexes.py; do
  if git cat-file -e "$BASE:$p" 2>/dev/null; then
    git checkout -q "$BASE" -- "$p" || exit 98
  else
    rm -f -- "$p"
  fi
done
git ls-files --others -z | while IFS= read -r -d '' f; do
  case "${f##*/}" in
    conftest.py|pytest.ini|.pytest.ini|setup.cfg|tox.ini|pyproject.toml)
      rm -f -- "$f"
      echo "VELITH_REMOVED $f"
      ;;
  esac
done
git apply /tmp/velith/test.patch || exit 93
for p in conftest.py pyproject.toml setup.cfg xarray/tests/conftest.py xarray/tests/test_indexes.py; do
  if [ -e "$p" ]; then
    echo "VELITH_SURFACE $(sha256sum -- "$p")"
  else
    echo "VELITH_SURFACE absent $p"
  fi
done
export PATH="/opt/miniconda3/envs/testbed/bin:$PATH"
/opt/miniconda3/envs/testbed/bin/python -m pytest -rA --junitxml=/tmp/velith-junit.xml xarray/tests/test_indexes.py
echo "VELITH_PYTEST_EXIT $?"
/opt/miniconda3/envs/testbed/bin/python - <<'PY'
import socket
try:
    socket.create_connection(("1.1.1.1", 53), timeout=3).close()
    print("VELITH_NET connected")
except OSError as exc:
    print("VELITH_NET blocked", type(exc).__name__, exc.errno)
PY
exit 0
