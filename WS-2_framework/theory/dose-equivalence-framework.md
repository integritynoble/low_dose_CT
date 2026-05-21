# Signal-Equivalence Framework — Formal Definition (v0.1)

**Status:** Working draft. Team iteration expected. *Not* the manuscript.
**Last revised:** 2026-05-20.
**Supersedes:** the informal one-line version in [`../README.md`](../README.md).
**Will be superseded by:** v0.2 after literature pass (see [`open_questions.md`](open_questions.md) §1).

This document sharpens the framework definition that [`../README.md`](../README.md) states informally. The informal version conflates several things that need to be separated before any theorem about the framework can be stated cleanly. Each sharpening is flagged **[SHARPEN-N]** below; the rationale is in §11.

---

## 1. Setting: an imaging modality as a measurable triple

Fix a **modality** as a triple `M = (𝒳, 𝒮, 𝒴)`:

- `𝒳` — **patient space** (measurable). An element `x ∈ 𝒳` is a patient at scan time: anatomy + physiology + position. Treated as latent; never observed directly.
- `𝒮` — **acquisition space** (measurable). An element `s ∈ 𝒮` is a raw measurement (CT sinogram, MRI k-space samples, PET list-mode counts).
- `𝒴` — **reconstruction space** (measurable). An element `y ∈ 𝒴` is a reconstructed image (or volume, or video).

A modality is equipped with a **reference acquisition operator** `S_ref : 𝒳 → 𝒫(𝒮)` (probabilistic, because acquisition is noisy): `S_ref(x)` is the distribution over raw measurements that the full-signal scanner produces on patient `x`.

For CT, `S_ref(x)` is the Poisson-noise-corrupted projection at the reference tube current `mA_ref`. For MRI, `S_ref(x)` is the fully-sampled k-space measurement at reference SNR. For PET, `S_ref(x)` is the list-mode draw at reference injected activity.

> **[SHARPEN-1]** The informal version writes "`x`" interchangeably for "patient" and "image." We need the distinction because the signal-reduction operator acts on *the acquisition*, not on the patient.

---

## 2. The signal-reduction operator

Let `r ∈ (0, 1]` be a **signal ratio**. A **signal-reduction operator at level r** is a map

```
T_r : 𝒫(𝒮) → 𝒫(𝒮)
```

with the interpretation: if `s ~ S_ref(x)`, then `s' ~ T_r(S_ref(x))` is the raw measurement that *would have been produced* if the scanner had been operated at reference-level scaled by `r`.

Define `S_red(x; r) := T_r(S_ref(x))` as the **reduced-signal acquisition** at ratio `r`.

The modality-specific instantiations of `T_r`:

| Modality | `T_r` instantiation | Comment |
|---|---|---|
| **CT** | If `s_ref ~ Poisson(λ(x))`, then `s_red ~ Poisson(r · λ(x))` | Tube-current reduction; expected count scales linearly, noise scales as `√r` |
| **MRI** | `s_red = Ω_r · s_ref` where `Ω_r` is a k-space subsampling mask with `|Ω_r| / |Ω_full| = r` | Mask realization is itself a random variable; `T_r` includes the mask distribution |
| **PET** | If `s_ref ~ Poisson(μ(x))`, then `s_red ~ Poisson(r · μ(x))` | Injected-activity reduction; same Poisson scaling as CT |
| **Optical (stretch)** | If `s_ref ~ Poisson(φ(x) · t_ref)`, then `s_red ~ Poisson(φ(x) · r · t_ref)` | Reduced exposure time |

> **[SHARPEN-2]** The informal version writes `S_red = r · S_ref`. That is dimensionally wrong: `S_red` is an *operator*, not a scaled signal. The scalar `r` parameterizes the operator family; it does not multiply the operator itself.

A modality is **signal-reducible** if a family `{T_r}_{r ∈ (0,1]}` is defined; all three target modalities (CT, MRI, PET) are signal-reducible under standard physics.

---

## 3. Reconstruction methods

A **reconstruction method** is a measurable map

```
M : 𝒮 → 𝒴
```

