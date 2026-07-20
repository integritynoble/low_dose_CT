# MRI mask-distribution decision (`open_questions.md` §7)

**Status:** v0.1 — decision recorded 2026-06-02 alongside the v0.2 manuscript.
**Cross-references:** [`open_questions.md`](../open_questions.md) §7; manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) §framework (clarification C5); [`experiments/cross_modality_consistency/`](../../experiments/cross_modality_consistency/) (synthetic Cartesian-mask channel).

---

## 1. The question

Framework §2 row 2 specifies MRI signal reduction as `s_red = Ω_r · s_ref`, where `Ω_r` is a $k$-space subsampling mask satisfying `|Ω_r| / |Ω_full| = r`. The mask realisation $\Omega_r$ is itself a random variable: the operator $T_r$ in the framework is *parametric in a mask distribution*. The three candidate mask distributions used in practice are:

1. **Uniform random** undersampling at rate $r$ — the cleanest theoretical object, used in most early compressed-sensing MRI papers (Lustig et al. 2007).
2. **Variable-density Cartesian** — denser sampling near the $k$-space centre, sparser at the edges; the fastMRI dataset reference (Zbontar et al. 2020).
3. **Equispaced + central-$k$ fully-sampled** — common in vendor implementations (Siemens GRAPPA / GE ARC) where a fixed central calibration region is reconstructed without acceleration.

These are not equivalent operators: a reconstruction method optimised for one mask family may degrade under another. Three credentials issued under three mask families on the same patient cohort are three distinct credentials, not three measurements of one.

Two ways the framework could handle this:

| Option | What | Cost |
|---|---|---|
| **(a) Canonical mask** | Specify one mask family per acceleration rate as the framework's reference $T_r$ for MRI; all credentials use that family. | Locks the framework to a single operational choice; reviewers will ask "why this one and not the others." |
| **(b) Record family in credential** | Extend the 5-tuple to `(r, T, ε, α, Π, mask_family)` for MRI. | Bloats the credential schema; the 5-tuple uniformity across modalities is lost. |

A third option dominates both:

**(c) Record `mask_family` as a field of $\Pi$** — the subpopulation measure already carries acquisition-protocol metadata; mask family is acquisition-protocol metadata; therefore the mask family rides naturally inside $\Pi$ alongside the scanner vendor, the coil geometry, and (for downstream conditional-monotonicity claims) the receiver-coil sensitivity profile.

This option preserves the 5-tuple shape verbatim across CT, MRI, and PET. It is the option the v0.2 manuscript adopts (clarification C5; Section *framework*).

---

## 2. The decision (recorded)

**Adopted:** option (c). Modality-specific acquisition parameters that change the meaning of "signal reduction" — most notably the MRI mask family — are recorded as **fields of $\Pi$**, not as additional tuple slots.

Concretely, an MRI credential's $\Pi$ slug resolves (via the dataset's content-addressed manifest, Section *anchoring*) to an operational specification listing at least:

* `mask_family` ∈ {`uniform_random`, `variable_density_cartesian`, `equispaced_acs`, ...}
* `acceleration_rate` $R = 1/r$
* `central_region_fraction` (fraction of $k$-space lines around $k=0$ that are always retained)
* `coil_sensitivity_protocol` (which acquisition the sensitivity maps were estimated from)
* `recruitment_criteria` (the patient-population description that the demographic interpretation of $\Pi$ requires)

A credential issued at `mask_family = "variable_density_cartesian"` is silent about a re-evaluation at `mask_family = "uniform_random"`. Users wanting comparable credentials across mask families must compute and report them separately; the framework refuses to interpolate.

---

## 3. Why this is the right call

**3.1. Preserves the 5-tuple invariant.** The schema is identical across CT / MRI / PET — the single `signal_equivalence_credential(...)` API call has the same arguments and returns a credential of the same shape regardless of modality. This is the methodological promise of the framework; bloating the tuple for one modality breaks it.

**3.2. Matches how acquisition is already specified.** Real MRI acquisition protocols already require a coil-sensitivity-estimation procedure, a central-region size, a phase-encoding direction, and a number of other operational choices that have meaning only within the modality. Recording them inside $\Pi$ rather than as separate tuple slots collects them in one place — the "subpopulation operational description" — which is where a radiologist or trial coordinator would expect to find them.

**3.3. Composes with the content-addressed deposit.** $\Pi$ is a slug that resolves to a normative document by hash (Section *anchoring*). The mask-family choice is therefore baked into the same SHA-256 anchor that pins the framework version and the dataset manifest — there is no separate registry layer for "the mask family this credential was issued under."

**3.4. The synthetic experiment already exercises this convention.** [`experiments/cross_modality_consistency/`](../../experiments/cross_modality_consistency/) implements MRI under the variable-density Cartesian mask (1/4 of kept lines at centre; uniform sampling on the periphery) and treats the mask family as a fixed component of the modality config. The synthetic PASS verdict at the equivalent-method setting confirms the API survives this convention without modality-specific branching.

---

## 4. What the framework refuses to claim

* **Cross-mask-family transfer.** A credential at `mask_family = X` is not evidence for the same method under `mask_family = Y`. The point-evaluated-by-design principle (manuscript Discussion §"Point-evaluated by design") applies verbatim.
* **Implicit canonical mask.** The framework does *not* designate a canonical reference mask family. Three credentials under three mask families on the same cohort are equally valid; users seeking a vendor-style "best" mask must run a separate analysis outside the framework's scope.
* **Mask-family-agnostic reconstruction-quality scores.** Any single scalar that averages over mask families is *not* a signal-equivalence credential — credentials are mask-family-specific by Π.

---

## 5. Sanity check against the reference worked example

The manuscript's MRI worked example (Results §"Worked example 2") uses `mask_family = variable_density_cartesian` at acceleration $R = 4$ ($r = 0.25$) on the fastMRI knee dataset. The credential JSON:

```json
{
  "schema_version": "pwm-signal-equivalence/v0.2",
  "framework_hash": "sha256:...",
  "credential": {
    "modality": "MRI",
    "signal_ratio": 0.25,
    "subpopulation": "fastmri_knee_vd_cartesian_R4_v1",
    "task": {"name": "meniscus_segmentation_dice", "metric": "dice"},
    "epsilon": 0.02, "alpha": 0.05,
    ...
  }
}
```

The `subpopulation` slug `fastmri_knee_vd_cartesian_R4_v1` resolves (by hash) to the operational document specifying the variable-density Cartesian mask family at $R = 4$, the coil-sensitivity protocol, and the patient inclusion criteria. The credential is silent about $R = 8$ or about `uniform_random` masks at the same $R$.

---

## 6. Open follow-up (not blocking submission)

* A future v0.3 of this writeup may add a *taxonomy* of mask families with operational definitions of each. The current set ({uniform_random, variable_density_cartesian, equispaced_acs, ...}) is open-ended by design; the canonical taxonomy is a matter for an MRI-community standard rather than a single framework paper.
* For acceleration rates $R > 8$, the mask-family choice begins to dominate the reconstruction quality more than the rate itself; a credential at high $R$ should be read with the mask family as the primary characterising parameter and $r$ as secondary. Recorded here for v0.3.

---

*v0.1 — 2026-06-02. Revise if the depth-pass reading of fastMRI mask conventions (related_work.md §5 candidate 1) introduces a mask-family that the current taxonomy does not cover.*
