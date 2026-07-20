# WS-3 reference reconstruction -- PWM RunBundle (Phase 3.5 / 4.3).
#
# A pinned, reproducible image: `docker run` regenerates the corpus + validation numbers.
# Build context is the REPO ROOT (the bundle installs three in-repo packages):
#   docker build -f WS-3_reference_method/runbundle/Dockerfile -t pwm-ldct-recon:<tag> .
#
# Default CMD runs the synthetic self-test (no GPU / no data) so the image proves it executes
# anywhere. A real reproduction mounts pinned ensemble weights + an authorised WS-1 tree and
# passes `--emit` (see run.py). For GPU reproduction, swap the base for a CUDA image and the
# torch index for the matching CUDA wheel.
FROM python:3.12-slim

# git is occasionally needed by editable installs; rm the apt lists to keep the layer small.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/pwm-ws3

# Only the subtrees the bundle needs (see .dockerignore at the repo root).
COPY WS-2_framework/pwm_dose_equivalence ./WS-2_framework/pwm_dose_equivalence
COPY WS-1_dataset/pwm_ldct_loader        ./WS-1_dataset/pwm_ldct_loader
COPY WS-3_reference_method               ./WS-3_reference_method

# torch from the CPU wheel index (no CUDA download); then the in-repo packages. The method
# package is installed EDITABLE so emit_corpus resolves its sibling corpus_emit/deposit tools
# by path (they are scripts, not installed packages).
RUN python -m pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install nibabel jsonschema "numpy>=1.21" \
    && pip install -e WS-2_framework/pwm_dose_equivalence \
    && pip install -e WS-1_dataset/pwm_ldct_loader \
    && pip install -e WS-3_reference_method/method --no-deps

# Reproducibility: pin determinism knobs (mirrors Supplementary Table S2).
ENV PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

ENTRYPOINT ["python", "WS-3_reference_method/runbundle/run.py"]
CMD ["--self-test", "--results", "/tmp/results.json"]