(deterministic; stochastic methods are handled by averaging over the method's seed in §6).

The composed map `M ∘ T_r ∘ S_ref : 𝒳 → 𝒫(𝒴)` is "reconstruct from a reduced-signal scan of patient `x`": it returns a distribution over reconstructions for fixed patient `x`, with randomness coming from (a) acquisition noise and (b) the reduction operator `T_r` if `T_r` is itself stochastic (e.g., MRI mask draw).

We compare two such composed maps:

| Map | Interpretation |
|---|---|
| `M_red := M ∘ T_r ∘ S_ref` | Method `M` applied to reduced-signal scans |
| `M_ref := M_baseline ∘ S_ref` | A **reference method** `M_baseline` applied to full-signal scans |

> **[SHARPEN-3]** The informal version uses "reference" ambiguously: sometimes the *reference acquisition* (full-signal scan), sometimes the *reference algorithm* (a specific reconstruction). We separate them: the reference acquisition is `S_ref`; the reference method is `M_baseline`. The reference *map* `M_ref = M_baseline ∘ S_ref` is the standard against which `M_red` is judged.
>
> Canonical `M_baseline` choices per modality:
> - CT: filtered back-projection (FBP) at full dose, or the vendor's standard iterative reconstruction (the radiologist's *de facto* reference)
> - MRI: GRAPPA / SENSE on fully-sampled k-space at reference SNR
> - PET: OSEM with the vendor's standard regularization at reference activity
>
> The choice of `M_baseline` is **part of the framework specification** and is recorded in the 5-tuple's `subpopulation` field as a sub-key. Different choices of `M_baseline` give different equivalence relations; the framework does *not* claim there is one "true" reference.

---

## 4. Tasks and performance

A **task** is a measurable map

```
T : 𝒴 → 𝒟
```

from reconstructions to a clinical decision space `𝒟`. Examples:

| Task name | `𝒟` | Example |
|---|---|---|
| Lesion detection | `{0, 1}` or `[0, 1]` | "Lung nodule ≥ 5 mm present?" → binary or detector confidence |
| Lesion localization | `{bounding boxes}` | "Where are the lung nodules?" |
| Segmentation | `{0, 1}^Ω` | Per-voxel mask of organ/lesion |
| Quantification | `ℝ_+` | Lesion volume in mm³ |

Ground truth `g(x) ∈ 𝒟` for patient `x` is established by a documented adjudication protocol (≥ 2 board-certified radiologists with majority vote, biopsy-confirmed, etc.); the protocol is part of the 5-tuple specification.

A **performance metric** is a functional

```
P : 𝒟 × 𝒟 → ℝ
```

with `P(T(y), g(x))` evaluated as "how well did the task output on reconstruction `y` agree with ground truth `g(x)`." Higher is better (rescale if not).

| Task type | Canonical `P` |
|---|---|
| Binary detection | indicator `1[T(y) = g(x)]`, or per-task ROC at fixed FPR |
| Detection over cohort | AUC, sensitivity at fixed FPR |
| Segmentation | Dice coefficient, Hausdorff distance |
| Quantification | `1 - |T(y) - g(x)| / g(x)` (relative-error → "skill") |

> **[SHARPEN-4]** Performance is *not* a property of a single image — it is a property of `(reconstruction, task output, ground truth)`. The informal version writes `Performance(M, S_red(x), T)` which obscures this. We write `P(T(y), g(x))` where `y ~ M_red(x)`.

---

## 5. Subpopulations

A **subpopulation** is a probability measure `Π` on `𝒳` together with an operational description (the recruitment / inclusion criteria a clinical-trial reader could use to verify draws from `Π`).

Examples:

| `Π` operational description | Notes |
|---|---|
| Adults aged 30-79 with current/former smoking history undergoing lung-cancer screening at a US academic medical center between 2018-2024 | LIDC-IDRI cohort proxy |
| Pediatric patients aged 5-17 undergoing chest CT for trauma evaluation at a Level-1 trauma center | A different `Π` — a method equivalent on adults may *not* be equivalent here |
| Oncology patients undergoing FDG-PET for treatment-response monitoring after 2 cycles of chemotherapy | A PET-specific `Π` |

