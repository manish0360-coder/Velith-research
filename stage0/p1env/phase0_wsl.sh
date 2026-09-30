#!/usr/bin/env bash
# OD-ENV Phase 0, WSL side. READ-ONLY baseline.
# - It pulls nothing (every docker run / compose run uses --pull never; STOP if an image is missing).
# - It does not build, prune, compact, move, or modify Velith main (git status is checked before and after).
# - Its only side effects are throw-away containers (--rm) and, if absent, Compose's default project network.
# - Container env/config is NOT recorded (it may hold secrets); only names, images, states and mounts are.
# Output: stage0/p1env/results/phase0-wsl-<UTC>/
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/results/phase0-wsl-$(date -u +%Y%m%dT%H%M%SZ)"
VELITH="${VELITH:-/mnt/e/Projects/OpenSourceLab/repos/Velith}"
PROBE_IMG="python:3.12-slim"
VELITH_IMG="velith-verifier:m0"
mkdir -p "$OUT/velith" "$OUT/volumes" "$OUT/inventory"

for img in "$PROBE_IMG" "$VELITH_IMG"; do
  docker image inspect "$img" >/dev/null 2>&1 || { echo "STOP: $img not present locally (no pulls allowed)"; exit 2; }
done

# ---- pre-state
git -C "$VELITH" --no-optional-locks rev-parse HEAD >"$OUT/velith/git_head.txt"
git -C "$VELITH" --no-optional-locks status --porcelain >"$OUT/velith/git_status_pre.txt"
docker network ls --no-trunc --format '{{json .}}' >"$OUT/inventory/networks_pre.jsonl"
docker image inspect "$VELITH_IMG" --format '{{.Id}} {{.Created}}' >"$OUT/velith/image_id.txt"

# ---- 1. Velith main checks on the EXISTING image, with no build and no pull
cd "$VELITH" || exit 2
i=0
while IFS= read -r step; do
  i=$((i+1)); f="$OUT/velith/$(printf '%02d' $i).txt"
  echo "\$ docker compose run --rm -T --pull never --no-deps verifier $step" >"$f"
  # shellcheck disable=SC2086
  docker compose run --rm -T --pull never --no-deps verifier $step </dev/null >>"$f" 2>&1
  echo "[exit $?]" >>"$f"
done <<'STEPS'
ruff --version
ruff check .
ruff format --check .
mypy src tests
pytest -q -rs
STEPS
cd "$HERE" || exit 2
git -C "$VELITH" --no-optional-locks status --porcelain >"$OUT/velith/git_status_post.txt"

# ---- 2/3. Docker usage: engine view and filesystem view
docker info --format '{{json .}}' >"$OUT/inventory/docker_info.json" 2>&1
docker system df >"$OUT/system_df.txt" 2>&1
docker system df -v >"$OUT/system_df_v.txt" 2>&1
docker buildx du >"$OUT/buildx_du.txt" 2>&1
docker buildx du --verbose >"$OUT/buildx_du_verbose.txt" 2>&1
docker run --rm --pull never --network none --entrypoint df "$PROBE_IMG" -B1 / >"$OUT/internal_df.txt" 2>&1

# ---- 5/6. Inventory (identities, no container env)
docker image ls -a --digests --no-trunc --format '{{json .}}' >"$OUT/inventory/images.jsonl"
docker image ls -a -q --no-trunc | sort -u | xargs -r docker image inspect \
  --format '{{.Id}}|{{json .RepoTags}}|{{json .RepoDigests}}|{{.Created}}|{{.Size}}|{{.Os}}/{{.Architecture}}' \
  >"$OUT/inventory/images_inspect.psv" 2>"$OUT/inventory/images_inspect.err"
docker ps -a --no-trunc --format '{{json .}}' >"$OUT/inventory/containers.jsonl"
docker ps -aq --no-trunc | xargs -r docker inspect \
  --format '{{.Id}}|{{.Name}}|{{.Image}}|{{.State.Status}}|{{json .Mounts}}' \
  >"$OUT/inventory/containers_inspect.psv" 2>&1
docker volume ls --format '{{json .}}' >"$OUT/inventory/volumes.jsonl"
docker volume ls -q | xargs -r docker volume inspect >"$OUT/inventory/volumes_inspect.json" 2>&1
docker network ls --no-trunc --format '{{json .}}' >"$OUT/inventory/networks_post.jsonl"
docker buildx ls >"$OUT/inventory/buildx_ls.txt" 2>&1
docker context ls --format '{{json .}}' >"$OUT/inventory/contexts.jsonl" 2>&1

