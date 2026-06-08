# Limitations anchors

**Companion to the V3-12 manuscript §Discussion subsubsection "Limitations of the present work".**

The reproduction guide ([`reproduction_guide.md`](reproduction_guide.md)) maps every *positive* numerical claim in the v0.3 manuscript to its repo anchor + the command that re-derives it. This document does the inverse: it maps every *limitation* the manuscript explicitly acknowledges to (a) the evidence we have that the limitation is real, (b) the proofs / simulation document that backs the magnitude or character of the limitation, and (c) the roadmap milestone that would close it. A reviewer can use this to confirm that each acknowledged gap is *honestly described*, not hand-waved past.

The five limitations below appear in [`manuscript.tex`](manuscript.tex) §Discussion, subsubsection "Limitations of the present work" (line ~302, immediately before §Methods). They are mirrored here verbatim with their anchors expanded.

---

## L-1. Empirical validation is synthetic-anchored, not yet real-cohort

**Manuscript text.** *"The current evidence backing the modality-general claim is the synthetic cross-modality consistency table (Results, Table 2; 6 credentials at seed = 42 covering CT, MRI, and PET) and the per-modality estimator-coverage simulations (Methods §3.3; AUC + Dice + contrast-recovery, total 93 simulated $(n, \sigma, \rho)$ cells). The per-modality Results tables (Table 2, Table 3, Table 4) carry `\todo{}` placeholders that fill at Phase 1 (CT, target D9 + 90 from the PWM-LDCT v0.5 cohort), Phase 3a (MRI, target D9 + 270 via fastMRI), and Phase 3b (PET, target D9 + 270 via the NEMA NU-2 IQ phantom)."*

| Anchor | What it backs |
|---|---|
| [`../experiments/cross_modality_consistency/cross_modality_consistency.py`](../experiments/cross_modality_consistency/cross_modality_consistency.py) + `results.json` | The 6-credential synthetic table referenced in §Results (3 PASS + 3 FAIL across CT / MRI / PET at seed = 42). Reproduces with `python3 cross_modality_consistency.py`. |
| [`../experiments/estimator_coverage/coverage_sim.py`](../experiments/estimator_coverage/coverage_sim.py) + `results.json` | 27 cells of AUC coverage under the truly-equivalent null. |
| [`../experiments/estimator_coverage/power_sim.py`](../experiments/estimator_coverage/power_sim.py) + `power_results.json` | 24 cells of AUC non-null power (the V3-9 simulation). |
| [`../experiments/estimator_coverage/dice_sim.py`](../experiments/estimator_coverage/dice_sim.py) + `dice_results.json` | 18 cells of Dice coverage + power (V3-10). |
| [`../experiments/estimator_coverage/cr_sim.py`](../experiments/estimator_coverage/cr_sim.py) + `cr_results.json` | 24 cells of contrast-recovery coverage + power (V3-11; surfaced the small-$n$ anti-conservativeness regime). |
| `manuscript.tex` Tables 2 / 3 / 4 (CT / MRI / PET Results) | All three carry `\todo{}` placeholders — these are the empty cells the synthetic-only acknowledgment names. |

**Closes when.** Phase 1 pilot CT data (D9 + 90 = 2026-09-03) populates Table 2; Phase 3a fastMRI integration (D9 + 270 = 2027-03-02) populates Table 3; Phase 3b NEMA NU-2 IQ phantom (D9 + 270) populates Table 4. The reproduction guide will gain §§13–15 anchoring each real-cohort table when its data lands.

**Why we believe the simulations transfer to real cohorts.** The estimator-coverage sims and the cross-modality consistency table together verify that the *code path* is correct; what real cohorts add is evidence about whether $T_r$ (Poisson thinning for CT, variable-density mask for MRI, activity reduction for PET) is a faithful model of the actual scanner physics. The proofs documents [`../theory/proofs/mri_mask.md`](../theory/proofs/mri_mask.md) and [`../theory/proofs/pet_reduction.md`](../theory/proofs/pet_reduction.md) argue this for MRI and PET respectively; CT's Poisson-thinning justification is in the manuscript §3.1.

---

## L-2. Three modalities are validated; the extension surface is not

