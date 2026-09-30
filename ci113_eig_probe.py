"""CI #113 read-only probe: runtime BLAS core + the A1_VS_A0 fixture's robust-covariance spectrum.
Run inside the verifier image via stdin (no repo change):
  docker compose run --rm -T --pull never verifier python - < .../Velith-research/ci113_eig_probe.py
"""
import ctypes, glob, hashlib, os, platform
import numpy as np, scipy, statsmodels
def corename(pkg):
    libs = glob.glob(os.path.join(os.path.dirname(pkg.__file__), os.pardir, pkg.__name__ + ".libs", "*openblas*"))
    for lib in libs:
        L = ctypes.CDLL(lib)
        for sym in ("scipy_openblas_get_corename64_", "scipy_openblas_get_corename", "openblas_get_corename"):
            if hasattr(L, sym):
                f = getattr(L, sym); f.restype = ctypes.c_char_p
                return f"{os.path.basename(lib)}:{f().decode()}"
    return f"no openblas lib found ({libs})"
cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?")
flags = next((l for l in open("/proc/cpuinfo") if l.startswith("flags")), "")
print("cpu:", cpu, "| avx512f:", " avx512f " in flags, "| avx2:", " avx2 " in flags, "| machine:", platform.machine())
print("versions: python", platform.python_version(), "numpy", np.__version__, "scipy", scipy.__version__, "statsmodels", statsmodels.__version__)
print("env:", {k: v for k, v in os.environ.items() if k.startswith(("OPENBLAS", "OMP", "MKL", "NPY"))})
print("blas core: numpy", corename(np), "| scipy", corename(scipy))
try:
    from numpy._core._multiarray_umath import __cpu_features__ as _f
    print("numpy SIMD found:", sorted(k for k, v in _f.items() if v))
except Exception as exc:
    print("numpy SIMD features unavailable:", exc)
from velith.analysis import gee as g
from velith.analysis.binder import Observation
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.cov_struct import Exchangeable
h = lambda s: hashlib.sha256(s.encode()).hexdigest()
o = []
for t in range(24):   # identical to tests/unit/test_analysis_gee.py::_a1_vs_a0(k=3, n_tasks=24)
    o.append(Observation(task_identity=h(f"task-{t}"), arm="A0", checkpoint_identity=hashlib.sha256(b"empty-checkpoint").hexdigest(), checkpoint_index=None, endpoint=1 if t % 4 == 0 else 0))
    for i in range(1, 4):
        o.append(Observation(task_identity=h(f"task-{t}"), arm="A1", checkpoint_identity=h(f"cp-{i}"), checkpoint_index=i, endpoint=0 if (t + i) % 3 == 0 else 1))
d = g.build_design(o, comparison=g.Comparison.A1_VS_A0, checkpoint_count=3)
f = GEE(np.asarray(d.endog, float), np.asarray(d.exog, float), np.asarray(d.groups, np.int64), family=Binomial(), cov_struct=Exchangeable()).fit(maxiter=100, ctol=1e-8, start_params=None, cov_type="robust")
print("params:", repr(np.asarray(f.params)))
print("cov_robust eigvals:", repr(np.linalg.eigvalsh(np.asarray(f.cov_robust))))
print("fit_gee:", type(g.fit_gee(o, comparison=g.Comparison.A1_VS_A0, checkpoint_count=3)).__name__)
