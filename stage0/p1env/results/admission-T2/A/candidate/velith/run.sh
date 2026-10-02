cd /testbed || exit 96
BASE=8f0003ae902952372824c9917975fb372c026a42
echo "VELITH_HEAD $(git rev-parse HEAD)"
echo "VELITH_PARENT $(git rev-parse HEAD^1)"
[ "$(git rev-parse HEAD^1)" = "$BASE" ] || exit 90
[ -z "$(git status --porcelain)" ] || exit 91

if [ -s /tmp/velith/candidate.patch ]; then
  git apply /tmp/velith/candidate.patch || exit 92
fi

for p in lib/matplotlib/tests/conftest.py lib/matplotlib/tests/test_offsetbox.py pyproject.toml pytest.ini setup.cfg tox.ini; do
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
for p in lib/matplotlib/tests/conftest.py lib/matplotlib/tests/test_offsetbox.py pyproject.toml pytest.ini setup.cfg tox.ini; do
  if [ -e "$p" ]; then
    echo "VELITH_SURFACE $(sha256sum -- "$p")"
  else
    echo "VELITH_SURFACE absent $p"
  fi
done
export PATH="/opt/miniconda3/envs/testbed/bin:$PATH"
/opt/miniconda3/envs/testbed/bin/python -m pytest -rA --junitxml=/tmp/velith-junit.xml lib/matplotlib/tests/test_offsetbox.py
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