**Manuscript text.** *"Methods Table 7 specifies the canonical $T_r$ operator for CT (Poisson thinning of projection counts), MRI (variable-density Cartesian mask, with `mask_family` carried inside $\Pi$), and PET (activity reduction); additional modalities — Optical / fluorescence, OCT, ultrasound — are listed as 'user-implementable, not validated.' The R3-3 tutorial notebook (`notebooks/04_optical_extending.py`) demonstrates that the API accepts an arbitrary modality string, but no independent research group has yet computed a credential under a user-implemented modality, and the modality-specific operator validity for those extensions remains the user's responsibility."*

| Anchor | What it backs |
|---|---|
| [`../pwm_dose_equivalence/notebooks/04_optical_extending.py`](../pwm_dose_equivalence/notebooks/04_optical_extending.py) | The "user-implementable" claim is *executable*: `Tr_optical` is defined alongside the `signal_equivalence_credential` call (no library code change), and the credential issues cleanly. PASS verdict at n = 80 specimens. R3-3 landing in `CHANGELOG.md`. |
| `manuscript.tex` Methods Table 7 ("modality dispatch") | Lists CT, MRI, PET as validated; Optical / OCT / ultrasound as user-implementable. The "not validated" annotation in the table is the acknowledgment this paragraph elaborates. |
| Adoption pathway §Discussion (months 0–12 milestone) | "three to five external research groups have computed credentials for their own methods" — the path by which the extension surface gets validated externally. |

**Closes when.** Adoption pathway months 0–12 milestone produces ≥ 1 independent external credential under a user-implemented modality. Until then, the manuscript's claim is *the API accepts arbitrary modalities*; we are not claiming *the API is correct for arbitrary modalities*.

**Why this is the right limitation framing.** A claim that the framework "supports OCT" would require us to independently verify that the OCT signal-reduction operator preserves the equivalence-credential semantics. We do not have that evidence; the R3-3 tutorial proves only that the API does not *prevent* an external user from constructing a credential. We surface this distinction explicitly rather than allow the unguarded "supports OCT" reading.

---

## L-3. The credential schema does not yet pin the method bundle

**Manuscript text.** *"The v0.2 schema carries `method` and `reference_method` as bare-string slugs; the manuscript's `code_hash` discipline (Section 3.1) currently lives at the publication venue (a Docker image digest in the supplementary materials, a pinned PyPI release hash, etc.) rather than inside the credential JSON itself. The companion credential reading guide (`paper_draft/credential_reading_guide.md`) and the library's CONTRIBUTING.md document this as the planned widening at v1.0 (Tier-A schema bump to `{name, code_hash}`); until then, method-bundle provenance is recorded out-of-band and is not enforced by the audit surface."*

| Anchor | What it backs |
|---|---|
| [`../pwm_dose_equivalence/src/pwm_dose_equivalence/credential.py`](../pwm_dose_equivalence/src/pwm_dose_equivalence/credential.py) line ~47 (`Credential.method: str`) | The bare-string status of the field as it ships at v0.2.2. |
| [`../pwm_dose_equivalence/credential_schema.json`](../pwm_dose_equivalence/credential_schema.json) `properties.credential.properties.method` | The standalone schema artifact reflects the same bare-string field. |
| [`credential_reading_guide.md`](credential_reading_guide.md) §2 "Schema-evolution note" | The reading guide explicitly tells reviewers this widens at v1.0. |
| [`../pwm_dose_equivalence/CONTRIBUTING.md`](../pwm_dose_equivalence/CONTRIBUTING.md) "Sign-off tiers" / "Versioning policy" | A widening of `method` from `str` to `dict` is a Tier-A MAJOR-version-bump change; CONTRIBUTING.md documents this. |
| [`CHANGELOG.md`](CHANGELOG.md) "L0.2.1 audit_credential" row | The original drift discovery — the reading guide's example showed `{name, code_hash}` but the library emits bare strings. The L0.2.1 entry reconciles the two by fixing the example and naming the v1.0 widening as the closure path. |

