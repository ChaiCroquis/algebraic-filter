# Hybrid checker image: algebraic-filter (+α) + pyright (base type-check).
# Zero host dependencies — everything (python / ruff / hypothesis / pyright / AF)
# lives in the container. The container acts as a Claude Code PostToolUse hook.
#
# Build:  docker build -t af-hybrid examples/hybrid-starter/docker
# Use (wired by setup_hybrid when Docker is detected):
#   docker run -i --rm -v "<proj>:/work" -e AF_HOST_PROJECT="<proj>" af-hybrid
FROM python:3.11-slim

# git: fetch AF (the pip package excludes hooks/, so clone the full repo).
# libatomic1: required by pyright's bundled node runtime (slim image lacks it,
#   otherwise node fails with "libatomic.so.1: cannot open shared object file").
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# AF source (af_phase2/3/4 + hooks/posttool_af_check.py)
RUN git clone --depth 1 https://github.com/ChaiCroquis/algebraic-filter /af

# checker deps (ruff: AF Layer 1 + base; hypothesis: AF Phase 2; pyright: base type-check)
RUN pip install --no-cache-dir ruff hypothesis pyright

# pre-warm pyright so its node runtime is downloaded into the image (not per-run)
RUN printf 'x: int = 1\n' > /tmp/_warm.py && pyright /tmp/_warm.py || true

COPY entrypoint.py /entrypoint.py

ENV PYTHONPATH=/af
ENV PYTHONUTF8=1
WORKDIR /work
ENTRYPOINT ["python", "-X", "utf8", "/entrypoint.py"]
