# Open Questions — Signal-Equivalence Framework

**Status:** Seeded 2026-05-20 alongside [`dose-equivalence-framework.md`](dose-equivalence-framework.md) v0.1.
**Window:** Phase B months 5-12 of Track 9 (theory time during the WS-1 IRB lag, per [`../README.md`](../README.md)).
**Purpose:** Enumerate every theoretical gap between the v0.1 working draft and a manuscript that *Nature Methods* reviewers will accept. Each item is scoped with deliverable, gating priority, and estimated effort so the IRB-lag window can be sequenced rationally.

The numbering matches the section anchors used by the framework draft (`open_questions.md §1` = literature pass; `§2` = sample-size formula, etc.). Renumbering breaks those cross-references — extend, don't reorder.

---

## Priority legend

| Tag | Meaning |
|---|---|
| **BLOCK** | Must close before *Nature Methods* submission; reviewer will reject without it |
| **SHARPEN** | Required for v0.2 of the framework draft (post-literature-pass); not submission-blocking but needed before Phase A pilot freezes the credential schema |
| **DEFER** | Real open question; can ship Nature Methods v1 without it and address in follow-up paper or v2 framework |

Effort is in **person-weeks** of dedicated theory time (≈ 15-20 h/week in the IRB-lag window, per [`../README.md`](../README.md)).

---

## §1. Literature pass — what does the field already call this?

**What's known.** Test-of-equivalence statistics is classical (Schuirmann 1987 TOST in pharmacokinetics; non-inferiority trial design in clinical statistics). Image-quality equivalence for low-dose CT has been studied empirically (AAPM TG-233; numerous radiologist-reader studies). What's *not* in the literature is a unified, modality-agnostic, task-conditional definition with an estimator and a credential format.

**What's open.**

1. Are there prior frameworks that anticipate the 5-tuple form? Candidates to read end-to-end (≤ 4):
   - Samei et al. "Performance evaluation of CT" series (task-based image quality, AAPM TG-233 lineage)
   - Barrett & Myers, *Foundations of Image Science* — task-based assessment chapters (Hotelling/CHO observer framework)
   - FDA guidance on AI/ML-based SaMD performance evaluation (subpopulation-stratified reporting)
   - Recent fastMRI / fastMRI+ papers on accelerated MRI reader studies
2. Does any prior work use a *paired-bootstrap-on-patients* estimator with explicit `(ε, α)` reporting? If yes, cite and contrast scope. If no, name that gap explicitly in the manuscript intro.
3. Are there prior attempts at *modality-general* signal-reduction equivalence? (Most prior work is modality-specific.) Confirm the multi-modality framing is genuinely novel before claiming so in §1 of the manuscript.

**Deliverable.** `related_work.md` (≤ 4 papers, ≤ 1 paragraph each), plus a 1-paragraph "what is genuinely new" memo the team writes for confidence before committing to v0.2.

**Priority.** SHARPEN. **Effort:** 1.5 weeks (1 wk reading + 0.5 wk writing). **Gates:** v0.2 framework revision; the answer to question 3 above is the manuscript's positioning.

---

## §2. Sample-size formula

**What's known.** The framework draft §7 currently states `n ≥ 200` for `ε = 0.02, α = 0.05` on AUC-type metrics, "justified empirically in v0.1, formally in v0.2+." This is a pre-registered guess, not a derivation.

**What's open.** A closed-form (or numerically tabulated) sample-size formula `n(ε, α, σ, ρ, metric)` where:
- `σ` is the population standard deviation of the per-patient performance difference `Δ_k = a_k − b_k` (framework §7)
- `ρ` is the pairing correlation between `a_k` and `b_k` (paired bootstrap exploits ρ; ignoring it gives a conservative bound)
- `metric` is at minimum {AUC, Dice, MAE} — three canonical cases cover the manuscript's worked examples

**Deliverable.** `proofs/sample_size.md` with:
1. Asymptotic normal-approximation bound (Hoeffding or CLT-based), giving `n ≥ (z_{α/2}/ε)^2 · σ^2(1−ρ)` as the leading-order rule.
2. Finite-sample correction (Bernstein-type) for tasks where `Δ_k` is bounded but non-Gaussian (AUC differences with small `n`).
3. A numerical table for `(ε, α) ∈ {(0.02, 0.05), (0.03, 0.05), (0.05, 0.05)} × σ ∈ {0.05, 0.10, 0.15} × ρ ∈ {0.0, 0.5, 0.9}`.
4. Empirical validation on the Phase 1 pilot data once the team produces `phase1_pilot_5_tuples.json` — does the formula predict the observed CI widths?

