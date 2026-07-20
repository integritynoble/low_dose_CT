# PET signal-reduction decision (`open_questions.md` §8)

**Status:** v0.1 — decision recorded 2026-06-02 alongside the v0.2 manuscript.
**Cross-references:** [`open_questions.md`](../open_questions.md) §8; manuscript [`paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) §framework (Table 1 row 3); [`experiments/cross_modality_consistency/`](../../experiments/cross_modality_consistency/) (synthetic list-mode channel).

---

## 1. The question

PET list-mode acquisition admits two physically distinct ways to "reduce the signal":

| Mode | Physical change | Expected list-mode count | Side effects |
|---|---|---|---|
| **(I) Activity reduction** | Inject less radiotracer (fewer photon-emitting decays per second over the entire scan window) | $r \cdot \mu(x)$ | Photon-statistics-noise increases as $1/\sqrt{r}$; kinetic model parameters unchanged |
| **(II) Scan-time reduction** | Full activity, shorter acquisition window | $r \cdot \mu(x)$ | Same total counts, but **the temporal distribution of counts differs** — motion blur, kinetic modelling, and dynamic studies all change |

The two are *statistically* equivalent at the level of total list-mode counts (Poisson-thinning gives the same marginal distribution of counts) but are *not physically* equivalent. A reconstruction method evaluated under activity reduction is not directly comparable to the same method evaluated under scan-time reduction, even at the same $r$.

---

## 2. The decision (recorded)

**v1 of the framework canonicalises (I) Activity reduction as the reference PET $T_r$.**

Three reasons:

1. **Matches the "low-dose PET" framing in the literature.** Activity reduction is what the PET-imaging community means by "low-dose": the patient receives a reduced injected dose, the safety-claim story is the dosimetry argument, and the comparator full-dose acquisition is acquired identically except for the activity. Scan-time reduction is more typically called "list-mode resampling" or "abbreviated PET" and is reported as a separate operating point.

2. **It is the more conservative choice for safety claims.** A signal-equivalence credential under activity reduction validates the safety argument *as stated*. A credential under scan-time reduction at the same nominal $r$ does not validate the same argument; the dosimetry implications are different even when count statistics match.

3. **The Poisson-thinning model is exact under (I).** If $s_{\text{ref}}$ counts arise from Poisson decay at rate $\mu(x)$, then independent Poisson-thinning at rate $r$ yields counts at rate $r\mu(x)$ that are also Poisson and that are jointly indistinguishable in distribution from the activity-reduction acquisition. This is the model the synthetic experiment in [`experiments/cross_modality_consistency/`](../../experiments/cross_modality_consistency/) implements.

**Scan-time reduction is documented as out-of-scope for v1 and admitted as a v2 distinction.** A v2 credential schema may carry a `reduction_mode` field of $\Pi$ analogous to the MRI `mask_family` discussion (see [`mri_mask.md`](mri_mask.md)) — but until v2 ships, credentials under scan-time reduction must be reported with an explicit non-framework label and may not be compared to activity-reduction credentials.

---

## 3. What this means for the manuscript

The manuscript's framework Table 1 row 3 reads:

> PET — Poisson-thinning of list-mode counts at rate $r$

That row commits to (I) Activity reduction without saying so explicitly. This writeup formalises the commitment: the canonical PET $T_r$ is activity-reduction; users seeking credentials under scan-time-reduction must specify `reduction_mode = scan_time` in $\Pi$ and accept that the resulting credential is not directly comparable to standard (activity-reduction) PET credentials.

A future revision of the manuscript should add a footnote to Table 1 row 3 making this explicit. Tracked as a v0.3 manuscript polish item.

---

## 4. Worked-example dataset

The PET worked example uses the **NEMA NU-2 IQ phantom** at multiple activity levels (full / 50 % / 25 % / 10 %), which is the activity-reduction model directly. The phantom provides:

* Physical ground truth (known sphere sizes, known activity concentrations, known target-to-background ratios)
* Multiple paired activity levels acquired on the same scanner without inter-acquisition motion (the phantom does not move; scan parameters are reset between activity levels)
* No reader study required — the contrast-recovery coefficients are physical quantities

The credential's `subpopulation` field for the PET worked example resolves to a NEMA-IQ-phantom-acquisition specification, including the scanner model, the tracer (typically ${}^{18}$F-FDG-equivalent), the reconstruction software version, and the activity levels. The phantom replaces the patient inclusion criteria that $\Pi$ would carry for an in-vivo study.

---

## 5. What the framework refuses to claim for PET (v1)

* **Scan-time-reduced equivalence under the same $r$.** A credential at activity-reduction $r$ is silent about the same method's behaviour under scan-time-reduction at $r$, even though the total counts are matched.
* **Cross-tracer equivalence.** A credential issued under ${}^{18}$F-FDG is silent about ${}^{68}$Ga-DOTATATE, ${}^{18}$F-florbetapir, etc. Tracers differ in kinetic profile, branching ratio, and in-vivo distribution; the credential's `subpopulation` field includes the tracer for this reason.
* **Cross-scanner generalisation.** Standard point-evaluated-by-design discipline applies; a credential under one scanner model is silent about another.

---

## 6. Open follow-up (not blocking submission)

* **Dynamic PET / kinetic modelling.** Dynamic PET acquisitions reconstruct *parameters* (e.g. $k_3$, distribution volume) rather than images. A framework extension for dynamic-PET credentials should be considered for v2; the question is whether the metric $P$ should operate on per-frame reconstructions or on the kinetic-model output. Recorded here for v0.3.
* **List-mode-resampling reference distribution.** When scan-time reduction is admitted into v2, a normative reference list-mode-resampling protocol will need to be specified (early-fraction vs. uniform-temporal-thinning vs. last-fraction). The v2 credential's $\Pi$ will record this as a `temporal_thinning_protocol` field. Recorded here for v2.

---

*v0.1 — 2026-06-02. Revise when the NEMA NU-2 IQ phantom worked example produces real numbers (Phase 3, D9 + 270) and the activity-reduction reference is empirically confirmed against published phantom contrast-recovery data.*
