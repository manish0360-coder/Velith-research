#!/usr/bin/env bash
# OD-ENV Phase 1, WSL-side steps (called by Phase1-Execute.ps1). Each subcommand exits non-zero on a HARD STOP.
#   velith | db-stop | precheck | prune | db-start      Usage: phase1_wsl_steps.sh <sub> <out_dir>
# The prune is the ONLY mutating Docker operation here: `docker buildx prune --builder default --force` (no --all).
set -u
P1ENV=/mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env
B0="${B0:-$P1ENV/results/phase0-wsl-20260930T064850Z}"       # post-stop baseline (DB stopped)
VELITH="${VELITH:-/mnt/e/Projects/OpenSourceLab/repos/Velith}"
EXPECT_HEAD=5452efc44274c575c781673eb9c6287facfb94e6
SUB="${1:?subcommand}"; OUT="${2:?out_dir}"; mkdir -p "$OUT"
fail() { echo "HARD-STOP: $*"; exit 1; }

inv_diff() {  # $1 = tag; compares images/containers/volumes/networks with B0
  local t="$1"
  grep -E '^sha256:' "$B0/inventory/images_inspect.psv" | cut -d'|' -f1 | sort -u >"$OUT/b0.images"
  grep -E '^[0-9a-f]{64}\|' "$B0/inventory/containers_inspect.psv" | cut -d'|' -f1 | sort >"$OUT/b0.containers"
  ls "$B0/volumes" | sed 's/\.json$//' | sort >"$OUT/b0.volumes"
  python3 -c "import json;[print(json.loads(l)['Name']) for l in open('$B0/inventory/networks_post.jsonl') if l.strip()]" | sort >"$OUT/b0.networks"
  docker image ls -a -q --no-trunc | sort -u >"$OUT/$t.images"
  docker ps -aq --no-trunc | sort >"$OUT/$t.containers"
  docker volume ls -q | sort >"$OUT/$t.volumes"
  docker network ls --format '{{.Name}}' | sort >"$OUT/$t.networks"
  for k in images containers volumes networks; do
    diff "$OUT/b0.$k" "$OUT/$t.$k" >"$OUT/$t.$k.diff" || fail "$k inventory differs from B0 ($t) -> $OUT/$t.$k.diff"
  done
  echo "PASS inventory unchanged ($t): $(wc -l <"$OUT/$t.images") images, $(wc -l <"$OUT/$t.containers") containers, $(wc -l <"$OUT/$t.volumes") volumes, $(wc -l <"$OUT/$t.networks") networks"
}
used_bytes() { docker run --rm --pull never --network none --entrypoint df python:3.12-slim -B1 / | awk 'NR==2{print $3}'; }
to_bytes() { python3 -c "
import re,sys; m=re.match(r'([\d.]+)\s*([kMGT]?B)', sys.argv[1].strip()); u={'B':1,'kB':1e3,'MB':1e6,'GB':1e9,'TB':1e12}
print(int(float(m.group(1))*u[m.group(2)]) if m else -1)" "$1"; }
du_field() { grep -E "^$1:" "$2" | awk '{print $2}'; }

case "$SUB" in
  velith)
    head="$(git -C "$VELITH" --no-optional-locks rev-parse HEAD)"; st="$(git -C "$VELITH" --no-optional-locks status --porcelain)"
    echo "velith HEAD=$head clean=$([ -z "$st" ] && echo true || echo false)" | tee "$OUT/velith.txt"
    [ "$head" = "$EXPECT_HEAD" ] && [ -z "$st" ] || fail "Velith main HEAD/clean changed" ;;
  db-stop)
    s="$(docker inspect districore-db-1 --format '{{.State.Status}}')"
    if [ "$s" = "running" ]; then docker stop --time 120 districore-db-1 >/dev/null; fi
    r="$(docker inspect districore-db-1 --format '{{.State.Status}} {{.State.ExitCode}}')"
    echo "districore-db-1: was=$s now=$r" | tee -a "$OUT/db.txt"
    [ "$r" = "exited 0" ] || fail "districore-db-1 not cleanly stopped: $r" ;;
  precheck)
    v="$(docker info --format '{{.ServerVersion}}')"; [ "$v" = "29.5.3" ] || fail "engine version '$v'"
    echo "PASS engine $v"
    n="$(docker image ls -a --format '{{.Repository}}' | grep -c '^swebench/' || true)"
    [ "$n" = "0" ] || fail "$n swebench images already present"; echo "PASS P1 images absent (0 swebench/*)"
    for vol in districore_backup_data districore_caddy_config_dev districore_caddy_data_dev districore_db_data districore_media_data districore_wal_archive; do
      docker volume inspect "$vol" >/dev/null 2>&1 || fail "volume $vol missing"; done
    echo "PASS six DistriCore volumes present"
    inv_diff pre ;;
  prune)
    docker buildx du --builder default >"$OUT/buildx_du_before.txt" 2>&1 || fail "buildx du (before) failed"
    docker system df >"$OUT/system_df_before.txt" 2>&1
    ub="$(used_bytes)"; echo "$ub" >"$OUT/internal_used_before.txt"
    docker buildx prune --builder default --force >"$OUT/buildx_prune_output.txt" 2>&1 || fail "buildx prune failed"
    docker buildx du --builder default >"$OUT/buildx_du_after.txt" 2>&1
    docker system df >"$OUT/system_df_after.txt" 2>&1
    ua="$(used_bytes)"; echo "$ua" >"$OUT/internal_used_after.txt"
    v="$(docker info --format '{{.ServerVersion}}')"; [ "$v" = "29.5.3" ] || fail "engine unhealthy after prune ('$v')"
    inv_diff post
    pb="$(du_field Private "$OUT/buildx_du_before.txt")"; pa="$(du_field Private "$OUT/buildx_du_after.txt")"
    sb="$(du_field Shared "$OUT/buildx_du_before.txt")"; sa="$(du_field Shared "$OUT/buildx_du_after.txt")"
    rec="$(grep -E '^Total:' "$OUT/buildx_prune_output.txt" | awk '{print $2}')"
    printf 'cache: private %s -> %s ; shared %s -> %s ; prune reported Total %s\ninternal used: %s -> %s bytes (freed %s)\n' \
      "$pb" "${pa:-0B}" "$sb" "${sa:-0B}" "${rec:-?}" "$ub" "$ua" "$((ub-ua))" | tee "$OUT/prune_numbers.txt"
    [ $((ub-ua)) -ge 15000000000 ] || fail "internal used dropped by only $((ub-ua)) bytes (<15 GB): do NOT compact" ;;
  db-start)
    docker start districore-db-1 >/dev/null || fail "docker start districore-db-1 failed"
    for i in $(seq 1 36); do
      h="$(docker inspect districore-db-1 --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}')"
      [ "$h" = "running healthy" ] && { echo "PASS districore-db-1: $h" | tee -a "$OUT/db.txt"; exit 0; }
      sleep 5
    done
    fail "districore-db-1 not healthy after 180 s: $h" ;;
  *) fail "unknown subcommand $SUB" ;;
esac
