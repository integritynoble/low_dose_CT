---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_9b76fb969a4411f19467525400287e28
    ReservedCode1: iwQ0Mn1WgBhWqzgCwzMcguMnBsbLVBgupyxGLEAdmDvY0667tl7mo9KB4lnf1wx3BbvMuE3OV6hAa6nyri2Hqvflw33wcVwhxeZTJWQx8VxPRQXnoGrcSkjnYiuU8lSaR2YXDd2W6hjVzpeIOYIZ/aumgYfg1Ukmw/sy6Qh4KcBQQ8TjG9pL8LyavaY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_9b76fb969a4411f19467525400287e28
    ReservedCode2: iwQ0Mn1WgBhWqzgCwzMcguMnBsbLVBgupyxGLEAdmDvY0667tl7mo9KB4lnf1wx3BbvMuE3OV6hAa6nyri2Hqvflw33wcVwhxeZTJWQx8VxPRQXnoGrcSkjnYiuU8lSaR2YXDd2W6hjVzpeIOYIZ/aumgYfg1Ukmw/sy6Qh4KcBQQ8TjG9pL8LyavaY=
---

# WS-3 — Compute & GPU resource plan

Scope: the resource requirements for training the WS-3 reference reconstruction method
(`method/`, `pwm_ldct_recon`) to publication quality, the budget for that training, and the
**current training status** as of this audit. The reader is expected to be a reviewer, a
funder, or the engineer who will book the GPU. All figures are D9-anchored
(D9 = 2026-05-20); training-status markers are dated and updated on every material change.

---

## 1. Workload profile

| Item | Value | Source |
|---|---|---|
| Model | Unrolled iterative reconstruction, K=10 iterations, shared U-Net denoiser | `config.py` `ReconConfig.iterations` |
| Denoiser channels | (32, 64, 128, 256), GroupNorm, GELU | `config.py` |
| Parameter count | < 5M per member | README architecture table |
| UQ | Deep ensemble, **M = 5** independently-seeded members | `config.py` `EnsembleConfig.members` |
| Slice size | 512 × 512 axial, single channel | `config.py` `slice_size` |
| Batch size | 4 | `config.py` `batch_size` |
| Optimizer / epochs | AdamW, cosine + 5% warmup, 100 epochs (S1 `\todo{epochs}`, calibrate on real tree) | `config.py` |
| Training data | WS-1 v0.5 harmonized tree (doses 0.10 / 0.25 / 0.50, mix weights 0.4/0.4/0.2) | `config.py` `doses` |
| Inference target | < 5 s/slice on a single A100 (operational claim) | README architecture table |

The unrolled loop runs the differentiable Radon forward/back-projection operator
`packages/pwm_core/contrib/modalities/ct_radon.py` at every iteration **in the training
graph**, so the per-step cost is dominated by K×(projection pair + denoiser forward/backward)
rather than by a single U-Net pass. Do not size the cluster from plain-2D-U-Net rules of thumb.

---

## 2. Required GPU class

### Minimum acceptable (training to publication quality)

| Class | Examples | Why |
|---|---|---|
| **Primary** | NVIDIA A100 80GB (PCIe or SXM) | Fits full 512×512 batch-4 unrolled graph with Radon operators in memory; reproduces the `< 5 s/slice` inference claim; matches `runbundle/Dockerfile` CUDA assumptions |
| **Equivalent / acceptable** | H100 80GB, A6000 48GB (smaller batch or gradient checkpointing), RTX 4090 24GB (dev/ablation only, **not** final numbers) | Same architecture; adjust `batch_size`/`slice_size` only as documented in §4 |

### Explicitly insufficient

| Hardware | Limitation |
|---|---|
| RTX 4060 Laptop 8 GB (current workstation) | Cannot hold a single 512² batch-4 unrolled member; **no publication numbers can be produced on this device** |
| CPU-only | Correct for `pwm-recon smoke` and CI only; not for training |

### Recommendation

Book **5 × A100 80GB** (one per ensemble member) for the production run; the members are
independent up to data loading, so this cuts wall-clock ~5× versus a single GPU and is the
cheapest way to respect the fixed `seeds = (42..46)` contract. A single A100 with sequential
members is acceptable but multiplies wall-clock by ~5.

