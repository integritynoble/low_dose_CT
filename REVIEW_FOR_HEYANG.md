# Review for heyang — WS-1 … WS-4 status and what to do next

_Date: 2026-09-04 · Round 4, over merge commit `92fbe4a` (`heyang` → `main`)._
_Supersedes the 2026-07-20 review, which was written against `838d6a3` and is now materially out of date for WS-1._

## TL;DR

The July review said "zero real data artifacts, every headline table is an empty `\todo`." **That is no longer true for WS-1.** The `heyang` branch delivered a real GPU evaluation and an independent recalculation, and WS-1's manuscript now has zero `\todo`.

| Manuscript | `\todo` 2026-07-20 | `\todo` now | Movement |
|---|---|---|---|
| **WS-1** dataset | 28 | **0** | filled from a real run |
| WS-2 framework | 15 | 15 | unchanged |
| WS-2b PET | 76 | 72 | unchanged in substance |
| WS-3 reference | 125 | 126 | unchanged in substance |
| WS-4 leaderboard | 85 | 85 | unchanged (correctly — it is terminal) |

WS-1 is now the closest to submission, not WS-2. The remaining WS-1 blockers are **one statistics fix (now done, see below) and a pile of administrative paperwork** — not new science.

### What landed

- 5 models × 5 seeds × 3 dose levels over the full **n = 764** test slices, with per-slice detail committed.
- Vendored baselines (RED-CNN, LEARN, CTformer, CoreDiff) plus a permanent Gaussian-blur trap.
- `WS-1_dataset/R6_recalc/` — an **independent recalculation** on a separate venv and toolchain: report, runbook, asset manifest, A3/A4 scripts, results, SHA256 manifests. `blur` and `learn` reproduce **bit-identically**.
- The recalculation caught two real protocol errors *of its own accord* (a cached LIDC low-dose tree that silently changed the vendor KW result; a checkpoint/guide mismatch worth 9–13 dB) and documented both. That is exactly the discipline this project needs — keep it.

Tests at `92fbe4a`: WS-4 scoring **51 passed / 10 skipped**, WS-3 method **65 passed**, WS-1 analysis extractors **4 passed**. WS-1's loader tests fail to *collect* (`No module named pwm_ldct_loader.schema`) — packaging, not logic.

---

## Fixed in this pass

### 1. The five seeds were the same seed — and the bootstrap n was inflated 5× ✅ fixed

For every model and every dose level, the five seeds `{42, 2023, 7, 12345, 999}` produce **byte-identical** per-slice vectors (verified by SHA256 over the 764-element `psnr/ssim/cnr/cho_auc/npwe` arrays — one distinct hash across all five seeds, in both `baselines/results/` and `R6_recalc/results/`). Inference is deterministic given the checkpoint; the seed never reaches a stochastic component.

Two consequences, both now corrected:

- `manuscript.tex` declared the reproducibility gate as "report the mean and interval (min/max) of the per-seed results, so no reported number is a single-seed value." **Every one of those intervals was `[x, x]`.** The gate was satisfied in form and empty in substance.
- More seriously, the slice-level bootstrap pooled **"3,820 slices per dose level"** across the 5-seed grid — five exact copies of 764 slices. That inflated *n* by 5× and narrowed every percentile CI by ≈ √5.

**What changed.** `analysis/bootstrap_lidc_sim.py` is new and now committed (previously only the *outputs* of this computation were in the repo — the generator was not, so the numbers could not be re-derived). It resamples the **764 distinct slices**. Corrected CIs are **1.7–2.4× wider**:

| Quantity | Was | Now |
|---|---|---|
| CTformer knee 95% CI | 0.131 [0.128, 0.135] | 0.131 **[0.123, 0.139]** |
| RED-CNN CNR @ r010 | 5.192 [5.104, 5.280] | 5.192 **[5.000, 5.389]** |
| blur vs CTformer sep. @ r010 | 2.23× [2.208, 2.256] | 2.23× **[2.180, 2.286]** |

**No conclusion flips.** Every `≤0.10` knee still holds (r010 lower CI bounds 5.00–5.81, all far above Rose = 3.0), and CTformer's knee CI still lies strictly between r010 and r025. What changed is the width of the uncertainty, not the direction or the ordering. Point estimates are untouched.

The script was **validated before it was trusted**: run with `--pooling seed_pooled` it reproduces the published numbers exactly across all three report sections (§1 knees, §2 per-dose CNR CIs, §3 the twelve separation ratios). Only then was `--pooling distinct` used to replace them. Both artifacts are kept — the superseded reproduction sits in `output/lidc_simulated_bootstrap_stats_full764_seed_pooled.json` for comparison.