**Priority.** BLOCK. *Nature Methods* will not accept an empirical-only sample-size justification for a methodological framework paper. **Effort:** 2 weeks. **Depends on:** §3 (the formula's validity rests on the estimator's concentration properties).

---

## §3. Concentration / validity of the paired-bootstrap estimator

**What's known.** The paired bootstrap (Efron 1979; Efron & Tibshirani 1993, ch. 8) is consistent for the population-mean difference under finite-second-moment assumptions on `Δ_k`. Standard.

**What's open.**

1. Does the percentile-CI used in framework §7 attain its nominal coverage `1 − α` *uniformly* over the parameter regimes the framework will be applied in (AUC near 1.0; Dice near 0.85; small `n`)? AUC near the boundary is known to be a regime where bootstrap CIs are anti-conservative; this is a real risk.
2. Should we use BCa (bias-corrected accelerated) percentiles instead of plain percentile? BCa fixes the AUC-boundary problem in known cases but adds notational baggage.
3. Is there a closed-form alternative (e.g., DeLong's test for paired AUC) for the most common task metric (AUC), and if so should the framework default to it and use bootstrap only as fallback?

**Deliverable.** `proofs/estimator.md` with:
1. Coverage guarantee (theorem-statement form) under IID-from-`Π` assumption and finite-second-moment `Δ_k`.
2. Coverage simulation: run the bootstrap on synthetic AUC pairs at AUC ∈ {0.85, 0.92, 0.97} with `n ∈ {100, 200, 500}` and report empirical coverage. If percentile CI under-covers, switch the framework default to BCa or DeLong and document.
3. Decision: percentile (current) vs BCa vs DeLong-for-AUC.

**Priority.** BLOCK. The estimator is the operational definition of the framework; if its coverage is wrong, every credential is mis-stated. **Effort:** 1.5 weeks (0.5 wk theory + 1 wk sims).

---

## §4. Composition law

**What's known.** Framework §8 lists composition as **open**: "if `M ≡_(r, ...) M_baseline` and `M_baseline ≡_(r', ...) M_baseline'`, then `M ≡_(?, ...) M_baseline'` for some `?`." A conservative guess `? = r · r'` is offered without proof.

**What's open.** Whether *any* clean composition law exists. Two candidate forms:

| Candidate | Statement | Plausibility |
|---|---|---|
| Multiplicative-`r` | `M ≡_(r · r', T, ε + ε', α + α', Π) M_baseline'` | Likely too loose; `r · r'` is correct for the signal ratio (composing reduction operators) but `ε + ε'` ignores correlations |
| Additive-`ε` only | Same task `T`, same `Π`; transitive `ε` budgets compose linearly under disjoint randomness assumption | Cleaner; `r` does not compose because `M` was never evaluated at `r · r'` directly |
| No composition | The framework refuses to make composition claims; users must re-evaluate at the composed level | Defensible; matches the "task-restriction" caveat |

**Deliverable.** `proofs/composition.md`. The honest outcome may be a negative result: "composition does not hold non-trivially; the framework is intentionally not transitive across reference choices." That is a publishable position if argued well.

**Priority.** DEFER. The manuscript can ship with a clear "we make no composition claims" footnote and a one-paragraph discussion. Forcing a composition theorem risks producing a wrong one. **Effort:** 0.5 weeks (write the negative-result note) or 2-3 weeks (attempt a real proof).

---

## §5. Conditional monotonicity-in-`r`

**What's known.** Framework §8 flags this as the **key open property**: monotonicity-in-`r` is *not* unconditionally true (a method tuned for one `r` may degrade at other `r`), but a useful sub-claim is "monotonicity holds for methods trained or tuned across the range `r ∈ [r_min, 1]`."

**What's open.** Formalize the conditioning. Concretely:

1. Define a class of methods `𝓜_{[r_min, 1]}` that are trained on a distribution over `r` covering `[r_min, 1]` (e.g., uniformly).
2. Conjecture: for `M ∈ 𝓜_{[r_min, 1]}`, if `M ≡_(r_0, T, ε, α, Π) M_baseline` with `r_0 ∈ [r_min, 1]`, then `M ≡_(r, T, ε, α, Π) M_baseline` for all `r ∈ [r_0, 1]`.
3. Counterexample search: construct (or look for in the literature) a member of `𝓜_{[r_min, 1]}` that violates the conjecture. If found, weaken the conjecture.

**Deliverable.** `proofs/monotonicity.md`. Realistic outcome is a *conjecture + empirical evidence* result, not a clean theorem. The manuscript states it as a "design recommendation supported by Phase A pilot data on 3 baselines" — that is honest and usable.