**Closes when.** Library v1.0.0 release (target: alongside *Nature Methods* paper acceptance). The schema widening is Tier-A: bumps `FRAMEWORK_SPEC`, regenerates `credential_schema.json`, re-issues all `examples/*.json` files, refreshes `expected_audit_output.txt`. The CI step "Verify FRAMEWORK_SPEC hash is unchanged" will fail at the exact commit that proposes the widening, forcing a deliberate update to the expected-hash constant.

**Practical implication for reviewers reading v0.2.2 credentials.** A v0.2.2 credential's `method` field is just a slug — the audit cannot tell the reviewer whether the bundle behind that slug is what the authors claim. The reviewer must ask the authors for the method bundle (Docker image digest, PyPI release hash) and verify it independently. This is the same discipline the reading guide §7's red-flag checklist names ("Method bundle hash not published alongside the credential").

---

## L-4. Reader-variability is a hard ceiling on attainable ε

**Manuscript text.** *"The framework's verdicts are conditional on ground-truth label quality; in the AUC / Dice regime the label-noise floor is whatever the reader-panel adjudication protocol leaves on the table. Concretely: a credential at $\varepsilon = 0.02$ on a task whose inter-reader Dice variance has standard deviation $\sim 0.05$ is operating below the label-noise floor and the verdict is largely a function of which adjudication subsample fell into the test split, not of the candidate method's actual signal-equivalence. The library refuses to issue a credential when the documented adjudication-protocol disagreement rate exceeds $\varepsilon / 2$ (Section 4.5, 'Estimator failure modes'); however, on tasks where reader-panel disagreement has not been independently quantified, the user is responsible for choosing $\varepsilon$ above the plausible label-noise floor. We do not currently provide a per-task label-noise registry; building one is on the v1.0 roadmap."*

| Anchor | What it backs |
|---|---|
| `manuscript.tex` §Discussion "Failure modes of the framework" → "Estimator failure modes" paragraph (existing pre-V3-12 text) | The `ε / 2` adjudication-disagreement gate. The library refuses to issue when the documented adjudication-protocol disagreement rate exceeds this. |
| [`../../WS-1_dataset/README.md`](../../WS-1_dataset/README.md) "Annotation QA protocol" entries | The WS-1 v0.5 cohort's adjudication protocol — board-certified reader panel + calibration gate + consolidation rule — is documented operationally. This is the protocol the AUC / Dice credentials issued on the v0.5 cohort would invoke. |
| [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md) §4 (estimator-default decision) | The estimator is unbiased under the assumption that ground-truth labels are noise-free; relaxing this assumption is the open theoretical question this limitation flags. |

**Closes when.** A per-task label-noise registry on the v1.0 roadmap. For the v0.5 cohort, the existing annotation-QA protocol gives an *implicit* label-noise floor (the consolidation-rule disagreement rate); making it *explicit* in the credential schema (a new optional `label_noise_floor` field) is a Tier-B MINOR-version bump because it is API-additive — existing credentials remain valid; new credentials gain the field.

**Why this is a fundamental, not engineering, limitation.** A credential cannot tighten its $\varepsilon$ below the per-task label noise floor without leaving the verifiable-claim regime. The framework's $\varepsilon$ parameter has a real, modality-specific lower bound; we surface this to prevent users from issuing tighter-than-meaningful credentials.

---

## L-5. The headline WS-1 v0.5 cohort sits in the INDETERMINATE-dominated regime

**Manuscript text.** *"At the recommended AUC-task default $\varepsilon = 0.05$ and a typical lung-nodule operating point AUC $\approx 0.92$, the v0.5 cohort of 208 unique paired patients satisfies the (S3) sample-size formula (n ≈ 130–250 required) but the empirical verdict distribution is dominated by `INDETERMINATE` rather than `PASS`: P(`PASS`) under the null is approximately $0.40$ at $n = 200$, lifting to approximately $0.94$ at $n = 500$ (§3.3, 'Cohort-sizing implication'). Downstream users issuing credentials on this cohort should expect `INDETERMINATE` verdicts for many genuinely equivalent methods; absence of `PASS` on the v0.5 cohort is not evidence of non-equivalence, only of insufficient $n$ at this $(\varepsilon, \alpha)$. For Dice / MAE / contrast-recovery tasks at the recommended non-AUC default $\varepsilon = 0.02$, the same cohort is comfortably in the PASS regime per the per-modality estimator-coverage simulations. The prospective v1.0 cohort target (n $\geq 500$) lifts the AUC operating point into the reliable-PASS regime."*

