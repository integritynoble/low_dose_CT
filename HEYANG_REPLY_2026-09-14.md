# §3 reply — the discriminating index is gameable at both ends, and what the 3.9–6.7× is made of

Responding to [`HEYANG_NEXT_2026-09-13.md`](HEYANG_NEXT_2026-09-13.md) §3, which was written against `main` @ `72ba063`.
Written against **`heyang` @ `b520f9ab`** ("Merge origin/main (5ffe30d) into heyang: take main as authoritative", 13 September 2026), the current HEAD of this checkout.

Scope: §3 (a) and (b), plus one factual correction to §3's premise. Nothing else was touched — no commit, no push, no edit to any tracked file, no training and no weight change. (a) required **inference-only** re-runs of the existing checkpoints, because no existing observation record answers it (see §2.1).

---

## 1. (b) — was "higher ROI BandER is better" the intent, or was *closer to the reference*?

**No.** In `detectability-freq-v1` the index is a **retention floor against the full-dose reference**, not a scale on which more is better.

- BandER is defined as a ratio **against the reference**, whose denominator *is* the reference:
  `band_energy_ratio = sum(o_hf^2) / sum(fd_hf^2)` — `WS-1_dataset/baselines/task_spec.json:66`;
  `BandER = Σ o_hf² / Σ fd_hf²` — `WS-1_dataset/schema/detectability_task_spec.md:93`.
  So **1.0 is the parity point** (the output carrying the same 1-px high-pass band energy as the reference), not a target.
- The only thing the design text fixes is the **failure end**: "blur (sigma=1.0) is expected to retain the least HF energy" (`task_spec.json:66`); "a smoother retains the least HF energy" (`detectability_task_spec.md:93`). Protocol and gate are both written as *the trap must sit at the lowest end*: "the trap **lowest** on ROI BandER at every dose point" (`WS-4_leaderboard/OPTIMIZATIONS_LOG.md:351`); "catches a trap that is not last on ROI BandER" (`DIRECTOR_DECISIONS.md:115`).
- The calibrated thresholds are **one-sided**: blur ≤ 0.35 fails / learned ≥ 0.60 passes (`task_spec.json:69`, `detectability_task_spec.md:95`). **An upper bound was never specified**, in either direction.
- "Higher is better" is a reading the **leaderboard** introduced on its own. `WS-4_leaderboard/scoring/leaderboard.py` sorts the discriminating field descending — `sort_entries` ends in `sorted(entries, key=key, reverse=True)` (`leaderboard.py:313-329`; docstring: "detectability-first ranking: discriminating index **desc**"). `git blame` attributes that line (`:329`) to **`54c58ca6`** (2026-08-23, "sync: full local project state onto heyang"). Nothing in the protocol's design text is the source of that reading: `scoring/task_spec.py:60` declares only that the field is *discriminating* (`DISCRIMINATING_FIELDS = ("bander_roi",)`), never its direction.
- Because the numerator is unbounded under that reading, a **noise injector is rewarded** (~183 at +20 HU, ~1598 at +60 HU, against 0.43–6.7 for everything real). That was **not foreseen at design time** — an entry *above* the reference was never part of the design space.

**The correct follow-up is to add an upper-bound constraint, not to invert the index into distance-from-reference.** The symmetric fix (`|log BandER|`) is self-falsifying: on the AAPM held-out set the blur trap's 0.432 is *closer* to the reference than CTformer's 6.735, so under the symmetric score **the trap becomes the best entry**. Running `scripts/prepare-bander-direction-fix.py` (the read-only analysis that `72ba063` adds, and which changes no scoring rule) confirms: order fixed = `blur > learn > red_cnn > ctformer`, and in **2 of the 5 vendor groups** (Philips, AAPM-Siemens-real) the trap is no longer the worst entry. Inverting the index would hand the trap the top rank and drop the separation the gate depends on.

---

## 2. (a) — what is the 3.9–6.7× above the full-dose reference made of?

There is no prior diagnostics or visual record in the repository to recall, and no clear recollection of the output images on this side, so the question is answered by **measurement on the held-out test examples** rather than by impression.

