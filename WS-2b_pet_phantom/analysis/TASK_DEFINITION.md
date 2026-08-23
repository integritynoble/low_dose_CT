# PWM-PET-IQ 1.0 — phantom task definition & observer plan

> **Status: v0.1 (2026-08-21)** · P2-3 + P2-4 · Machine-readable mirror:
> `analysis/task_spec.json` · Implementation: `analysis/nema_metrics.py`
> (6/6 unit tests pass). Aligns with WS-1
> `baselines/task_spec.json` observer discipline (task stated before scoring)
> and with the WS-2 twin validity domain.

## 1. Why a task definition (and not just "measure CRC")

low-dose-ct.md's Rung 1.1 requires the *task* to be stated before any scoring:
signal vs background, contrast, location-known?, and the observer. This
workspace's dataset answers a specific question — *how does a fixed
reconstruction preserve known physical contrast as counts decrease?* — and it
deliberately does **not** answer a different question (*can an observer detect
lesions?*). Writing the task down prevents the first being misread as the second.

## 2. The task (P2-3)

**Task**: estimate, per sphere and per count level `r`, how well a single fixed
reconstruction recovers the *known* physical contrast of the NEMA NU-2 IQ
phantom, measured by NEMA NU 2-2018 percent contrast recovery, against the
released `ground_truth.json`.

| Element | Definition | Value |
|---|---|---|
| Signal (lesion) | NEMA NU-2 IQ phantom spheres | 10 / 13 / 17 / 22 / 28 / 37 mm internal diameter |
| Signal class | Hot spheres 10–22 mm; cold spheres 28–37 mm | fill ratio 4:1 (SBR) |
| Background | Uniform phantom background + low-density lung insert | NEMA 12-region × 5-slice ROI set |
| Contrast | True sphere:background activity ratio | **known by construction** (4:1); measured fill concentrations in `ground_truth.json` |
| Location | Sphere centres and diameters | **known** (physical geometry, recorded in `ground_truth.json`; VOI placement is a deterministic geometry step, not a search) |
| Count axis | `r ∈ {1.0, 0.50, 0.25, 0.10}` | decayed (physical) + thinned (list-mode Poisson, seeded) |
| Confound control | One fixed reconstruction protocol for every series | reconstruction eliminated as a variable |

**Explicitly NOT in the task**: lesion detectability in the decision-theoretic
sense (AUC of a CHO/NPWE-style observer, free-response detection, reader
studies). Contrast recovery measures *signal fidelity* under a known ground
truth; it is not a detectability endpoint. Reporting it as such would be a Rung
1 / Rung 3 category error.

## 3. Observer plan (P2-3)

- **Observer = NEMA-defined numeric metrics**, computed by
  `analysis/nema_metrics.py` (pure functions over ROI means, unit-tested):
  - percent contrast recovery, hot `Q_H` and cold `Q_C`;
  - background variability `N_j`;
  - contrast-to-noise `CNR`;
  - decayed-vs-thinned Bland–Altman bias / 95 % limits (the central validation:
    measures the list-mode-thinning model error assumed by WS-2 PET `T_r`);
  - across-realization mean + population variance (noise-replicate budget).
- **No reader panel** and **no channelized-observer detectability experiment in
  1.0**. Rationale: the phantom's spheres are known-location, known-contrast
  physical signals; the scientific claim of this descriptor is about *measured
  contrast fidelity vs counts*, which CRC answers directly. A future observer
  experiment (e.g. CHO on reconstructed volumes) would be a **separate study**
  with its own task definition and its own report — it is out of scope here and
  must not be inferred from the CRC tables.

## 4. Low-activity → dose mapping (P2-4)

The four count levels are **not four isolated operating points**; they are a
dose axis. The mapping rule:

```
r = A_reduced / A_reference        (injected-activity ratio, same frame duration)
⇒ same r is the same relative dose fraction: D(r) = r × D_reference
```

- **Decayed series**: `A_reduced` is achieved physically by tracer decay
  (`A(t) = A_0 e^{-λt}`); measured by dose calibrator, decay-corrected per
  series, recorded in `metadata.json`. These are *true* low-dose acquisitions.
- **Thinned series**: a seeded list-mode Poisson thinning at rate `r` of the
  full-count reference models the same dose fraction at the coincidence-count
  level; `thinning/seed_recipe.json` makes each realization bit-reproducible.
- **Twin link**: `r` in this dataset is exactly the WS-2 PET signal-reduction
  level `T_r`. The decayed-vs-thinned agreement therefore calibrates the WS-2
  twin's PET reduction model against physical acquisition — converting the
  framework's "thinning model" from an assumption into a measured quantity.
- **Explicit non-claim**: thinning matches count statistics but **not**
  activity-dependent detector physics (dead-time, pile-up, activity-dependent
  randoms fraction). The magnitude of that discrepancy is *measured* here
  (Bland–Altman + randoms-fraction deltas), not assumed away.

## 5. Solved-when (gates)

- [ ] `task_spec.json` + this file reviewed and locked before Phase A design
      freeze (SUBMISSION_CHECKLIST §1).
- [ ] CRC / variability / CNR / Bland–Altman / replicate stats emitted only by
      committed `analysis/` scripts over deposited records (never hand-typed).
- [ ] No detectability (AUC/CHO/reader) number is claimed anywhere in the
      descriptor; Limitations §Phantom-not-patient already scopes this.