| Anchor | What it backs |
|---|---|
| [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md) §4a "Cohort-sizing implication" | The V3-9 power simulation that produced P(`PASS`) ≈ 0.40 at n = 200; ≈ 0.94 at n = 500 at the AUC ≈ 0.92, $\varepsilon = 0.05$ operating point. |
| [`../experiments/estimator_coverage/power_sim.py`](../experiments/estimator_coverage/power_sim.py) + `power_results.json` | The 24-cell simulation behind those numbers. Reproduces with `python3 power_sim.py` (~25 min wall time). |
| [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md) §4b (Dice) + §4c (CR) | The "Dice / CR is comfortably in the PASS regime at $\varepsilon = 0.02$" claim is backed by V3-10 + V3-11; non-AUC cohort behaviour does not share the AUC's INDETERMINATE bias at the v0.5 cohort size. |
| [`../theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) §3.2 (S3 formula derivation) | The "(S3) formula says n ≈ 130–250" claim — the *formula prescription* the empirical power-simulation tightens. |
| [`../../WS-1_dataset/README.md`](../../WS-1_dataset/README.md) "Credential-issuance regime" row in Target specs | The same regime called out in WS-1's README for downstream users. The mirror-pair: the manuscript names the regime; the WS-1 README operationalises it. |
| [`credential_reading_guide.md`](credential_reading_guide.md) §4 "Sample-size sanity check" | The reading guide tells non-coder reviewers what the regime means in practice ("absence of PASS on a 208-patient cohort is not evidence of non-equivalence"). |
| [`../pwm_dose_equivalence/examples/valid_ct_lung_nodule.json`](../pwm_dose_equivalence/examples/valid_ct_lung_nodule.json) | The clean PASS example is *intentionally* issued at n = 500, the regime's PASS threshold — not at n = 208 — so the per-example table in `examples/README.md` shows a clean verdict on a realistic cohort size. |

**Closes when.** Prospective v1.0 cohort (n $\geq 500$, target D9 + 270 → D9 + 450 with the IRB lag) lifts the AUC operating point into the P(`PASS`) ≈ 0.94 regime. Until then, **this is a property of the dataset × operating-point combination, not of the framework itself.** Tighter margins ($\varepsilon = 0.02$) or larger cohorts (v1.0) both resolve the regime; choosing a non-AUC task on the same cohort also avoids it.

**Reviewer-practice implication.** A reviewer reading a credential issued on the v0.5 cohort at $\varepsilon = 0.05$ should *expect* `INDETERMINATE` to be the modal outcome and should not treat it as a negative finding. The reading guide §3 spells this out; this anchor row ties the reading-guide text back to the simulation that justifies it.

---

## Cross-references

* [`manuscript.tex`](manuscript.tex) §Discussion "Limitations of the present work" — the V3-12 source this document anchors.
* [`reproduction_guide.md`](reproduction_guide.md) — the positive-claim companion (per-claim anchor table for what the manuscript *does* show).
* [`credential_reading_guide.md`](credential_reading_guide.md) §3, §4, §7 — the non-coder reviewer surface; this anchor doc backs the reading guide's "this is how to read X" framings with the proofs/simulation evidence.
* [`CHANGELOG.md`](CHANGELOG.md) "V3-12 Manuscript §Discussion 'Limitations of the present work'" — the landing record.
* [`../theory/proofs/`](../theory/proofs/) — the six theory documents the anchors above cite.
* [`../experiments/estimator_coverage/`](../experiments/estimator_coverage/) — the four estimator-coverage simulations.

---

*Limitations anchors v1.0 — 2026-06-08 (D9 + 19). Companion to manuscript v0.3 §Discussion "Limitations of the present work" (V3-12). Pairs with `reproduction_guide.md` (positive-claim anchors) and `credential_reading_guide.md` (non-coder reviewer surface).*
