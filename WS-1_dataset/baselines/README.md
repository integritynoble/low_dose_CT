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
pip install -e ../pwm_ldct_loader   # the sibling loader package, first (src/ layout)
pip install -e .[dev]
pytest                              # synthetic-data harness tests (train a step -> eval -> results.json)
```

### Third environment (Blackwell / RTX 50-series, e.g. native Linux RTX 5090)

The shipped reference/recalculation environments use torch 2.3.0+cu121 (CUDA 12.1).
NVIDIA Blackwell GPUs (sm_120) require **CUDA 12.8+**; **PyTorch 2.7.0 is the first
stable release with native sm_120 support** (CUDA 12.8 wheels). For a third-party
re-run on a Blackwell host, install the `blackwell` extra (torch>=2.7.0,
torchvision>=0.22.0) inside a fresh venv:

```bash
python -m venv .venv_t3 && source .venv_t3/bin/activate
pip install --upgrade pip
# Route A (recommended): official PyTorch CUDA 12.8 stable wheels
pip install -e ../pwm_ldct_loader
pip install -e .[blackwell,lpips] --index-url https://download.pytorch.org/whl/cu128
pip install -e ../pwm_ldct_loader --index-url https://download.pytorch.org/whl/cu128
# then reinstall the two editable packages WITHOUT the index override so they resolve
# against the torch already present (do not downgrade torch):
pip install -e ../pwm_ldct_loader
pip install -e .[blackwell,lpips]
# verify
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_capability(0))"
```

> Route A 依赖全部经 `--index-url https://download.pytorch.org/whl/cu128` 安装；
> 若 prefer CUDA 13.0（PyPI stable）可改用默认 PyPI + `pip install torch torchvision`，
> 或 CUDA 13.2（experimental nightly）：`--index-url https://download.pytorch.org/whl/nightly/cu132`。
> 本分支仅放宽运行依赖（`blackwell` extra），**不修改任何指标/协议/observer/模型定义代码**；
> eval 语义与容器门（§7.1）不变。完整第三方运行手册见
> [`../R6_recalc/third_env/THIRD_ENV_RUNBOOK_2026-09-25.md`](../R6_recalc/third_env/THIRD_ENV_RUNBOOK_2026-09-25.md)。

`pwm_ldct_loader` must be installed, not merely present on disk: it is a `src/`-layout
package, so an uninstalled checkout is shadowed by its own outer directory and
`pwm_ldct_loader.schema` will not import. See
[`../pwm_ldct_loader/README.md`](../pwm_ldct_loader/README.md) ("Troubleshooting").

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

## Container reproduction gate (§7.1) — standing rule

**Any downstream comparison (WS-3 reference method, WS-4 leaderboard, external benchmark) must use
numbers reproduced inside this released container** (`pwm-ldct-baselines:v0.5`,
`Dockerfile.baseline`, content-addressed) under the declared task specification
([`task_spec.json`](task_spec.json), [`../schema/detectability_task_spec.md`](../schema/detectability_task_spec.md))
and the double-metric evaluation protocol (fidelity + detectability reported together).
**Paper numbers from the original publications must not be quoted as baseline evidence.** The
container gate guarantees every comparison rests on the same bits, the same task, and the same
evaluation — reproduce first, compare second.

## Fixed seed set (§7.3)

Every reported evaluation must run over the fixed seed set and report mean + interval (min/max):
`eval --seeds 42,2023,7,12345,999 --out <model>_seedset.json` (see `RUN_PLAN.md` §8).

## Metrics

PSNR and Gaussian-windowed SSIM are computed in normalized `[0,1]` space (`data_range=1`); LPIPS
(AlexNet) is computed when the optional `lpips` package is installed, else reported as `null`.
