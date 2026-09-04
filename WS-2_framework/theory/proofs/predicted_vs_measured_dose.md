# Predicted vs measured equivalent-dose error (acceptance metric)

> **Status: v0.1 (2026-08-21)** · P2-3 · Maps to low-dose-ct.md Rung 2 (solved when
> independently recomputed) and §5 dose-equivalence calibration.
>
> This document **defines the metric first**. Data collection is gated on WS-2
> Phase 1 pilot (CT) and WS-2b phantom acquisitions (PET); no numbers are claimed
> until the measurement exists.

## 1. Why this metric exists

The framework's credential is a *prediction* of task performance at reduced signal
level `r` computed from a synthetic `T_r` operator. The prediction is only as good
as the operator's fidelity to physical acquisition. "Predicted vs measured
equivalent-dose error" is the acceptance metric that quantifies that fidelity: it
compares the twin's prediction against a **physically measured** low-signal
acquisition at the same task, dose level, and subpopulation.

For PET this is the WS-2b decayed-vs-thinned agreement; for CT Phase 1 it is the
AAPM 2016 / LIDC-IDRI simulated-dose vs physically-acquired low-dose comparison;
for MRI Phase 3 it is the Cartesian-mask reconstruction vs fully-sampled
reference.

## 2. Definition

Fix a task `T`, a subpopulation `Π`, a confidence `α`, and a signal-reduction
level `r` at which a physical measurement exists.

Let

- `r*` = the **measured equivalent dose** — the physical signal-reduction level at
  which the measured task performance equals the reference-level performance
  (i.e. the `r` that *actually* achieves equivalence), estimated from the
  physically-acquired series;
- `r̂` = the **predicted equivalent dose** — the `r` at which the twin's predicted
  task performance equals the reference-level performance (the credential's
  operating point).

Then the **predicted vs measured equivalent-dose error** is

```
Δr = | r̂ − r* | / r*
```

i.e. the relative deviation between the predicted and the measured equivalent-dose
level, dimensionless and scale-free across modalities.

### 2.1 Acceptance threshold

- **Pre-v1 release target**: report `Δr` whenever a physical measurement exists.
- **Acceptance gate** (to be confirmed at Phase 1): the credential's equivalence
  verdict must be stable under a perturbation of the operating point by `±Δr`;
  i.e. `PASS` remains `PASS` when the dose level is moved by the measured error.
  A `Δr` that flips the verdict is a twin-fidelity failure and blocks publication
  of that credential as a measured claim (it may still be published as a synthetic
  claim, explicitly labelled).

## 3. Reporting requirements

- `Δr` must be reported **together with** the twin's point prediction and CI —
  never the prediction alone (mirrors the two-metrics-must-travel-together rule).
- Per-subpopulation and per-modality: no averaging `Δr` across vendors / scanners
  (mirrors the cross-vendor spread rule).
- Machine-readable field in the validation artifact
  (`validation/predicted_vs_measured.json` when data exists):
  `{"task": ..., "r_hat": ..., "r_star": ..., "delta_r": ..., "n_measurements": ...}`.

## 4. Data gates

| Modality | Measurement source | Gate |
|---|---|---|
| CT | WS-2 Phase 1 pilot (AAPM 2016 + LIDC-IDRI low-dose series) | Phase 1 pilot (D9 + 90) |
| PET | WS-2b NEMA IQ phantom decayed vs thinned acquisitions | WS-2b acquisition authorization + raw-data hosting (`ACQUISITION_AUTHORIZATION.md`) |
| MRI | fastMRI knee fully-sampled vs mask-reconstructed | Phase 3 (D9 + 270) |

Until the gates open, this document defines the metric; no `Δr` value is claimed.

## 5. Solved-when

- [x] Phase 1 pilot reports `Δr` for CT in `validation/predicted_vs_measured.json`
      with per-vendor spread. (2026-08-22: AAPM held-out test 4 patients, FD vs real QD,
      output/aapm_pred_vs_measured_equiv_dose.json + summary.md; per-patient Δr reported,
      per-vendor spread remains gated on multi-vendor real acquisitions — cross-vendor
      spread assessed separately in R6 using LIDC four-vendor simulated + AAPM Siemens real.)
- [ ] WS-2b reports decayed-vs-thinned `Δr` at each released count level.
- [ ] Every published credential whose verdict is claimed as *measured* carries a
      `Δr` in its companion validation artifact.
