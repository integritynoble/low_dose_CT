---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_11b826ed9d9211f1a54f525400f8a581
    ReservedCode1: Y69TgVgAr4S94BUi+UjkJnJxjbQVWBkzvrfPCvLgHoJbjVq5EYytOohG7JLvL1EJqGL0vJr6u1QY1kwQIMBt+B49tI4VgSvIIoh46BgT044H8NTSALLvzDFCr3zJ9aoxyFA9esvBoq145BixJsSc0ZsyOovce49ogMjxViKvJxz8oMTIs4Sc1ioF/NQ=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_11b826ed9d9211f1a54f525400f8a581
    ReservedCode2: Y69TgVgAr4S94BUi+UjkJnJxjbQVWBkzvrfPCvLgHoJbjVq5EYytOohG7JLvL1EJqGL0vJr6u1QY1kwQIMBt+B49tI4VgSvIIoh46BgT044H8NTSALLvzDFCr3zJ9aoxyFA9esvBoq145BixJsSc0ZsyOovce49ogMjxViKvJxz8oMTIs4Sc1ioF/NQ=
---

# PWM-LDCT v0.5 — Detectability task specification (published)

> Companion spec to `dataset_schema.md`. This document is the **published, normative
> declaration** of the task-based detectability benchmark used in Technical Validation
> (Table `tab:detectability_v05`, Figure `fig:dose_detectability_curve`). It fixes every
> parameter so the task is stated **before** the observer (Rung 1.1) and so any downstream
> method can reproduce the exact same task without contacting the release authors.
>
> Machine-readable mirror: `baselines/task_spec.json`. Canonical implementation:
> `baselines/src/pwm_ldct_baselines/observers.py` (`TaskSpec`).

---

## 1. Task statement (stated before the observer)

| Field | Value |
|---|---|
| Task class | SKE / BKS — signal-known-exactly, background-known-statistically |
| Signal | 2D Gaussian, $\sigma = 2.0$ px (~1.4 mm at 0.7 mm/px) |
| Peak contrast | 20 HU (subtle lesion) above background |
| Location | known — lesion centred in the extracted tissue ROI patch |
| Background | homogeneous soft-tissue ROI, **no anatomy** |
| Task label | `SKE-Gaussian20HU-s2px` |

## 2. Lesion insertion protocol (Rung 3)

The synthetic Gaussian lesion is inserted into the **low-dose INPUT slice**
(HU-space addition). The lesion is part of the anatomy, so it is present in both the
low-dose acquisition and the full-dose reference. The model reconstructs both the
lesion-present and the lesion-absent inputs; **detectability is measured on the model
OUTPUTS**. A method that merely smooths (e.g. Gaussian blur, $\sigma = 1.0$, $5 \times 5$
kernel) destroys the inserted signal, so its CNR falls below the Rose criterion (3.0)
even when PSNR rises — the **blur trap** (permanent control).

## 3. Noise ROI protocol

- Patch size: 32×32 px.
- Selection: `find_tissue_roi` scores random candidate patches (deterministic RNG
  seed 42) by closeness to soft-tissue HU (band **10–120 HU**), low internal gradient
  (Sobel, $\exp(-\bar{g}/20)$), and low internal std ($\exp(-\sigma_{HU}/50)$).
- The ROI is **never** placed over anatomy; detectability is never measured on
  anatomy-bearing regions.

## 4. Observers (stated, fixed parameters — Rung 1.2)

| Observer | Parameters |
|---|---|
| CNR (Rose index) | $(\mu_{present} - \mu_{absent}) / \sigma_{absent}$, Rose criterion **3.0** |
| CHO | 4 difference-of-Gaussians channels, no internal noise, Mann-Whitney AUC |
| NPWE | non-prewhitening matched filter with eye filter $\rho e^{-\rho/0.2}$ |

CHO AUC saturates at 1.000 for every method on this SKE task at the stated difficulty,
so CNR is the discriminating index **on the LIDC simulated-dose pilot (v0.5)**. On the
AAPM 2016 real-paired held-out set the insertion-based indices are **not** discriminative
(see §7, calibration note): the frequency-domain protocol of §6 is the calibrated
discriminating dimension for real anatomy.

