# L2 Spec — Signal-Equivalence Framework (covers dose / sampling / activity reduction)

**Status:** ⏳ Draft pending Phase B framework development (months 5-12 post-mainnet).
**Target on-chain date:** D9 + 365.
**Backing paper:** [`../WS-2_framework/paper_draft/`](../WS-2_framework/) (target venue: ***Nature Methods*** primary; *IEEE TMI* / *Medical Image Analysis* fallback).
**Workstream:** WS-2.

---

## Scope: modality-general

The L2 spec is **not CT-specific.** It applies to any biomedical-imaging acquisition where signal is intentionally reduced from a reference:

| Modality | Signal-reduction parameter `r` | Phase A coverage |
|---|---|---|
| **CT** | `r = mA_red / mA_ref` (dose ratio) | ✅ Primary validation (Phase 1 pilot weeks 9-12) |
| **MRI accelerated reconstruction** | `r = 1/R` (4× acceleration ⇒ `r = 0.25`) | Phase B extension (fastMRI knee dataset) |
| **PET low-dose / low-activity** | `r = A_red / A_ref` (injected activity ratio) | Phase B extension (public phantom data acceptable for v1) |

The L2 spec ships when CT + at least one of {MRI, PET} have a working validator in `pwm_dose_equivalence`.

---

## Formal definition

Let `T` denote a clinical task with a scalar performance metric `m: outputs → ℝ`. Let `S_ref` denote a reference (full-signal) acquisition operator and `S_red = r · S_ref` (with `r ∈ (0, 1]`) a reduced-signal acquisition. Let `M` be a reconstruction method mapping reduced-signal inputs to reconstructed images. Let `Π` denote a patient subpopulation.

**Definition.** Method `M` is **signal-equivalent at level (r, T, ε, α)** over subpopulation `Π` iff:

```
Pr_{x ~ Π} [ | m(M(S_red(x))) − m(reference(S_ref(x))) | < ε ] ≥ 1 − α
```

The 5-tuple `(r, T, ε, α, Π)` is the **signal-equivalence credential** of method `M`.

---

## What this replaces

Existing vendor claims of the form:

> *"Our deep-learning reconstruction enables 50% dose reduction."* (CT)
> *"Our reconstruction supports 4× MRI acceleration."* (MRI)
> *"Our pipeline enables 25%-activity FDG-PET scans."* (PET)

…are scientifically meaningless without specifying the task, the subpopulation, the equivalence margin, and the statistical confidence. The L2 spec mandates all five — **across modalities, with the same formalism**.

---

## Estimation protocol

A method `M` is **certified** at level `(r, T, ε, α, Π)` via:

1. Draw `n ≥ n*(ε, α)` patients i.i.d. from `Π` (sample-size requirement derived in the framework paper).
2. For each patient, acquire (or simulate) the paired `(x_{D_red}, x_{D_ref})`.
3. Compute `m(M(x_{D_red}))` and `m(reference(x_{D_ref}))` per patient.
4. Bootstrap the equivalence indicator over `n` patients; compute the lower confidence bound.
5. If lower CB ≥ `1 − α`, certify; else reject.

Bootstrap N = 10,000 unless otherwise specified. Random seed must be recorded and reproducible.

---

## Reference implementation

The `pwm_dose_equivalence` Python package (`framework/pwm_dose_equivalence/`) is the reference implementation. Any submission claiming a 5-tuple credential must compute it via this library or an equivalent that produces bit-identical results on the L3 benchmark.

---

## Registry payload (draft — finalize at submission time)

```yaml
pwm_l2_spec:
  name: signal_equivalence_v1
  version: 0.1.0
  framework_paper:
    arxiv: TBD
    venue: TBD                 # nature_methods (primary) / ieee_tmi (fallback)
    doi: TBD
  reference_library:
    name: pwm_dose_equivalence    # library name preserved for PyPI continuity; covers all modalities
    pypi: TBD
    repo: TBD
    pinned_version: TBD
  supported_modalities:        # at least 2 must be live at L2 registration time
    - ct                       # primary, validated against AAPM 2016 + WS-1 dataset
    - mri                      # Phase B extension, validated against fastMRI
    - pet                      # stretch, public phantom data
  schema:
    credential:
      signal_ratio: float      # r in (0, 1]; interpretation per modality (see field below)
      modality: enum[ct, mri, pet]
      ratio_interpretation: str  # e.g., "mA_ratio_CT" / "1_over_acceleration_MRI" / "activity_ratio_PET"
      task:
        name: str
        metric: str            # e.g., "auc", "dice", "sensitivity_at_fpr_0.1"
        target: float
      epsilon: float           # equivalence margin
      alpha: float             # confidence level
      subpopulation: str
      bootstrap_n: int
      seed: int
    verdict:
      verdict: enum[PASS, FAIL]
      performance_mean: float
      performance_ci: tuple[float, float]
      sample_size: int
  content_hash: sha256:TBD
```

---

## Pending work (gate to registration)

- [ ] Theoretical depth: concentration inequalities, sample-size derivation.
- [ ] Multi-task extensions (cross-task credentials).
- [ ] Cross-subpopulation extensions.
- [ ] `pwm_dose_equivalence` library at v1.0.0 on PyPI with **≥ 2 modality validators** (CT + MRI minimum; PET stretch).
- [ ] Phase 1 pilot (see WS-2 [`README.md`](../WS-2_framework/README.md)) confirms end-to-end implementability on CT.
- [ ] Phase B multi-modality validation: at least one of {MRI fastMRI, PET phantom} working.
- [ ] Paper submitted to ***Nature Methods*** (primary) or *IEEE TMI* / *Medical Image Analysis* (fallback).
- [ ] Registry-format final (depends on stabilized PWM Registry post-mainnet).

---

## Cross-references

- Framework workstream: [`../WS-2_framework/README.md`](../WS-2_framework/README.md)
- Framework formal definition (this spec hashes a frozen version): [`../WS-2_framework/theory/dose-equivalence-framework.md`](../WS-2_framework/theory/dose-equivalence-framework.md)
