# EPG-14 V0–V5 — environment preparation (K2 venue A: WSL + Docker)

**Status:** environment preparation only. V0–V5 are **not authorized and not executed**. Nothing here
has been run on the owner's WSL host. The `egrid` package referenced in §4 does not exist yet; its
implementation requires the separate RD authorization.

Files in this directory:

| File | Purpose |
|---|---|
| `Dockerfile` | Validation image (base tag believed to exist, unverified from the CSE session) |
| `requirements.txt` | Exact runtime pins: numpy 2.2.6, scipy 1.15.3, mpmath 1.3.0 (stdlib `unittest` as runner) |
| `make_env_record.py` | Writes `env.lock` (deterministic, no timestamps) and `env_record.json`; reports observed controls |
| `probes/venueB_sandbox_*` | Evidence from the CSE sandbox (candidate venue B, **not selected**) |
| `out/` | Created by the owner in §2; holds the real venue-A `env.lock` and `env_record.json` |

## 1. Owner prerequisites (record each output)

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research
uname -a ; cat /etc/os-release | head -3
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}'
docker info --format 'cgroup={{.CgroupVersion}} driver={{.CgroupDriver}} os={{.OperatingSystem}}'
nproc ; free -m
```

## 2. Build once, then record the environment (network needed for the build only)

```bash
docker build --pull -t egrid-env:epg14-v0v5 -f stats/egrid/env/Dockerfile stats/egrid/env
IMAGE_ID=$(docker image inspect --format '{{.Id}}' egrid-env:epg14-v0v5)
BASE_DIGEST=$(docker image inspect --format '{{index .RepoDigests 0}}' python:3.12.10-slim-bookworm)
echo "$IMAGE_ID $BASE_DIGEST"
mkdir -p stats/egrid/env/out

docker run --rm --network none --cpus=1 --memory=2g --memory-swap=2g --pids-limit=64 \
  --read-only --tmpfs /tmp:rw,size=64m --cap-drop=ALL --security-opt=no-new-privileges \
  --user 1000:1000 --ulimit cpu=300:300 \
  -e EGRID_VENUE=wsl-docker -e EGRID_IMAGE_ID="$IMAGE_ID" -e EGRID_BASE_DIGEST="$BASE_DIGEST" \
  -v "$PWD/stats/egrid/env:/egrid/env:ro" -v "$PWD/stats/egrid/env/out:/out" \
  "$IMAGE_ID" prlimit --as=2147483648 \
  python /egrid/env/make_env_record.py --lock /out/env.lock --record /out/env_record.json

sha256sum stats/egrid/env/out/env.lock stats/egrid/env/out/env_record.json
```

Expected `controls_observed`: every entry `PASS`. Any `FAIL` or `UNOBSERVABLE` → stop and report;
do not proceed to authorization. The `env.lock` SHA-256 printed by the host is the only value that
may be entered in the RD authorization record.

## 3. Resource budget (unchanged; enforced, not merely documented, once implemented)

| Stage | Hard CPU cap (s) | Enforcement |
|---|---|---|
| V0 | 1800 | `--ulimit cpu` backstop + driver `getrusage` check + in-process `RLIMIT_AS` 2 GiB |
| V1 | 900 | same |
| V2 | 5400 | same |
| V3 | 900 | same |
| V4 | 1800 | same |
| V5 | 3600 | same |
| **Total** | **14400 (= 4 CPU-h)** | No borrowing between stages; exceeding a cap → STOP-8 |

## 4. Future V0–V5 commands — DO NOT RUN until the RD authorization is recorded

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research
IMAGE_ID=<image_id line from stats/egrid/env/out/env.lock>
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p "stats/egrid/runs/$RUN_ID"
COMMON=(--rm --network none --cpus=1 --memory=2g --memory-swap=2g --pids-limit=64
  --read-only --tmpfs /tmp:rw,size=256m --cap-drop=ALL --security-opt=no-new-privileges
  --user 1000:1000 -w /egrid
  -v "$PWD/stats/egrid:/egrid:ro" -v "$PWD/stats/egrid/runs/$RUN_ID:/egrid/runs/$RUN_ID"
  -e EGRID_IMAGE_ID="$IMAGE_ID" -e EGRID_RUN_ID="$RUN_ID")
stage() { docker run "${COMMON[@]}" --ulimit cpu="$2":"$2" "$IMAGE_ID" \
  python -m egrid.cli stage "$1" --run-id "$RUN_ID" --cpu-cap-s "$2"; }
stage V0 1800 && stage V1 900 && stage V2 5400 && stage V3 900 && stage V4 1800 && stage V5 3600
docker run "${COMMON[@]}" "$IMAGE_ID" python -m egrid.cli report --run-id "$RUN_ID"
```

The `&&` chain halts at the first non-zero exit (any STOP). Validation never uses the network, never
writes outside `stats/egrid/runs/$RUN_ID`, and never touches production Velith.
