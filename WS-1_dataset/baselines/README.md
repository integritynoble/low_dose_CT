# pwm_ldct_baselines

Reproducible reconstruction-baseline harness for **PWM-LDCT v0.5** — the code behind the
manuscript's Technical-Validation baseline reproductions (`tab:baselines_v05`). It trains a
low-dose → full-dose reconstruction model against the harmonized dataset (via `pwm_ldct_loader`)
and emits per-dose-level **PSNR / SSIM / LPIPS**.

> **Status:** harness complete and tested. **RED-CNN** (Chen et al., TMI 2017) is implemented
> faithfully. The manuscript's three other baselines (a transformer, a diffusion, and an
> unrolled-iterative method) are **pluggable registry stubs** — each needs its published
> implementation + a method-selection decision (still `\todo` in the manuscript). Any
> `nn.Module` mapping `[B,1,H,W] → [B,1,H,W]` plugs in (see `models/`).
>
> **To run the benchmark on a GPU** (method selection, compute estimate, protocol, data-quality
> prerequisite) see [`RUN_PLAN.md`](RUN_PLAN.md).
>
> **Compute:** training to publication quality needs a **GPU**. The harness auto-selects CUDA when
> available (CPU otherwise — fine for the tests, not for the benchmark numbers).

## Install / test

```bash
pip install -e .[dev]          # needs pwm_ldct_loader on the path
pytest                         # synthetic-data harness tests (train a step -> eval -> results.json)
```

## Use (GPU)

```bash
python -m pwm_ldct_baselines train \
    --dataset /path/pwm_ldct_v0_5 --out red_cnn.pt --model red_cnn --epochs 100 --seed 42
python -m pwm_ldct_baselines eval \
    --dataset /path/pwm_ldct_v0_5 --checkpoint red_cnn.pt --split test --out results.json --seed 42
```

`results.json` reports PSNR/SSIM/LPIPS for each simulated dose level (`sim_r010/r025/r050`) and the
real low-dose subset (`real`) separately. `--sources mayo,aapm` restricts to the real-paired
subset; `Dockerfile.baseline` builds the GPU image used for bit-identical reproduction.

This harness is **not** a method ranking (out of scope for a Data Descriptor) — its role is to show
the unified loader drives heterogeneous methods to convergence and that the numbers reproduce from
the released container.

## Metrics

PSNR and Gaussian-windowed SSIM are computed in normalized `[0,1]` space (`data_range=1`); LPIPS
(AlexNet) is computed when the optional `lpips` package is installed, else reported as `null`.