## 5. Reporting rules

- Fidelity and detectability are reported **together** (both numbers or neither — §4 of
  the companion charter).
- Each result JSON under `baselines/results/*_results_det.json` embeds the task
  parameters and observer settings inline for self-description.
- The dose–detectability curve (`output/dose_detectability_curve.png`) reports CNR at
  the three simulated dose ratios (0.10/0.25/0.50) and names the **knee** (dose ratio at
  which CNR first crosses the Rose criterion 3.0, linear interpolation between adjacent
  simulated points; `not_reached` for methods that never cross).

## 6. Frequency-domain detectability protocol (calibrated for real anatomy)

> Added 2026-08-21 after AAPM real-paired calibration (protocol version
> `detectability-freq-v1`). On real anatomy, the inserted-signal CNR/CHO/NPWE indices are
> dominated by cross-slice background spread (65–75 HU) and give no separation between a
> learned denoiser and a pure smoother. The 1-px high-frequency band of the **real**
> anatomy (micro-structures of the lung/tissue) is the task signal that a denoiser must
> preserve and that a smoother erases.

| Field | Value |
|---|---|
| Signal model | 1-px high-frequency band $h = \mathrm{img} - G_{\sigma=1.0\mathrm{px}}(\mathrm{img})$ in HU space (Gaussian high-pass residual) |
| Target selection | `find_micro_peak`: local 32×32-px patch in the FD high-frequency residual with maximal HF energy, restricted to the soft-tissue ROI (same HU band as §3) |
| Index 1 — band energy ratio | $\mathrm{BandER} = \sum o_{hf}^2 / \sum \mathrm{fd}_{hf}^2$ on the same 48-slice detection subset; a smoother retains the least HF energy |
| Index 2 — template-match AUC | correlation of the FD HF micro-structure template with the model-output HF residual at the signal location (positive) vs an absent soft-tissue patch (negative); Mann-Whitney AUC |
| Calibrated threshold (AAPM held-out test, 2026-08-21) | blur $\mathrm{BandER} \le 0.35$ vs learned baselines $\ge 0.60$ (means over 4 patients) |

Calibration results: blur BandER mean 0.247 vs RED-CNN 0.636 / CTformer 1.040 / LEARN
0.631 — a 2.6–4.2× separation — while blur scores the **highest** SSIM (0.929) and a
PSNR comparable to the baselines (39.46 vs 39.49–40.98). The blur trap is therefore a
"high fidelity, low detectability" failure on real anatomy, measured by the frequency
domain.

## 7. AAPM real-paired calibration record (2026-08-21)

- Scope: AAPM 2016 held-out test (4 patients: L109/L192/L286/L333; splits
  `aapm_{train,val,test}.txt`, train 3 / val 3 / test 4).
- Attempted insertion grid: contrast HU ∈ {20, 40, 60} × σ px ∈ {0.5, 0.75, 1, 1.5, 2, 3},
  plus 80 HU/4 px and disk micro-structures 15–240 HU; in every grid cell CHO AUC
  saturated ≥ 0.92–1.000 and the blur-vs-model AUC gap ≤ 0.02 — the insertion protocol is
  not discriminative on real anatomy.
- Resolution: the frequency-domain protocol (§6) is the calibrated discriminative
  dimension; full held-out v2 numbers in
  `output/aapm_paired_baselines_v2.json` + `output/aapm_paired_baselines_v2_summary.md`.

## 8. Versioning

- `task_version: detectability-task-v1` (see `baselines/task_spec.json`).
- Any change to signal / contrast / location / ROI protocol / observer parameters
  increments the task version; results under the old version are not comparable to
  results under the new one.
- The frequency-domain protocol is versioned independently as `detectability-freq-v1`
  and is the calibrated discriminative index for real anatomy; the insertion task version
  is kept at v1 because its signal/insertion parameters are unchanged (calibration note in
  `task_spec.json` records the negative result of the contrast/sigma grid).