Updated: `paper_draft/manuscript.tex` (6 edits), `output/lidc_simulated_bootstrap_report.md` (banner + §2/§3 tables), `output/lidc_simulated_bootstrap_stats_full764.json`.

The manuscript now states the seed set **certifies determinism rather than quantifying variance**, and reports sampling uncertainty from the slice bootstrap instead. That is the honest version of the same gate.

> Remaining caveat, stated in both the script and the manuscript: slice-level resampling covers slice-sampling uncertainty only. Slices within a patient are correlated, so even the corrected CI is optimistic with respect to inter-patient heterogeneity. Patient-level resampling needs a slice→patient map that the committed result JSONs do not carry. **Worth adding** — it is the single cheapest remaining strengthening of the simulated arm.

### 2. Asset manifest and operator guide ✅ fixed / already fixed

- `R6_recalc/ASSET_MANIFEST.md` A2 was the last placeholder (`（交付时填写）`). Filled with a combined SHA-256 over the 17-file `pwm_ldct_loader` source tree, using this repo's own `analysis/common.py::inputs_fingerprint` convention, with the verification command inline. A tarball hash was deliberately *not* used — it depends on tar/zip parameters and is not reproducible. **No placeholders remain.**
- The recalculation report recommends fixing the guide's step-4 CTformer command. **This was already done** in the merged state (`R6独立复算操作指南.md` lines 120–133 use `ctformer_small_retrain.pt`). No action needed; the report's recommendation ① is stale.

---

## Open — needs your decision, deliberately not decided here

### 3. The comparison artifact ships a FAIL that only prose overrides ⚠️

`R6_recalc/results/comparison_full764.json` carries `"overall": "FAIL"` with red_cnn, ctformer and corediff marked `FAIL`, while `R6_recalc_report.md` §8 marks the same three `PASS*`. The repository contains a **machine-readable FAIL overridden only by prose**.

The tempting fix — loosen the tolerance — would relocate the prose `PASS*` into a script constant. That is the same post-hoc adjudication in a less visible place, so it was **not** done. Instead `R6_recalc/tolerance_audit.py` characterises the disagreement and writes a non-destructive `tolerance_audit` block into the JSON. **The `status` and `overall` fields are left exactly as shipped.** New §9 of the recalculation report explains it.

What the audit establishes:

**(a) The criterion is scale-inappropriate.** An *absolute* 1e-6 is applied to metrics spanning five orders of magnitude. `npwe_mean` ≈ 1.56e5, where absolute 1e-6 demands ~11 significant figures from a 764-term float64 reduction — unattainable regardless of cuDNN. So this is a units defect in the comparator, separable from the determinism question.

**(b) A relative criterion at the same strictness separates the two questions.**

| Model | worst absolute diff | worst relative diff | at relative 1e-6 |
|---|---|---|---|
| blur, learn | 0 | 0 | pass (bit-identical) |
| **ctformer** | 3.35e-02 | **4.41e-07** | **passes** |
| corediff | 4.58e+00 | 2.50e-05 | exceeds |
| red_cnn | 3.43e+01 | 6.36e-05 | exceeds |

CTformer's FAIL is an **artifact of the criterion**. RED-CNN and CoreDiff genuinely exceed 1e-6 relative — those two are the real cuDNN question.

**(c) Changing the number alone cannot work — the *kind* of criterion has to change.**

| Criterion | 1e-6 | 1e-5 | 1e-4 | 1e-3 |
|---|---|---|---|---|
| absolute (current) | FAIL | FAIL | FAIL | **FAIL** |
| relative | FAIL | FAIL | **PASS** | PASS |

Note the guide's §153 relaxation to 1e-3 is written for *differing hardware* and is absolute — under it, all three still FAIL. "Set the tolerance to 1e-3" would not make the artifact self-consistent.

**Two defensible routes, both yours to pick:**

- **(a)** Enable deterministic kernels (`torch.backends.cudnn.deterministic=True`, `torch.use_deterministic_algorithms(True)`) and re-run, so the strict branch passes on its own terms. *Preferred* — it removes the question instead of relitigating it.
- **(b)** Amend the operator guide in writing, dated, to declare that GPU inference paths compare at **relative** 1e-4 and say why; then re-run the comparison. One command once the guide says so.

### 4. The paired gate does not require the metric that catches the trap ⚠️