The framework makes no claim about generalization between subpopulations: a 5-tuple credential is **explicitly conditional on `Π`**.

> **[SHARPEN-5]** Subpopulation is a *measure*, not a label. Two credentials with the same `Π` label but different operational definitions are different credentials.

---

## 6. The signal-equivalence definition (v0.1 canonical)

We give two formulations and pick one as canonical.

### 6a. Aggregate formulation (**canonical**)

Method `M` is **signal-equivalent to `M_baseline` at level `(r, T, ε, α)` over subpopulation `Π`**, written

```
M  ≡_(r, T, ε, α, Π)  M_baseline
```

iff

```
| E_{x ~ Π} [ E_{y ~ M_red(x)} P(T(y), g(x)) ]
  - E_{x ~ Π} [ E_{y' ~ M_ref(x)} P(T(y'), g(x)) ] |  <  ε       (*)
```

with confidence `≥ 1 - α` under the estimator described in §7.

Read: *"the population-mean task performance of `M` on reduced-signal scans is within `ε` of the population-mean task performance of `M_baseline` on full-signal scans, with confidence `1 - α`."*

### 6b. Per-patient formulation (stronger; defined for reference)

`M` is **per-patient signal-equivalent** iff

```
P_{x ~ Π} [ | E_{y ~ M_red(x)} P(T(y), g(x))
            - E_{y' ~ M_ref(x)} P(T(y'), g(x)) |  <  ε ]   ≥  1 - α
```

This says the *per-patient* performance gap is small with high probability over the patient draw. Strictly stronger than 6a (per-patient implies aggregate; converse false).

### Canonical choice

**Adopt 6a as canonical.** Reasons:

1. Aggregate matches how clinical-trial endpoints are reported (population means with CIs).
2. Per-patient is too strict for clinical adoption: patient-level swap-equivalence would forbid even small re-ranking of borderline cases.
3. The estimator (bootstrap on patients drawn from `Π`) directly delivers 6a; 6b requires a more elaborate concentration argument.

6b is kept in the framework as an **optional strengthening**: a credential may be tagged `formulation=per_patient` and held to the stricter bound. Default `formulation=aggregate`.

> **[SHARPEN-6]** The informal version conflates 6a and 6b ("`P_x [...] ≥ 1 - α`" looks per-patient, but the bracketed quantity is `|Performance(M) - Performance(ref)|` without an inner expectation, which is ambiguous). We separate them explicitly and commit to 6a as default.

---

## 7. Estimator

The natural estimator of the left-hand side of (*) is a **two-sample bootstrap on independent patient draws** from `Π`:

```
Input:  test set {x_1, ..., x_n} drawn IID from Π; ground truth {g(x_i)}.
        Method M; reference method M_baseline; reduction ratio r.

For k = 1, ..., n:
    sample s_red ~ T_r(S_ref(x_k));     y_red := M(s_red);     a_k := P(T(y_red), g(x_k))
    sample s_ref ~ S_ref(x_k);          y_ref := M_baseline(s_ref); b_k := P(T(y_ref), g(x_k))

For b = 1, ..., B bootstrap replicates:
    resample (a_k, b_k) pairs with replacement; compute mean difference
    Δ_b := mean_k(a_k) - mean_k(b_k)

Compute |percentile-CI(Δ, 1-α)|.
Verdict PASS iff CI ⊂ (-ε, ε).
```

`B = 10,000` for default 5-tuple computation; `n` set by the sample-size formula in [`open_questions.md`](open_questions.md) §2 (currently open — pre-registered targets are `n ≥ 200` for `ε = 0.02, α = 0.05` on AUC-type metrics, justified empirically in v0.1, formally in v0.2+).

Pairing `(a_k, b_k)` is essential: the comparison is *paired* on patient because the reduction operator acts on the same patient's acquisition.

---

## 8. Properties (claims; proofs in `proofs/` later)

The framework should satisfy:

