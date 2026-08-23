# Digital-twin validity domain (L2 spec / twin member refusal)

> **Status: v0.1 (2026-08-21)** · P1-2 · Maps to low-dose-ct.md *4 layers — Digital
> twin / L2 spec / twin member refusal* and Rung 2 (solved when independently
> recomputed).
>
> Companion: `theory/dose-equivalence-framework.md`, `theory/proofs/pet_reduction.md`
> (activity-reduction `T_r`), `WS-2b_pet_phantom/ACQUISITION_AUTHORIZATION.md`
> (embodied acquisition grant), `README.md` §Digital-twin validity domain.

## 1. What the twin is

The `pwm_dose_equivalence` framework is a **digital twin of the signal-reduction
experiment**: given a full-signal acquisition and a reduction operator `T_r`
(Poisson CT channel, Cartesian MRI mask, list-mode PET thinning), it predicts the
distribution of task performance at level `r` without physically re-acquiring the
low-signal data. A credential `(r, T, ε, α, Π)` is the twin's testable output.

The twin is **not** a simulator of the full physics chain. It predicts
signal-statistics-mediated performance changes, not every image-quality effect.

## 2. Validity domain

The twin is valid **only** where the reduction operator `T_r` is a faithful model of
the corresponding physical acquisition. By construction this holds when:

| Domain requirement | CT (Poisson channel) | MRI (Cartesian mask) | PET (list-mode thinning) |
|---|---|---|---|
| Reduction acts on raw signal statistics | photon noise | k-space sampling | coincidence counts |
| Scatter / attenuation physics | assumed fixed; `T_r` does not re-model them | n/a (mask does not change physics) | **scatter / attenuation / randoms treated as fixed and independent of `r`** |
| Beam-hardening | outside domain (fixed) | n/a | n/a |
| Detector non-linearity / dead-time / pile-up | outside domain unless explicitly modeled | n/a | **outside domain** (thinning omits activity-dependent detector physics) |
| Motion | outside domain (twin assumes static anatomy) | outside domain unless motion modeled | outside domain |
| Tracer kinetics (PET) | n/a | n/a | outside domain (static distribution assumed) |

The PET row is the reason `WS-2b_pet_phantom` exists: physically-decayed
acquisitions are the *measurement* that bounds the thinning-model error (the
decayed-vs-thinned agreement endpoint), so the twin's PET validity domain is
**empirically verified** rather than assumed.

## 3. Refusal rule (twin member refusal)

A twin member (credential) **must refuse** to be scored when any of the following
holds:

1. **Domain-exit input**: the subpopulation `Π` or acquisition metadata implies
   physics outside the domain table above (e.g. a PET series where randoms fraction
   is materially `r`-dependent, or a CT series with known beam-hardening that
   `T_r` does not model). Refusal = return `INDETERMINATE` with a machine-readable
   refusal code, not `FAIL` — `FAIL` would imply the twin *scored* the case.
2. **Out-of-domain endpoint**: the task metric `T` is a detectability endpoint whose
   observer specification is not declared (see `task_equivalence.py` / P1-1). A
   detectability claim without a published observer spec is refused.
3. **Missing physics evidence** (PET only): the decayed-vs-thinned agreement is not
   reported for the count level. The twin's PET `T_r` is valid only where the
   thinning-model error has been measured.
4. **Label noise exceeds the refusal threshold**: documented inter-reader
   disagreement greater than `ε/2` (already in the manuscript's Label-noise refusal
   threshold).

Refusal codes are emitted as `INDETERMINATE` verdicts with
`sample_size_check`-style structured fields; they are **not** evidence of
non-equivalence (mirrors the estimator.md §4a regime).

## 4. Scope of this writeup

This writeup declares the domain and the refusal rule at the theory level. The
library-level enforcement hooks are:

- `ObserverSpec` (P1-1) — refuses detectability endpoints without a declared observer.
- `WS-2b` decayed-vs-thinned endpoint — the empirical gate for the PET thinning
  domain.
- `README.md` §Digital-twin validity domain — the one-paragraph user-facing refusal
  statement.

## 5. Solved-when

- [ ] Every published credential carries a machine-readable domain tag (CT / MRI /
      PET + physics assumptions), and out-of-domain inputs produce `INDETERMINATE`
      with a refusal code in ≥ 1 integration test.
- [ ] WS-2b decayed-vs-thinned agreement is reported at every released count level
      (data-blocked until acquisition; see `WS-2b/SUBMISSION_CHECKLIST.md`).