---

## 3. Training-time estimate

Planning estimate, not a measurement — calibrate on the real harmonized tree before booking.
Per-step cost assumes A100 80GB, batch 4, 512² slice, K=10, mixed-precision (BF16).

| Component | Estimate |
|---|---|
| Per-step wall time (train) | ~0.8–1.5 s (unrolled K=10 + ensemble member) |
| Steps per epoch (v0.5 train split ≈ 60% of 1,226 unique series, ~100 slices/series, batched ×4) | ~1.5–2.5K |
| Epochs (S1 target) | 60–100 (warm-up ablations will pin this; `config.py` default 100) |
| **Single member** | **~90–250 GPU-h** |
| **Full deep ensemble (M=5, sequential)** | **~450–1,250 GPU-h** |
| Wall-clock on 5×A100 (members in parallel) | ~4–11 days |
| Cross-vendor runs (train Siemens → test GE, etc.) + UQ calibration + credential task runs | +20–40% of the above |
| Total budget envelope (production corpus) | **~600–1,800 A100-h** |

Sensitivity: doubling batch size roughly halves wall-clock but raises memory; gradient
checkpointing adds ~20–30% wall-time and lowers memory ~40%; `max_steps` (train.py) is the
supported knob for pilot runs before the full schedule.

---

## 4. Budget

Cloud list prices, 2026-08 (on-demand, US regions; spot/committed-use are cheaper). Figures are
planning ranges, not quotes.

| Option | Hourly (GPU) | 1,800 A100-h envelope | Notes |
|---|---|---|---|
| 5 × A100 80GB (on-demand, e.g. Lambda/runpod/AWS p4d) | $1.5–3 / GPU-h | **$2.7K–5.4K** | recommended production path |
| 1 × A100 80GB (sequential members) | $1.5–3 / GPU-h | same total GPU-h, ~5× wall-clock | cheapest cash outlay |
| RTX 4090 24GB (ablation / hyperparameter pilots only) | $0.5–1 / GPU-h | — | never for final numbers |
| Academic cluster (UTSW / partner) | internal | near-$0 cash | preferred if available; aligns with NIH budget narrative (WS-5 R21 Aim 2/3) |

Caveats that move the estimate up: real-data pathologies (retries, OOM tuning), any change to
`slice_size` above 512, LPIPS/SSIM batch evaluation over the full test split, and re-runs for
reviewer requests. Reserve **+25% headroom** in the booking.

---

## 5. Current training status (updated 2026-08-17)

| Item | Status |
|---|---|
| Method scaffold + CPU tests | ✅ done — 65 tests pass; `pwm-recon smoke` runs the full Phase-3 pipeline on synthetic data (CI, 3 Python versions) |
| Real training data tree | ❌ blocked — WS-1 v0.5 harmonized tree (LIDC + AAPM + Mayo) not yet landed locally; GCS staging (`gs://low-dose-ct/...`) pending WS-1 pipeline runs |
| GPU | ❌ blocked — current workstation has only RTX 4060 Laptop 8 GB (see §2); no data-center GPU booked |
| Production training (v1 ensemble) | ⛔ **NOT STARTED** — all PSNR/SSIM/UQ numbers in `manuscript.tex` remain `\todo{}` / synthetic-only until §2–§4 resources are available |
| Budget status | ◻ no cloud GPU spend yet; plan above approved as the booking target |

**Manuscript implications:** `paper_draft/manuscript.tex` reports all technical-validation
numbers as pending (see the `\todo{}` markers in Tables and the training-status note added in
`manuscript.tex` §Methods / §Availability). Until the §3 envelope is executed, the Data
Descriptor cannot claim measured reconstruction metrics; the paper remains submission-ready
only in structure, not in numbers.

**Next actions:** (1) land the WS-1 v0.5 tree locally; (2) run the §2 recommended 5×A100 booking
or secure academic cluster time; (3) execute a 1–2 epoch pilot (`--max_steps` in `train.py`) to
calibrate §3 per-step numbers; (4) re-update this section with measured timings and the
`\todo{epochs}`/`\todo{lr}` back-fill into `supplementary.tex` Table S1.
*（内容由AI生成，仅供参考）*