| Property | Statement | Status |
|---|---|---|
| **Reflexivity** | `M_baseline ≡_(1, T, 0, 0, Π) M_baseline` (at full signal, the baseline is trivially equivalent to itself with `ε = 0`) | Immediate |
| **Monotonicity in r** | If `M ≡_(r, T, ε, α, Π) M_baseline` and `r' > r`, then `M ≡_(r', T, ε, α, Π) M_baseline` (more signal is easier) | Plausible; not always true (some methods are tuned for a specific `r` and degrade above) — **open** |
| **Monotonicity in ε** | If `M ≡_(r, T, ε, α, Π) M_baseline` and `ε' > ε`, then `M ≡_(r, T, ε', α, Π) M_baseline` | Immediate (looser margin) |
| **Monotonicity in α** | If `M ≡_(r, T, ε, α, Π) M_baseline` and `α' > α`, then `M ≡_(r, T, ε, α', Π) M_baseline` | Immediate (less confidence) |
| **Task-restriction** | Equivalence on task `T` does *not* imply equivalence on task `T'` ≠ `T` | True by counter-example (denoising-aggressive methods pass detection but fail texture-preservation tasks); recorded to prevent misuse |
| **Subpopulation-restriction** | Equivalence on `Π` does *not* imply equivalence on `Π'` ≠ `Π` | True by counter-example (adult-trained methods often fail on pediatric `Π`); recorded |
| **Composition** | If `M ≡_(r, ...) M_baseline` and `M_baseline ≡_(r', ...) M_baseline'` then `M ≡_(?, ...) M_baseline'` for some `?` | **Open** — composition law unknown; conservative bound is `?  = r · r'` for some assumptions |

**The Monotonicity-in-r property is the key open one** — it is *not* unconditionally true (a method may overfit to one `r`), but a useful sub-claim is "monotonicity holds for methods trained or tuned across the `r ∈ [r_min, 1]` range." Formalizing this conditioning is open work.

---

## 9. The 5-tuple credential

The output of evaluating method `M` against `M_baseline` at `(r, T, ε, α, Π)` is a **credential record**:

```jsonc
{
  "schema_version": "pwm-signal-equivalence/v0.1",
  "credential": {
    "method": {
      "name": "method-identifier",
      "code_hash": "sha256:...",
      "weights_hash": "sha256:...",
      "runbundle_cid": "ipfs://...",
      "seed": 42
    },
    "modality": "CT",                         // CT | MRI | PET | ...
    "signal_ratio": 0.25,
    "reference_method": {
      "name": "FBP@full_dose",
      "code_hash": "sha256:..."
    },
    "task": {
      "name": "lung_nodule_5mm_detection",
      "decision_space": "binary",
      "ground_truth_protocol": "majority-vote-2-radiologists",
      "metric": "auc",
      "operating_point": "fpr=0.05"
    },
    "subpopulation": {
      "label": "adult_chest_smoker_screening_US_2018_2024",
      "operational_definition": "see Π-spec link",
      "source_dataset": "LIDC-IDRI v4",
      "n_test_patients": 412
    },
    "epsilon": 0.02,
    "alpha": 0.05,
    "formulation": "aggregate",               // aggregate (default) | per_patient
    "estimator": {
      "type": "paired-bootstrap",
      "B": 10000,
      "seed": 42
    },
    "result": {
      "verdict": "PASS",                      // PASS | FAIL | INDETERMINATE
      "delta_mean": -0.011,
      "delta_ci_95": [-0.024, 0.001],
      "performance_method_mean": 0.961,
      "performance_reference_mean": 0.972,
      "performance_method_ci_95": [0.948, 0.973],
      "performance_reference_ci_95": [0.965, 0.979]
    }
  },
  "pwm": {
    "l2_framework_hash": "sha256:..."         // hash of this dose-equivalence-framework.md at the version this credential commits to
  }
}
```

`INDETERMINATE` is permitted: the CI may straddle `ε` (cannot confidently call PASS or FAIL); reported transparently. The framework rejects forced binarization.

---

## 10. Notation glossary