**One-line attribution.** *The excess is dominated by residual broadband noise the denoisers did not remove, not by edge sharpening: red_cnn and LEARN carry ~10% **less** ROI high-pass energy than the undenoised low-dose input (3.88 / 3.85 vs 4.29), whose own ratio is already 4.3×, and 85.7% of that energy is orthogonal to the reference (energy account in §2.3) — the same share as the input's (86.0%); the flat/edge split tracks the input's (edge/flat ≈ 0.90 in both). CTformer is the exception on top of that residual: it adds energy the input does not have (flat-region ratio 7.39 vs the input's 4.62), flattens the flat-region spectrum (−1.61 vs −2.76) and carries 1.7× the input's orthogonal energy (6.140 vs 3.692 in units of the reference's ROI HF energy, where red_cnn and learn sit at 0.9× the input's) — consistent with added high-frequency texture/sharpening.*
*Strength: medium-to-strong for "residual noise dominates"; weak-to-medium for "flat regions lead edges" (a ≈10% difference, on an ROI protocol that selects flat soft tissue in the first place); the ROI high-pass correlation ρ separates nothing across objects and is used only as a normalisation, never as evidence; the spectrum-slope whitening test is not usable here and is not part of the conclusion.*

### 2.1 What was run

- **Metric reused verbatim.** `WS-1_dataset/R6_recalc/freq_detectability_recalc.py`'s own functions and constants: `highfreq_hu` (`HF_SIGMA = 1.0`), `find_tissue_roi` (`PATCH = 32`, `seed 42`), `run_model`, `DET_SLICES = 48`, and the `eps_floor = 1e-4 ×` full-image FD HF energy regularisation. No re-derivation of the metric.
- **Objects**: the four evaluated entries — `red_cnn`, `ctformer`, `learn`, and the 5×5 σ=1 blur trap — on the four AAPM 2016 held-out patients `aapm-0003/0005/0006/0009` (aapm-0006 included), 48 ROIs per patient → 192 ROI measurements per object (768 across the four objects).
- **Inference only.** Output images were written to the session scratch directory; nothing was persisted into the repository.
- **Checkpoint note (reproducibility, worth recording).** The CTformer weights behind the frequency artifact — and behind the 6.735/8.667 quoted for `aapm-0006` — are **`baselines/checkpoints/ctformer.pt`** (87,569,384 params), *not* `baselines/checkpoints/ctformer_small_retrain.pt`. Per-slice comparison against the on-disk artifact gives a 1.4e-06 relative match for `ctformer.pt` versus a 41% deviation for the small retrain (aapm-0003 mean 5.116 vs 3.870). The R6 recalc guide's step 4 lists the small retrain first; anyone re-running should use `ctformer.pt`.

### 2.2 Reproducibility self-check — re-run vs the on-disk R6 artifact

Per-slice ROI BandER was compared with `WS-1_dataset/R6_recalc/results/freq_aapm_real_r025_*.json` (`ber_per_slice`, 48 values × 4 patients per object):

| object | slices compared | bit-identical | max rel. dev | mean rel. dev | 4-patient mean (disk / re-run) |
|---|---|---|---|---|---|
| red_cnn | 192 | 0 | 7.50e-05 | 2.22e-05 | 3.8762 / 3.8762 |
| ctformer | 192 | 21 | 1.68e-06 | 3.99e-07 | 6.7352 / 6.7352 |
| learn | 192 | 192 | 0 | 0 | 3.8539 / 3.8539 |
| blur | 192 | 192 | 0 | 0 | 0.4315 / 0.4315 |

The re-run reproduces the frozen artifact to float noise on all four objects (global max 7.5e-05, global mean 2.2e-05, both on red_cnn; every per-patient mean agrees to four decimals), so the attribution below rests on numbers that match the artifact that produced §3's figures. A cross-check of the input row (same low-dose input, recomputed once per object) agrees to 0.0 across all four objects.

### 2.3 Attribution — four rows per object, means over the 4 held-out patients

Regions: ROI pixels split at the **median of the full-dose reference's local gradient** (`|grad|` of the FD image inside the ROI) into flat / edge halves. `R_flat`, `R_edge`: Σ o_hf² / Σ fd_hf² restricted to each half. `slope`: power-law exponent of the ROI high-pass power spectrum (16×16 blocks). `ρ`: Pearson correlation between the output's and the reference's ROI high-pass (the driver's `corr2(o_hf, fd_hf)`) — the quantity the energy accounting below is normalised by, and **not usable as a discriminator** (see below).

| object | R_flat | R_edge | edge/flat | slope (output) | slope (reference) | ρ (ROI HF corr.) |
|---|---|---|---|---|---|---|
| red_cnn | 4.17 | 3.75 | 0.90 | −2.73 | −2.76 | 0.394 |
| ctformer | 7.39 | 6.41 | 0.87 | −1.61 | −2.76 | 0.314 |
| learn | 4.14 | 3.73 | 0.90 | −2.72 | −2.76 | 0.395 |
| blur (trap) | 0.44 | 0.43 | 0.97 | −7.36 | −2.76 | 0.393 |
| low-dose input¹ | 4.62 | 4.15 | 0.90 | −2.57 | −2.76 | 0.390 |
| **4-example mean (learned only)** | **5.23** | **4.63** | **0.89** | **−2.35** | **−2.76** | **0.367** |

¹ Computed with the same formula from the low-dose input; not part of the frozen artifact, included as the zero-denoising reference point.