# ---- 6. Volume content metadata (read-only mounts; live volumes are flagged)
HASHER='
import hashlib, json, os, stat
root = "/v"; lines = []; n_f = n_d = n_l = n_o = 0; total = 0; errors = []
for dp, dns, fns in os.walk(root, followlinks=False):
    dns.sort()
    for name in sorted(fns) + [d for d in dns if os.path.islink(os.path.join(dp, d))]:
        p = os.path.join(dp, name); rel = os.path.relpath(p, root)
        try:
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                n_l += 1; lines.append(f"L\t{rel}\t{os.readlink(p)}")
            elif stat.S_ISREG(st.st_mode):
                h = hashlib.sha256()
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
                n_f += 1; total += st.st_size
                lines.append(f"F\t{rel}\t{oct(st.st_mode & 0o7777)}\t{st.st_uid}:{st.st_gid}\t{st.st_size}\t{h.hexdigest()}")
            else:
                n_o += 1; lines.append(f"O\t{rel}\t{oct(st.st_mode)}")
        except OSError as e:
            errors.append(f"{rel}: {e}")
    n_d += len(dns)
tree = hashlib.sha256("\n".join(lines).encode("utf-8", "surrogateescape")).hexdigest()
print(json.dumps({"files": n_f, "dirs": n_d, "symlinks": n_l, "other": n_o, "total_file_bytes": total,
                  "tree_sha256": tree, "errors": errors[:20], "n_errors": len(errors)}))
'
docker volume ls -q | while IFS= read -r v; do
  users="$(docker ps -a --filter "volume=$v" --format '{{.Names}}:{{.State}}' | tr '\n' ' ')"
  meta="$(docker run --rm --pull never --network none -v "$v":/v:ro --entrypoint python3 "$PROBE_IMG" -c "$HASHER" 2>&1)"
  printf '{"volume": "%s", "used_by": "%s", "metadata": %s}\n' "$v" "$users" "${meta:-null}" >"$OUT/volumes/$v.json"
done

# ---- summary
python3 - "$OUT" <<'PY'
import glob, json, os, re, sys
out = sys.argv[1]; S = {}
def rd(p):
    try: return open(os.path.join(out, p), encoding="utf-8", errors="replace").read()
    except OSError: return ""
S["velith_git_head"] = rd("velith/git_head.txt").strip()
S["velith_git_clean_pre"] = rd("velith/git_status_pre.txt").strip() == ""
S["velith_git_clean_post"] = rd("velith/git_status_post.txt").strip() == ""
S["velith_image"] = rd("velith/image_id.txt").strip()
steps = {}
for f in sorted(glob.glob(os.path.join(out, "velith", "0*.txt"))):
    t = open(f, encoding="utf-8", errors="replace").read()
    ex = re.findall(r"\[exit (\d+)\]", t)
    last = [l for l in t.strip().splitlines() if l.strip() and not l.startswith("[exit")]
    steps[os.path.basename(f)] = {"cmd": t.splitlines()[0][2:], "exit": int(ex[-1]) if ex else None,
                                  "last_line": last[-1] if last else ""}
S["velith_checks"] = steps
S["velith_pytest_skips"] = re.findall(r"^SKIPPED.*$", rd("velith/05.txt"), re.M)
df = [l.split() for l in rd("internal_df.txt").splitlines() if l.startswith("overlay") or l.endswith(" /")]
if df:
    S["internal_fs"] = {"size_bytes": int(df[-1][1]), "used_bytes": int(df[-1][2]), "avail_bytes": int(df[-1][3])}
S["system_df"] = rd("system_df.txt").strip()
S["buildx_du_total"] = [l for l in rd("buildx_du.txt").splitlines() if l.lower().startswith(("shared", "private", "reclaimable", "total"))]
S["n_images"] = sum(1 for l in open(os.path.join(out, "inventory", "images_inspect.psv")) if l.startswith("sha256:"))
S["n_containers"] = sum(1 for _ in open(os.path.join(out, "inventory", "containers.jsonl")))
vols = []
for f in sorted(glob.glob(os.path.join(out, "volumes", "*.json"))):
    try: vols.append(json.loads(open(f).read()))
    except ValueError: vols.append({"volume": os.path.basename(f)[:-5], "used_by": "?", "metadata": None, "parse_error": True})
S["volumes"] = vols
S["networks_changed"] = rd("inventory/networks_pre.jsonl") != rd("inventory/networks_post.jsonl")
json.dump(S, open(os.path.join(out, "summary.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in S.items() if k not in ("volumes", "system_df")}, indent=2))
print("volumes:", [(v["volume"], v["used_by"], (v["metadata"] or {}).get("total_file_bytes")) for v in S["volumes"]])
PY
echo "PHASE0 WSL WRITTEN: $OUT"