| Symbol | Meaning |
|---|---|
| `𝒳` | Patient space (latent) |
| `𝒮` | Acquisition (raw measurement) space |
| `𝒴` | Reconstruction space |
| `x ∈ 𝒳` | A patient |
| `s ∈ 𝒮` | A raw acquisition |
| `y ∈ 𝒴` | A reconstruction |
| `S_ref` | Reference acquisition operator `𝒳 → 𝒫(𝒮)` (full-signal scan) |
| `T_r` | Signal-reduction operator `𝒫(𝒮) → 𝒫(𝒮)` at level `r ∈ (0, 1]` |
| `S_red(·; r)` | Composition `T_r ∘ S_ref`; the reduced-signal acquisition |
| `M` | Reconstruction method under evaluation |
| `M_baseline` | Reference reconstruction method (against which `M` is judged) |
| `M_red`, `M_ref` | `M ∘ T_r ∘ S_ref` and `M_baseline ∘ S_ref` respectively |
| `T` | Task (post-reconstruction decision map) `𝒴 → 𝒟` |
| `𝒟` | Decision space |
| `g(x)` | Ground-truth decision for patient `x` |
| `P` | Performance metric `𝒟 × 𝒟 → ℝ` |
| `Π` | Subpopulation probability measure on `𝒳` |
| `r` | Signal ratio (CT dose ratio, MRI 1/acceleration, PET activity ratio) |
| `ε` | Equivalence margin (absolute, in metric's native units) |
| `α` | Significance level for the bootstrap CI |

---

## 11. Sharpenings — rationale summary

The six **[SHARPEN-N]** flags above are the substantive deltas from the README definition. Recapped:

1. **Patient vs image distinction** — `S_red` acts on the acquisition of a patient, not on the patient. Cleaner type signatures throughout.
2. **`T_r` is an operator, not a scalar multiplier** — `r` parameterizes a family; `r · S_ref` was dimensionally wrong.
3. **Reference acquisition vs reference algorithm** — separated as `S_ref` (operator) and `M_baseline` (method); the "reference" of the comparison is `M_baseline ∘ S_ref`.
4. **Performance acts on `(task output, ground truth)`** — not on `(method, scan, task)`. Cleaner functional form.
5. **Subpopulation is a measure** — not a label; operational definition is required.
6. **Aggregate vs per-patient formulations separated** — aggregate is canonical (matches clinical-trial endpoint reporting); per-patient is opt-in stronger.

These are working-draft sharpenings, not theorems. The Nature Methods version will live or die on (a) whether the choices in §3 and §6 hold up to reviewer scrutiny, (b) whether the open properties in §8 close cleanly, and (c) whether the worked examples in §2 (MRI + PET) survive empirical validation.

---

## 12. What this document is NOT

- **Not** a theorem. The framework so far is a *language*; the theorems (concentration, sample-size, composition) are open. See [`open_questions.md`](open_questions.md).
- **Not** the L2 spec. The L2 spec on PWMRegistry will hash a frozen version of this document at submission time; v0.1 is **not** that frozen version.
- **Not** modality-complete. CT is grounded; MRI/PET instantiations of `T_r` in §2 are correct in expectation but the precise stochastic models (especially MRI mask distributions) need empirical validation in Phase B.
- **Not** a substitute for the manuscript. Manuscript prose will compress most of this and expand the §8 properties into proofs.

---

## 13. Cross-references

- [`../README.md`](../README.md) — high-level WS-2 scope and modality table.
- [`open_questions.md`](open_questions.md) — what's not yet proven; the work list for Phase B theory time.
- [`../README.md`](../README.md) — WS-2 workstream README (Goals / Tasks / Timeline; includes the Phase 1 pilot that empirically tests this definition on three CT baselines and the IRB-lag theory window in months 5-9).
- [`../../pwm_integration/l2_spec.md`](../../pwm_integration/l2_spec.md) — the eventual on-chain L2 spec will hash a frozen version of this file.

---

*Draft v0.1 — team iteration expected. Revise as related-work pass and Phase 1 pilot results land.*