**`ρ` separates nothing, and is not evidence.** The correlation column reads 0.390–0.395 for red_cnn, learn, the undenoised input and the σ=1 blur trap alike — a spread of 1.1% of its own value across objects whose `R` spans 0.43–4.29, and per ROI blur vs red_cnn gives Cohen's d ≈ 0.01. It is therefore unusable as a discriminator and is kept only because it is the normalisation that ties the energy account below together (`α ≈ ρ·√R` per ROI). CTformer's 0.314 is a real shift in the mean (192 ROIs, sd ≈ 0.11 → SE ≈ 0.008), but it is the sole gap in an otherwise flat column and it overlaps the others per ROI, so the CTformer exception is **not** argued from it: it is carried by the flat-region ratio (7.39 vs the input's 4.62), the flat-region slope (−1.61 vs −2.76) and the absolute orthogonal energy (6.140 vs the input's 3.692, against 0.9× the input's for red_cnn / learn).

**How much of the output is actually the reference's fine structure** (energy accounting, 4-patient means):

Each ROI carries two vectors of the same length: **o**, the object's output high-pass (σ = 1 px) sampled inside the ROI, and **f**, the same from the full-dose reference. Write `E_o ≡ ‖o‖²`, `E_fd ≡ ‖f‖²` and `R ≡ E_o/E_fd` (the ROI ratio of the first column). The reference-collinear part of **o** is its least-squares projection on **f**,

`α ≡ ⟨o, f⟩ / ‖f‖²`  (the driver's `alpha`),  i.e.  `o = α·f + o_⊥` with `⟨o_⊥, f⟩ = 0`,  `‖o‖² = α²‖f‖² + ‖o_⊥‖²`.

Dividing by `‖f‖²` puts the whole account in units of the reference's ROI high-pass energy: `R = α² + ‖o_⊥‖²/‖f‖²`. Note that **`α²` is an energy, not a share** — the shares are `α²/R` and `1 − α²/R`:

| object | E_o/E_fd = R | collinear energy / E_fd (α²) | orthogonal energy / E_fd (R − α²) | collinear share of E_o (α²/R) | orthogonal share of E_o (1 − α²/R) |
|---|---|---|---|---|---|
| red_cnn | 3.876 | 0.5530 | 3.3232 | 14.3% | 85.7% |
| ctformer | 6.735 | 0.5950 | 6.1401 | 8.8% | 91.2% |
| learn | 3.854 | 0.5524 | 3.3015 | 14.3% | 85.7% |
| blur (trap) | 0.432 | 0.0649 | 0.3666 | 15.0% | 85.0% |
| low-dose input | 4.291 | 0.5993 | 3.6915 | 14.0% | 86.0% |

Every row re-adds by hand in both directions: `α² + (R − α²) = R` on the left (0.5530 + 3.3232 = 3.8762, i.e. the printed `R` = 3.876 for red_cnn — the two energy terms are shown to four decimals so that they sum to the three-decimal `R`; this holds in all five rows) and `α²/R + (1 − α²/R) = 1` on the right (14.3% + 85.7%). Means are over the same 192 (4 patients × 48) ROI measurements as above; `α²` is evaluated at the ROI mean `ᾱ` (0.744 for red_cnn) rather than as the mean of the per-ROI `α²` (0.576), which is why the row sums are exact at the precision shown — the two conventions differ by ~4% in the collinear term (per-ROI means: 0.576 / 3.300, and a mean per-ROI orthogonal share of 83.0%). Orthogonal *amplitude* rather than energy is `√(R − α²)` in units of the reference's ROI high-pass amplitude: 1.82 for red_cnn, 2.48 for CTformer.

**Sensitivity to the flat/edge threshold (±1 grade)**, using ROI gradient quartiles instead of the median:

| object | R_flat (q25, stricter flat) | R_edge (q75, stricter edge) |
|---|---|---|
| red_cnn | 4.23 | 3.62 |
| ctformer | 7.57 | 6.13 |
| learn | 4.20 | 3.60 |
| blur | 0.45 | 0.42 |
| low-dose input | 4.69 | 4.00 |

The flat > edge ordering — including the input's own — survives both threshold shifts; the gap it measures is ~10% under the median split and 14–19% under the quartile split.

**Not used as evidence.** An alternative partition by the *reference's* HF amplitude (median of `|h_fd|`) gives 25.1 / 46.1 / 24.9 (flat half) vs 2.36 / 3.92 / 2.34 (high half) for red_cnn / ctformer / learn — a 2.3–46.1× range for the same three objects, versus 3.85–6.74× under the protocol's own median split. That number is dominated by where the denominator is smallest, not by where the output energy is added — it is a property of the normalisation, not of the denoiser, and it is why §3's "3.9–6.7×" cannot be read as "3.9–6.7× of clinical signal".

### 2.4 Limitations declared with this answer

- **ROI sampling is flat soft tissue by construction.** `find_tissue_roi` selects HU 10–120, low-gradient, low-std 32×32 patches (seed 42) from the full-dose reference, so all of this is a statement about texture-free soft tissue; nothing here bounds edge/lesion behaviour.
- **The denominator is small where the ratio is loud.** With the adaptive floor at 1e-4 × full-image FD HF energy, ROIs whose reference HF energy is near the floor make the ratio most sensitive and most inflated; the numbers above are dominated by those ROIs.
- **Two candidate mechanisms, one triage.** The magnitude comparison (output vs undenoised input, and the orthogonal share) separates "residual noise" from "added high-frequency content" cleanly; it cannot resolve the last ~10% by which flat exceeds edge, and it cannot separate sharpening from ringing within CTformer's excess.
- **"~10% less" is a net energy difference, not a removal fraction.** The 10% figure checks out arithmetically (9.7% for red_cnn, 10.2% for learn; 10.0% / 10.6% on the orthogonal term alone), but it counts *net* ROI band energy: a denoiser that removed more noise than it added back as texture, or that redistributed the same energy within the band, would land on a similar number, and the ROIs that dominate this denominator are precisely those whose reference HF energy sits closest to the adaptive floor. What the comparison supports is the weaker claim "the denoisers add no net ROI band energy and leave the input's orthogonal residual largely in place" — it does not measure noise removal.
- **Spectral slope is not a whitening test for CT.** CT noise is not white, and the fitted band (0.125–0.5 cyc/px on 16×16 blocks) sits on the falling tail of the noise power spectrum; the blur row (−7.36) simply shows an attenuation-dominated slope. The column is reported for completeness, not as evidence.
- **No human visual reading was involved.** This is a numerical attribution of where the band energy sits; it does not measure clinical information.

---

## 3. Factual correction to §3's premise

§3 says "All **four** learned methods sit 3.9–6.7× above the full-dose reference, and 23 of 36 measured values across vendors exceed 2×."

The source artifacts — `WS-1_dataset/output/aapm_r3_roi_detectability.json`, `WS-1_dataset/output/aapm_lidc_cross_vendor_spread.json`, and the per-model raw runs `WS-1_dataset/R6_recalc/results/freq_aapm_real_r025_*.json` — carry **`models = [red_cnn, ctformer, learn, blur]`**: **three learned methods plus the blur trap**. CoreDiff carries no `bander`/`freq_roi` field anywhere (the CoreDiff entries under `WS-1_dataset/output/` have no BandER at all), so it cannot be the fourth. There are three learned methods; the "36 measured values" is 12 (patient × vendor-group) slots × 3 learned models, which is consistent with that.

Two smaller numeric notes, for exactness:
- the range's lower end computes to **3.85** (learn 3.8539; red_cnn 3.8762), so "3.9–6.7×" is rounded slightly high at the bottom;
- the 36 values are per-patient-per-vendor ratings for the three learned methods (GE 2/6, Philips 6/6, Siemens 1/6, Toshiba 2/6, AAPM-Siemens-real 12/12 exceed 2×, total 23/36 — `aapm_lidc_cross_vendor_spread.json`, `per_vendor.*.patients[].models[].freq_roi.roi_band_energy_ratio`).

---

## 4. Reproduce

```bash
# (a) inference-only re-run of the metric, 4 objects x 4 test patients x 48 ROIs
#     driver imports WS-1_dataset/R6_recalc/freq_detectability_recalc.py by path
python a_rerun_diag.py --model red_cnn      # ckpt baselines/checkpoints/red_cnn.pt
python a_rerun_diag.py --model ctformer     # ckpt baselines/checkpoints/ctformer.pt   <-- not the small retrain
python a_rerun_diag.py --model learn        # ckpt baselines/checkpoints/learn.pt
python a_rerun_diag.py --model blur         # 5x5 Gaussian, sigma = 1 px

# (a) reproducibility self-check against the on-disk artifact + (b) falsification (read-only)
python selfcheck_final.py
python scripts/prepare-bander-direction-fix.py
```

Paths used by the re-run (session scratch, outside the repository):

- drivers / intermediates: `C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_745ff6c6840d4212ae08918d2177f660\temp\` (`a_rerun_diag_<model>.json`, `s3a_selfcheck_final.json`, `s3a_table.json`, `dump_lines*.py`)
- inputs: the same paired npy used by the R6 recalc — `...\r6_recalc\data\aapm_test_fd`, `...\r6_recalc\data\aapm_test_ld`
- compared against: `WS-1_dataset/R6_recalc/results/freq_aapm_real_r025_{red_cnn,ctformer,learn,blur}.json`

No file in this repository was modified, added or committed as part of this reply other than this file itself (untracked).
