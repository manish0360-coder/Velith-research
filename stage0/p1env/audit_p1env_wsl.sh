#!/usr/bin/env bash
# P1 environment-readiness audit, WSL side. READ-ONLY.
# It pulls no image, creates or runs no container, and changes no Docker/WSL setting.
# `docker manifest inspect` reads registry metadata only (anonymous Docker Hub; 5 manifest
# requests, which count against the anonymous rate limit).
# Output: stage0/p1env/results/wsl-<UTC>/ (raw command outputs + summary.json)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/results/wsl-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT/manifests"

run() { local name="$1"; shift; { echo "\$ $*"; "$@"; echo "[exit $?]"; } >"$OUT/$name.txt" 2>&1; }

run os             uname -a
run os_release     cat /etc/os-release
run python3        python3 --version
run git            git --version
run disk           df -B1 / /mnt/c /mnt/d /mnt/e
docker version --format '{{json .}}' >"$OUT/docker_version.json" 2>"$OUT/docker_version.err"
docker info --format '{{json .}}' >"$OUT/docker_info.json" 2>"$OUT/docker_info.err"
run docker_context docker context ls
run docker_df      docker system df
run docker_images  docker image ls --digests --no-trunc

# The five P1 task images (M2-PV-P1_PILOT_DESIGN.md §8). T1's digest was verified in M2.
IMAGES=(
  "T1 swebench/sweb.eval.x86_64.pallets_1776_flask-5014:latest"
  "T2 swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-24570:latest"
  "T3 swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14629:latest"
  "T4 swebench/sweb.eval.x86_64.astropy_1776_astropy-7336:latest"
  "T5 swebench/sweb.eval.x86_64.pydata_1776_xarray-6721:latest"
)
for entry in "${IMAGES[@]}"; do
  set -- $entry
  docker manifest inspect -v "$2" >"$OUT/manifests/$1.json" 2>"$OUT/manifests/$1.err"
  echo $? >"$OUT/manifests/$1.exit"
done

python3 - "$OUT" <<'PY'
import json, os, sys, re
out = sys.argv[1]
M2_T1_DIGEST = "sha256:eaf597005c159361cb8ee26018fb3741b320f331065f0c95726d83ccf2f1fba4"
names = {"T1": "pallets_1776_flask-5014", "T2": "matplotlib_1776_matplotlib-24570",
         "T3": "scikit-learn_1776_scikit-learn-14629", "T4": "astropy_1776_astropy-7336",
         "T5": "pydata_1776_xarray-6721"}
local = open(os.path.join(out, "docker_images.txt"), encoding="utf-8", errors="replace").read()
images, union = {}, {}
for t in sorted(names):
    rec = {"image": f"swebench/sweb.eval.x86_64.{names[t]}:latest",
           "exit": open(os.path.join(out, "manifests", t + ".exit")).read().strip()}
    try:
        raw = json.load(open(os.path.join(out, "manifests", t + ".json")))
        entries = raw if isinstance(raw, list) else [raw]
        def _plat(x):
            return (x.get("Descriptor", {}).get("platform") or {})
        amd = [x for x in entries if _plat(x).get("os") == "linux" and _plat(x).get("architecture") == "amd64"]
        e = (amd or entries)[0]
        man = e.get("SchemaV2Manifest") or e.get("OCIManifest") or {}
        layers = man.get("layers", [])
        rec.update(manifest_digest=e.get("Descriptor", {}).get("digest"),
                   platform=e.get("Descriptor", {}).get("platform"),
                   n_layers=len(layers),
                   compressed_bytes=sum(int(l["size"]) for l in layers),
                   config_digest=(man.get("config") or {}).get("digest"),
                   multi_platform_index=isinstance(raw, list))
        for l in layers:
            union[l["digest"]] = int(l["size"])
        rec["layer_digests"] = [l["digest"] for l in layers]
    except Exception as exc:  # recorded, never fatal
        rec["error"] = f"{type(exc).__name__}: {exc}"
    rec["present_locally"] = names[t] in local
    images[t] = rec
if "T1" in images and images["T1"].get("manifest_digest"):
    images["T1"]["matches_m2_digest"] = images["T1"]["manifest_digest"] == M2_T1_DIGEST
per_sum = sum(r.get("compressed_bytes", 0) for r in images.values())
uniq = sum(union.values())
try:
    info = json.load(open(os.path.join(out, "docker_info.json")))
    ds = dict(info.get("DriverStatus") or [])
    docker = {k: info.get(k) for k in ("ServerVersion", "OperatingSystem", "KernelVersion", "Driver",
                                       "DockerRootDir", "MemTotal", "NCPU", "CgroupVersion", "SecurityOptions")}
    docker["driver_type"] = ds.get("driver-type")
    docker["containerd_snapshotter"] = "containerd" in str(ds.get("driver-type", ""))
except Exception as exc:
    docker = {"error": f"{type(exc).__name__}: {exc}"}
summary = {
    "images": images,
    "compressed_bytes_sum_per_image": per_sum,
    "compressed_bytes_unique_layers": uniq,
    "shared_layer_savings_bytes": per_sum - uniq,
    "note": "Registry sizes are COMPRESSED. On-disk size after pull is larger (not measurable without pulling). "
            "With the containerd image store, both compressed blobs and unpacked snapshots are kept.",
    "docker": docker,
}
json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in summary.items() if k != "images"}, indent=2))
for t, r in images.items():
    print(t, r.get("exit"), r.get("manifest_digest"), r.get("n_layers"), r.get("compressed_bytes"),
          "local" if r.get("present_locally") else "", r.get("error", ""))
PY
echo "WSL AUDIT WRITTEN: $OUT"