**Priority.** SHARPEN. Not strictly submission-blocking (the framework is well-defined without monotonicity), but a reviewer will ask. Better to have a half-page answer than a hand-wave. **Effort:** 1 week (formalization + empirical check against Phase 1 pilot results once they land).

---

## §6. Per-patient vs aggregate — when does the choice matter?

**What's known.** Framework §6 commits to aggregate (formulation 6a) as canonical, with per-patient (6b) as an opt-in stronger tag. Aggregate matches clinical-trial endpoint reporting; per-patient is too strict for adoption.

**What's open.** Pre-register *guidance* — not just "you may choose either" — on when per-patient should be preferred:

1. Pediatric / rare-population credentials, where aggregate masks a small cohort with disproportionate risk.
2. Diagnostic settings where the loss of a single missed lesion is the regret function (vs. population-level AUC).
3. Regulatory submissions where the FDA reviewer expects subgroup analysis.

**Deliverable.** A 1-paragraph section in the manuscript's discussion (and a longer note here) on the decision rule. No proof required; this is editorial.

**Priority.** SHARPEN. **Effort:** 0.5 weeks (after §1 literature pass surfaces what FDA precedent looks like).

---

## §7. MRI mask distribution model

**What's known.** Framework §2 row 2: MRI signal reduction is `s_red = Ω_r · s_ref` where `Ω_r` is a k-space subsampling mask with `|Ω_r| / |Ω_full| = r`. The mask realization is itself a random variable — `T_r` includes the mask distribution.

**What's open.** Which mask distribution(s) are the framework's *reference* for MRI:

1. **Uniform random** undersampling at rate `r` — the cleanest theoretical object.
2. **Variable-density Cartesian** (denser sampling near k-space center) — the fastMRI dataset default.
3. **Equispaced + central-k-fully-sampled** — common in vendor implementations.

These are not equivalent: a method optimized for one mask family may fail under another. The framework can either:

- (a) Specify *one* canonical mask distribution per acceleration rate (with the framework definition implicitly fixing `T_r` to that mask family). Risk: ties the framework to a specific operational choice.
- (b) Let the credential record the mask distribution alongside `r` (extending the 5-tuple to include `mask_family` for MRI). Risk: bloats the credential schema; loses cross-modality uniformity.

**Deliverable.** Decision recorded in `proofs/mri_mask.md`. Lean (b) — record `mask_family` as a subpopulation sub-key — to preserve the 5-tuple's uniform shape. Worked example uses fastMRI variable-density mask as the reference for the manuscript.

**Priority.** BLOCK *for MRI worked example only*. Without resolving this, the MRI validator section of the manuscript cannot be written. **Effort:** 1 week (literature scan on fastMRI mask conventions + decision).

---

## §8. PET model under list-mode reduction

**What's known.** Framework §2 row 3: PET signal reduction is Poisson-thinning of list-mode counts at rate `r`. Standard.

**What's open.** PET list-mode supports two physically distinct reductions:

1. **Activity reduction** — inject less radiotracer; expected count `r · μ(x)`. Poisson-thinning model is exact.
2. **Scan-time reduction** — full activity, shorter acquisition window. Expected count is still `r · μ(x)`, but the temporal distribution of counts is non-equivalent (motion blur differs; kinetic modeling differs).

For the *Nature Methods* worked example, only one is needed. Suggest **activity reduction** (matches the "low-dose PET" framing in the literature and is the more conservative choice for safety claims). Scan-time reduction is recorded as out-of-scope for v1 and added as a v2 distinction.

**Deliverable.** 2-paragraph decision in `proofs/pet_reduction.md`. Reference public phantom data (e.g., NEMA IQ phantom at varying activity) as the worked-example dataset.

**Priority.** SHARPEN — required if PET is the second-modality worked example; can defer if MRI alone satisfies the multi-modality bar (team judgment call at month 8). **Effort:** 0.5 weeks.

---

## §9. Multi-task aggregation

**What's known.** Framework §8 task-restriction property: equivalence on task `T` does *not* imply equivalence on `T' ≠ T`. The 5-tuple is task-specific by construction.

**What's open.** Many real clinical workflows depend on *multiple* tasks (detect + localize + quantify). A method that passes equivalence on detection but fails on quantification is not clinically deployable. Should the framework offer a *task-bundle* extension where a credential covers a vector of tasks `(T_1, ..., T_K)` with per-task `ε_k`?

**Deliverable.** Recorded as a v2 extension. Manuscript v1 explicitly acknowledges this limitation and points to the bundle extension as future work.

**Priority.** DEFER. Not submission-blocking; including a half-baked bundle definition is worse than omitting it. **Effort:** 0 weeks in v1 (acknowledgment only).

---

## §10. Cross-subpopulation generalization

**What's known.** Framework §5 subpopulation-restriction property: equivalence on `Π` does not imply equivalence on `Π' ≠ Π`. Adult-trained methods often fail on pediatric `Π`.