`task_spec` declares `DETECTABILITY_FIELDS = (cnr_mean, cho_auc_mean, npwe_mean)`. `bander_roi` is **absent** — so the gate never requires the only metric that separates the blur trap. This is not academic: the manuscript itself reports that on simulated data the trap's CNR *exceeds* RED-CNN by 1.11–1.19×, CoreDiff by 1.08–1.13× and CTformer by 1.90–2.23× at every dose level. **A metric the gate requires ranks the deliberate cheat above three of four real methods.** BandER is what catches it (8.9–15.6× separation, P(blur last) = 1.0000) and it is exactly what the gate omits. Add `bander_roi` to the required set.

_(Credit: raised by a parallel review session; verified here.)_

### 5. Vendored third-party code and data 🔴 blocks going public

The merge added 145.6 MB; `.git` is now 124 MB. That is tolerable. The licensing is not:

- **CoreDiff ships no license file at all.** LEARN has Apache-2.0 (`LICENSE` + `COPYING`), CTformer has a `LICENSE`, CoreDiff has neither.
- Third-party **pretrained weights** are redistributed (`ctformer/model_pretrained/T2T_vit_530000iter.ckpt`, `LEARN/examples/.../LEARN_MODEL.mat`, 85 MB `proMatrix_64.mat`).
- **`vendor/ctformer/test_img/*.npy` are Mayo-derived slices** (`L506_*`) — DUA-restricted data, redistributed in-repo.

Code Availability points readers at this repository, so resolve before it goes public. The last item is the urgent one: it is a data-use question, not a licensing preference.

### 6. Smaller items

- **The recalculation verified 5 groups, not 8.** Claim ① is stated as "8 groups (4 vendors × 2 dose tracks)" but `aapm_lidc_cross_vendor_spread.json` contains 5 (four LIDC vendors at simulated r = 0.25, plus AAPM-Siemens real). The second dose track was not recalculated. Either recalculate it or restate the claim as 5 groups.
- **Three different separation ranges** appear: 8.9–15.6× (`manuscript.tex:481,485,495`), 9.17–15.59× (`:636`), 8.9–23.1× (R6 runbook claim ①), against a measured 8.93–18.83×. These are plausibly different scopes (AAPM-only vs cross-vendor), but a reviewer will read them as one number. Label each with its scope.
- **WS-1 loader tests do not collect** — `pwm_ldct_loader.schema` missing. Fix the packaging so the 25/25 suite runs again.

---

## WS-1's remaining blockers are administrative

All four 🔴 sections of `SUBMISSION_CHECKLIST.md` are paperwork, not research:

1. **People & declarations** — authors, affiliations, ORCIDs, corresponding author; CRediT matrix; **per-author competing interests**. The PWM Protocol Foundation equity/token disclosure is *not optional* at a medical venue and is currently a `\todo`.
2. **Deposit & identifiers** — PhysioNet DOI, Zenodo mirror. *Scientific Data* requires deposited data **at submission**. This has the longest lead time — **start it now**, in parallel with everything else.
3. **IRB determination number** — obtain the letter, cite the number. Do not assert a determination whose number is unknown.
4. **Final assembly** — funding/grant numbers, cover letter, reporting summary.

---

## Suggested order

1. ~~Fix the bootstrap *n* and the seed protocol~~ ✅ done in this pass.
2. **Decide the tolerance question** (§3) — route (a) preferred. Then **add `bander_roi` to the gate** (§4).
3. **Start the PhysioNet deposit now** — longest lead time, gates submission.
4. **Resolve vendor licensing and the Mayo-derived `.npy` files** (§5) before the repo goes public.
5. **Clear the four administrative sections** of the WS-1 checklist.
6. **Add the patient-level bootstrap** for the simulated arm (needs a slice→patient map in the result JSONs).
7. Then WS-2 (prose reconciliation only — still no new experiments needed), then WS-3's Phase-3 run, then WS-2b's physical PET scan. WS-4 stays terminal; do **not** "finish" it by inventing cohort numbers.

## What's genuinely good — don't lose it

- The R6 recalculation methodology: independent venv, independent toolchain, byte-level source snapshot verification, and a willingness to report its own errors. This is the strongest research-integrity artifact in the repository.
- The `analysis/` provenance pattern (extractor scripts + combined-SHA `provenance.json`) — now extended to the bootstrap generator.
- The blur trap as a permanent control. It is doing its job: it is *precisely* the thing that exposes the gate defect in §4.
- Honest self-accounting across `SUBMISSION_CHECKLIST.md` and the limitations docs. That discipline is what keeps this on the right side of research integrity, and it is why the two defects fixed above were findable at all.
