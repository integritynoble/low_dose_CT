# WS-3 RunBundle — reproducible corpus generation

The PWM-format RunBundle for the WS-3 reference method (plan tasks 3.5 / 4.3): a pinned Docker
image whose `docker run` regenerates the derived-data corpus and its validation numbers, so an
external verifier can reproduce every Technical-Validation figure from a fixed artifact. It is
also the mechanism by which reusers regenerate the **DUA-restricted** AAPM/Mayo pixel records
locally (see the manuscript's *Licensing and redistribution*; those pixels are not redistributed).

## Contents

| File | Role |
|---|---|
| `Dockerfile` | Pinned image: torch (CPU wheel) + the in-repo WS-1 loader / WS-2 library / WS-3 method, installed editable so `emit_corpus` resolves its sibling `corpus_emit`/`deposit` tools. |
| `run.py` | Entrypoint. `--self-test` (default) runs the synthetic end-to-end; `--emit` is the real, GPU+data-gated reproduction. Writes `results.json`. |
| `results.schema.json` | Schema for `results.json` (corpus checks + PSNR/SSIM/UQ-Spearman). `run.py` self-validates against it. |
| `build.sh` | `docker build` from the repo root with a pinned tag. |

## Build & run

```bash
# from the repo root
bash WS-3_reference_method/runbundle/build.sh pwm-ldct-recon:0.1.0

# self-test: no GPU, no data — proves the bundle executes end-to-end
docker run --rm pwm-ldct-recon:0.1.0

# run.py also works from a checkout without Docker (CI uses this):
python WS-3_reference_method/runbundle/run.py --self-test --results /tmp/results.json
```

`--self-test` trains a tiny ensemble, emits a corpus (reference method + an FBP baseline), runs
the deposit pipeline (credential audit + `MANIFEST.sha256` + the `error_abs` construction-check),
and computes a validation block. Its numbers are **synthetic, not scientific** — the point is
that the pipeline runs and the deposit checks pass.

## Real reproduction (Phase 3, GPU + data gated)

```bash
docker run --rm \
  -v /path/to/weights:/weights \
  -v /path/to/authorised-ws1-tree:/data \
  pwm-ldct-recon:0.1.0 \
  --emit --weights /weights/ensemble.pt --data-root /data --results /tmp/results.json
```

`--emit` is currently a documented stub: it needs the pinned 5-member ensemble weights, the
frozen LUNA16 detector, and an authorised WS-1 HDF5 tree (none present on the build host). Wiring
point is `run.py:emit_real` → `pwm_ldct_recon.emit_corpus.run`. For GPU, swap the base image for a
CUDA image and the torch index for the matching CUDA wheel. The IPFS CID and PWM L4 cert that
anchor the published bundle are recorded in the manuscript's Code Availability section at deposit.

## Reproducibility knobs

`PYTHONHASHSEED=0`, single-threaded BLAS, and the per-member seeds `{42..46}` (Supplementary
Table S2) are pinned so a fixed `(image, weights, data)` triple reproduces the corpus within
floating-point tolerance.