**What's open.** Is there a useful bound of the form: "if `M ≡_(r, T, ε, α, Π) M_baseline` and `KL(Π' ‖ Π) < δ`, then `M ≡_(r, T, ε + f(δ), α, Π') M_baseline`"? This would be a transfer-learning-style guarantee.

**Deliverable.** Recorded as v2 extension. Manuscript v1 cites this as the most-requested follow-up and explicitly does not attempt it.

**Priority.** DEFER. Same reasoning as §9. **Effort:** 0 weeks in v1.

---

## Summary table — IRB-lag work schedule

The questions ordered by intended attack sequence within the months 5-9 theory window:

| Order | § | Item | Priority | Effort (wk) | Cumulative (wk) | Deliverable |
|---|---|---|---|---|---|---|
| 1 | §1 | Literature pass | SHARPEN | 1.5 | 1.5 | `related_work.md` + positioning memo |
| 2 | §3 | Estimator validity / coverage sims | BLOCK | 1.5 | 3.0 | `proofs/estimator.md` |
| 3 | §2 | Sample-size formula | BLOCK | 2.0 | 5.0 | `proofs/sample_size.md` |
| 4 | §7 | MRI mask distribution decision | BLOCK (MRI only) | 1.0 | 6.0 | `proofs/mri_mask.md` |
| 5 | §5 | Conditional monotonicity (after Phase A pilot lands) | SHARPEN | 1.0 | 7.0 | `proofs/monotonicity.md` |
| 6 | §8 | PET model decision (if PET is second validator) | SHARPEN | 0.5 | 7.5 | `proofs/pet_reduction.md` |
| 7 | §6 | Per-patient guidance editorial | SHARPEN | 0.5 | 8.0 | manuscript discussion paragraph |
| 8 | §4 | Composition law — negative-result note OR proof attempt | DEFER | 0.5–3.0 | 8.5–11.0 | `proofs/composition.md` |
| 9 | §9, §10 | Multi-task + cross-subpopulation extensions | DEFER | 0.0 | 8.5–11.0 | acknowledgments only |

**Read of the schedule.** ~8 weeks of theory work covers everything BLOCK + SHARPEN, leaving 0-3 weeks for the optional composition attempt. The IRB-lag window in [`../README.md`](../README.md) is months 5-9 ≈ 16-20 weeks of calendar; even at half capacity (mainnet ops + paper revisions also run in parallel), 8 weeks of theory is achievable. Composition can absorb the rest or be deferred.

**Critical sequencing note.** §2 (sample-size) depends on §3 (estimator validity). Do not start §2 before §3 closes — a sample-size formula built on a wrong estimator validity assumption is worse than no formula.

**Phase 1 pilot dependency.** §5 (monotonicity) and §3 (coverage sims) both benefit from `phase1_pilot_5_tuples.json` for empirical validation. Best-case start of §5 is month 7 (after pilot lands at week 12).

---

## What this list deliberately does NOT include

- **Engineering questions** — `pwm_dose_equivalence` library API, CI integration, documentation. Those live in `framework/pwm_dose_equivalence/` (later); they are not theory.
- **Manuscript prose** — section headings, figure list, page budgets. Those live in `paper_outline.md` (later).
- **Empirical results** — bootstrap CI widths, baseline performances, multi-modality validation. Those are Phase 1 pilot + Phase 2/3 implementation.
- **L2 spec format** — the on-chain credential schema. That lives in [`../../pwm_integration/l2_spec.md`](../../pwm_integration/l2_spec.md) and freezes a hash of the framework doc, not the open-questions doc.

---

## Cross-references

- [`README.md`](README.md) — purpose of this subfolder.
- [`dose-equivalence-framework.md`](dose-equivalence-framework.md) — v0.1 formal definition this list is the work-plan against.
- [`../README.md`](../README.md) — WS-2 framework scope (modality coverage, library design).
- [`../README.md`](../README.md) — WS-2 workstream README; Phase 1 pilot is the empirical companion to §3 and §5; the timeline schedules theory work across IRB-lag months 5-9.

---

*Seeded v0.1 — 2026-05-20. Revise as the literature pass (§1) closes; the answer to "what is genuinely new" determines whether the manuscript argues novelty on (a) the framework itself, (b) the modality-general framing, or (c) the credential / on-chain anchoring contribution. v0.1 leaves all three on the table.*
