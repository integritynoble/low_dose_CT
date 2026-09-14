# A separable paper: what tolerance a benchmark comparison actually needs

_Written 2026-09-14 against `e7efa20` · companions: [Heyang's handoff](HEYANG_NEXT_2026-09-13.md), [Director decisions](DIRECTOR_DECISIONS.md), [the recalculation report](WS-1_dataset/R6_recalc/R6_recalc_report.md)_

**What this is.** A scope for one self-contained paper, extracted from work already done, chosen so that it perturbs none of the five planned manuscripts. It is a proposal, not an assignment, not an authorship decision, and not permission to change any score, tolerance, registry status, dataset or release. It draws no new measurement; everything it cites is committed.

**What it is not.** It is not the manuscript. The write-up should be done by whoever leads it, and this file deliberately stops at the boundary of the argument rather than drafting it.

## 1. The claim

> A single absolute agreement tolerance cannot express reproduction across environments when the reported metrics span five orders of magnitude. Declaring agreement per metric, in that metric's own units, does — and the distinction is decidable by experiment rather than by preference.

The paper's value is the method and the negative result underneath it, not the verdict it ends on.

## 2. Why it is separable from the planned work

The five drafts in this repository are the v0.5 dataset descriptor (WS-1), the signal-equivalence framework (WS-2), the PET phantom release (WS-2b), the reference-reconstruction corpus (WS-3) and the Year-1 challenge report (WS-4).

This paper touches none of their claims. It says nothing about which reconstruction method is better, whether ROI BandER is the right detectability index, whether the blur control is fair, where the dose knee lies, or any clinical question. Those are exactly the contested surfaces, and this work sits off all of them.

It is **supporting rather than constraining**. The WS-1 manuscript states that a downstream user's `results.json` "should match the published values within the documented floating-point tolerance on equivalent hardware". That sentence is currently an assertion. This paper is the study behind it.

Two nearby pieces of work were considered and rejected for this purpose, for the same reason in both cases:

| Candidate | Why rejected here |
|---|---|
| The BandER control matrix (§3b, BANDER-2/4) | Lands directly on the discriminating index. WS-1 already reports BandER trap separation and the non-discriminativeness of insertion indices; a finding underneath those would constrain the main manuscripts rather than sit beside them. It remains valuable internal work. |
| The insertion-protocol saturation result | Already claimed inside the WS-1 manuscript's validation summary. Not extractable. |

## 3. What already exists

The independent recalculation was run as a genuine replication, not a re-seed, and its provenance is unusually complete. All paths below are in [`WS-1_dataset/R6_recalc/`](WS-1_dataset/R6_recalc/).

**A different environment, not a different seed.** Python 3.12.10 in a separate venv, torch 2.3.0+cu121, torchvision 0.18.0, numpy 1.26.4, on Windows with 2× RTX 4090 and driver 591.86 — against the on-board Linux stack. Different operating system, CUDA build and torch version. This is the part most reproducibility studies cannot offer.

**Fingerprints, committed.** Source-commit SHA plus per-file SHA256 verification of six critical files; `task_spec.json` SHA256; five checkpoint hashes ([`ckpt_hashes.txt`](WS-1_dataset/R6_recalc/hashes/ckpt_hashes.txt)); 364 LIDC and 25 AAPM data-tree hashes; a 57-line `pip freeze`. Twenty-seven result artifacts under `results/`.

**The decisive ablation, already run.** The pre-registered absolute 1e-6 criterion failed for red_cnn, ctformer and corediff, and passed for blur and learn. Route (a) tested the hypothesis that the residual was cuDNN kernel non-determinism, which predicted zero difference under deterministic kernels. It was run with `cudnn.deterministic=True`, `cudnn.benchmark=False`, `use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`, at a cost of about 48 GPU-hours, **by Heyang on the machine holding the checkpoints and data trees**. The result was `n_diffs = 0`, bit-identical — so the prediction failed and the residual is a systematic cross-environment offset, not kernel non-determinism.

That failed prediction is the paper's spine. A reproduction study that merely reports agreement is bookkeeping; one that rules out the obvious explanation by experiment is a result.

**The results table exists.** Under the declared per-metric criterion the worst relative differences are `red_cnn cnr_mean` 6.36e-05, `red_cnn npwe_mean` 3.62e-05, `corediff cnr_mean` 2.50e-05, against psnr residuals near 4e-07 throughout. The residual is metric-dependent across roughly two orders of magnitude, which *is* the argument for declaring per metric. Five models, 764 slices.

## 4. What is left

English write-up; reframing from project-internal audit to a general lesson; and a per-metric characterization of the residual computed from the differences already in [`comparison_full764.json`](WS-1_dataset/R6_recalc/results/comparison_full764.json). No GPU time, no new data, no new collaborator, no clinician, and no dependency on any open rung.

The re-derivation is already executable and currently passes:

```bash
python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check
```

## 5. The boundary the paper must not cross

**Cross-environment agreement of a metric computation is not agreement of the underlying science.** If the paper is readable as validating this benchmark's scientific conclusions, it has stopped being separable and has started making WS-4's argument. State the limit explicitly: what reproduces is the computation, on fixed inputs, under declared hashes.

Two further limits, both already established elsewhere in this repository and not to be re-litigated here: the patient counts are small, and the dose data are simulated or noise-inserted rather than re-acquired.

## 6. Venue

**Medical Physics**, as a Technical Note, is the primary recommendation — it is AAPM's journal and the AAPM 2016 challenge was published there, so the readership is the one that cares whether these numbers reproduce. **Scientific Reports** is the alternative if this paper should sit in Nature Portfolio with the rest of the plan. *Physics in Medicine & Biology* and *Journal of Medical Imaging* also fit.

ReScience C appeared in this file's first draft and is withdrawn: it is for independent third-party replication, and this is self-reproduction within the project. See [`PAPER_TARGET_JOURNALS.md`](PAPER_TARGET_JOURNALS.md) for the full register and the reasoning. Modest by construction — that is the point, not a shortcoming.

## 7. Two decisions for the owner, before it starts

1. **The paper reports that a pre-registered criterion failed and was superseded per metric.** That is ordinary and the whole resolution is already committed here, including the superseded criterion kept verbatim. It should still be an explicit decision to publish rather than a surprise at submission.
2. **Citation direction.** The planned manuscripts should cite this note rather than absorb it, and WS-1's floating-point sentence is the natural place. Agreeing that before submission costs nothing; afterwards it is awkward.

## 8. Effect on the original plan, stated honestly

Separable is not the same as free. The scientific surfaces are untouched, but three costs are real and one of them is the only one worth weighing.

**No effect on the science.** It changes no committed number — `tolerance_audit` is byte-for-byte unchanged and no measurement moved. It blocks and unblocks no rung, consumes no GPU time and no data access, and needs no radiologist or physicist, so it does not compete for the human-gated work that rungs 10, 13 and 14 wait on. It makes no claim about method ranking, the discriminating index, the control, the dose knee or clinical validity.

**Cost 1 — it discloses something currently internal.** Both repositories became private, so the superseded criterion is not presently readable by anyone outside. Publishing means stating that a pre-registered absolute 1e-6 failed on three of five models and was replaced by a per-metric relative criterion. A hostile reader can call that moving the goalposts, and a later WS-1 or WS-4 reviewer may encounter it.

The defence is strong and it is already on the record: route (a) was run **first**, at about 48 GPU-hours, so the criterion was not adjudicated after seeing a convenient result, and the superseded criterion and its FAIL are kept verbatim beside the new one. Publishing it framed by that evidence is better than having it surface bare. But the decision to disclose is a decision, and it belongs to the owner rather than to this file.

**Cost 2 — Heyang's time, and this is the one that matters.** He is P0 on the merge repairs and the invalid-input and publication checks, and P1 on the BandER control work that only his machine can do. A write-up of some weeks competes with that directly. This is the only way the paper delays the plan, and it is a scheduling decision, not a scientific one. If the P0 items slip, the paper was the wrong call regardless of its merits.

**Cost 3 — a small narrowing of WS-1, and an ordering choice.** WS-1's Technical Validation already reports per-voxel regeneration tolerance; cross-environment floating-point agreement would become this note's contribution to cite rather than WS-1's to claim. Whichever publishes first, the other cites it. Deciding that in advance costs nothing.

**One mechanical precaution.** The committed hashes carry absolute paths on a named machine. The existing publication-safety check applies before anything leaves the repository.

## Verification record

Checked on 2026-09-14 at `e7efa20`: the five manuscript titles read from their `paper_draft/manuscript.tex` files; the WS-1 floating-point sentence and its BandER/insertion claims read from that manuscript; the environment, hash counts (5 checkpoints, 364 + 25 data, 57 pip lines, 27 result files) and route-(a) evidence read from `R6_recalc/`; the per-metric residuals reproduced by running `recompare_per_metric.py --check`, which reported PASS for all five models and agreement between the committed verdict and the re-derivation. No image, reconstruction, prediction or reader result was generated, and no scoring rule, tolerance, registry status, dataset or release permission is changed by this file.
