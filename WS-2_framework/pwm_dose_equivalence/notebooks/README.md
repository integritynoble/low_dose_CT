# Tutorial notebooks

Four pedagogical tutorials — one per validated modality plus a user-implementable example — that walk you through computing a signal-equivalence credential end-to-end. Pairs naturally with [`../../paper_draft/reproduction_guide.md`](../../paper_draft/reproduction_guide.md), which is the reviewer-facing companion document.

| File | Modality | Task | Estimator | ε |
|---|---|---|---|---:|
| [`01_ct_lung_nodule_auc.py`](01_ct_lung_nodule_auc.py) | CT (validated) | lung-nodule detection | DeLong (auto-selected for AUC) | 0.05 |
| [`02_mri_meniscus_dice.py`](02_mri_meniscus_dice.py) | MRI (validated) | knee-meniscus segmentation | percentile bootstrap | 0.02 |
| [`03_pet_phantom_cr.py`](03_pet_phantom_cr.py) | PET (validated) | NEMA NU-2 IQ phantom contrast-recovery | percentile bootstrap (small-n warning) | 0.02 |
| [`04_optical_extending.py`](04_optical_extending.py) | Optical (user-implementable) | how to add a new modality | percentile bootstrap | 0.02 |

## Format

Each file is a `.py` script with `#%%` cell markers. It runs as a normal Python script:

```bash
python 01_ct_lung_nodule_auc.py
```

**and** as a Jupyter notebook — open in JupyterLab / VS Code / Spyder and cells render automatically. No `.ipynb` binary diffs; reproducible from source.

## Coverage

Across the four tutorials you will see:

* The single modality-agnostic `signal_equivalence_credential(...)` API call producing identical-shape credentials for CT / MRI / PET
* DeLong auto-selection for AUC tasks (~ 300× faster than the bootstrap variants per `proofs/estimator.md` §4)
* Percentile bootstrap for non-AUC metrics, with `sigma_delta_hint` triggering the (S1) CLT and (S4) Bernstein sample-size pre-flight
* BCa estimator opt-in for visible-skew bootstrap distributions (added in v0.2.0)
* The small-$n$ anti-conservativeness warning (n < 30 for non-AUC) per `proofs/estimator.md` §4c (V3-11)
* Content-addressed framework hash verification (SHA-256 of the v0.2 framework spec)
* The cohort-sizing implication: same WS-1 v0.5 n ≈ 208 cohort is comfortable for Dice but INDETERMINATE-dominated for AUC at the typical lung-nodule operating point
* How to extend the framework to a new modality (Tutorial 4) — define your own `T_r` operator, pass it through the existing `signal_equivalence_credential` API; the library does not need to be modified

## Cross-references

* [`../../paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) — the manuscript these tutorials supplement
* [`../../paper_draft/reproduction_guide.md`](../../paper_draft/reproduction_guide.md) — reviewer-facing companion that verifies every numerical claim
* [`../README.md`](../README.md) — library README + API reference
* [`../../theory/proofs/estimator.md`](../../theory/proofs/estimator.md) — the §§4 / 4a / 4b / 4c writeups the tutorials reference
* [`../../experiments/estimator_coverage/`](../../experiments/estimator_coverage/) — the four simulations the tutorials cite
