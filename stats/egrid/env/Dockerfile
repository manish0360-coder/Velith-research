# EPG-14 V0-V5 validation image (environment preparation only).
# Build ONCE on the owner's WSL host (build needs network); validation containers then run from the
# resulting immutable image ID with --network none. Never rebuild between V0 and V5: the image ID
# recorded in env.lock is the pin.
#
# The base tag below is believed to exist on Docker Hub but has NOT been verified from the CSE
# session. After `docker build --pull`, record the resolved base digest (RepoDigests) and the built
# image ID; both enter env.lock via EGRID_BASE_DIGEST / EGRID_IMAGE_ID.
ARG PY_IMAGE=python:3.12.10-slim-bookworm
FROM ${PY_IMAGE}

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --only-binary=:all: --no-deps -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && useradd --uid 1000 --create-home egrid

USER 1000:1000
WORKDIR /egrid
