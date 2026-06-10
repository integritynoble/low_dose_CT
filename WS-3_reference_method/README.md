# WS-3 — Reference Reconstruction Method (Track 9 sub-track 9c)

An **improvable, open-source low-dose CT reconstruction method** scoring top-25% on the (initially empty) leaderboard, with rigorous uncertainty quantification, cross-vendor generalization, and a verified L4 cert on PWM mainnet.

---

## Goals

1. **Publish a peer-reviewed paper** at ***Nature Scientific Data*** (primary) as a **Data Descriptor** for the released derived-data corpus — reference reconstructions + per-pixel uncertainty maps + paired error maps + downstream-task score maps + signal-equivalence credentials over the WS-1 benchmark (the reconstruction pipeline is demoted to data provenance). The prior MICCAI / *IEEE TMI* **method**-paper framing is preserved at [`paper_draft/manuscript_method_miccai.tex`](paper_draft/manuscript_method_miccai.tex) as a fallback. See [`paper_draft/README.md`](paper_draft/README.md) for the reframe rationale and submission-readiness gates.
2. **Register L4 cert on PWMRegistry** — the first L4 cert against the WS-1 L3 benchmark. Future community submissions reproduce this pattern; cleanliness here scales.
3. **Open-source the code under Apache 2.0** with a reproducible RunBundle on IPFS — `docker run` reproduces published numbers bit-identically (within FP tolerance).

A successful WS-3 means: an external reviewer pulls the RunBundle CID from PWMRegistry, runs `docker run` on a fresh VM, and reproduces every PSNR / SSIM / LPIPS / task-AUC number in the paper.

---

## Architecture (committed direction)

| Component | Choice | Rationale |
|---|---|---|
| Backbone | Unrolled iterative reconstruction (10-20 iterations) | Combines physical priors (Radon) + learned priors (CNN denoiser per iter); interpretable; differentiable |
| Forward model | Reuse `packages/pwm_core/contrib/modalities/ct_radon.py` | Already validated against PWM's 172-modality test suite; single source of truth |
| Denoiser at each iteration | Trainable U-Net-style CNN, weights shared across iterations | Compact (< 5M params); avoids over-parameterization |
| Warm start | TV regularization | Stable initialization; replace as training matures |
| Uncertainty quantification | Deep ensembles (5 models) — primary; MC dropout fallback | Ensembles outperform dropout on calibration |
| License | **Apache 2.0** | No encumbered weights, no patent-pending architectures |
| Inference target | < 5 s/slice on a single A100 | Operational claim for clinical viability |

**Why unrolled iterative is *improvable* by design.** Each component — denoiser, forward model, iteration schedule, UQ method — can be improved independently. Each improvement is a publishable follow-up paper that beats the reference without invalidating it. A pure-transformer or pure-diffusion reference would force replacement of the entire backbone to improve; citations would split.

**Why explicitly *not* chase SOTA.** A reference that is almost SOTA but *improvable* draws competition, citations, and follow-up papers. The leaderboard wins the long game; the last 0.3 dB does not.

---

## Tasks

### Phase 1 — Baselines (D9 + 30 → D9 + 60)

Three baselines reproduced inside this folder under `baselines/`. They serve three purposes: (a) reference points the WS-3 method must beat or match, (b) seed entries for the WS-4 leaderboard, (c) input to the WS-2 Phase A pilot.

| # | Task | Output |
|---|---|---|
| 1.1 | `baselines/red_cnn/` — reproduce Chen et al. 2017 within ± 0.5 dB PSNR | Docker image, results.json, checkpoint |
| 1.2 | `baselines/transformer/` — reproduce a 2023-24 transformer SOTA (e.g., CTformer / TransCT) | Docker image, results.json, checkpoint |
| 1.3 | `baselines/diffusion/` — reproduce a 2024 score-based / diffusion SOTA | Docker image, results.json, checkpoint |
| 1.4 | `baselines/comparison/` — unified evaluation harness; one entry point produces a comparison JSON | Comparison runner + figures |

### Phase 2 — v0.1 prototype (D9 + 60 → D9 + 90)

| # | Task | Output |
|---|---|---|
| 2.1 | 10-iteration unrolled loop in PyTorch; single trainable U-Net denoiser (weights shared); TV warm start | `v0.1/model/`, train.py, eval.py |
| 2.2 | Train on LIDC-IDRI + AAPM 2016 simulated 25% photon-count low-dose | Trained checkpoint |
| 2.3 | Evaluate on AAPM 2016 real quarter-dose held-out test; PSNR ≥ 34 dB target | `v0.1/results.json` |
| 2.4 | Reproducibility: `docker run` from fresh VM matches results.json | Docker image |

### Phase 3 — v1 with UQ + cross-vendor (D9 + 150 → D9 + 365)

| # | Task | Output |
|---|---|---|
| 3.1 | Deep ensembles (5 independently-seeded models); UQ calibration on held-out test (Spearman ρ ≥ 0.5 per-pixel UQ vs per-pixel error) | `v1/ensemble/` |
| 3.2 | Train on full WS-1 dataset including real low-dose pairs | v1 checkpoints |
| 3.3 | Cross-vendor generalization experiments (train on Siemens, test on GE, etc.) | Cross-vendor results table |
| 3.4 | Compute 5-tuple credentials per WS-2 L2 spec for ≥ 3 clinical tasks (lung nodule detection, liver lesion segmentation, abdominal quantification) | `v1/dose_equivalence_credentials.json` |
| 3.5 | Package as PWM RunBundle (Dockerfile + eval.py + results.json + credentials + checkpoint pointer) | RunBundle directory + IPFS CID |

### Phase 4 — Paper + L4 cert (D9 + 270 → D9 + 540)

| # | Task | Output |
|---|---|---|
| 4.1 | Draft manuscript (Methods, Architecture, UQ, Cross-vendor, Credentials, Comparison) | Draft v1 |
| 4.2 | Deposit the corpus (figshare/Zenodo DOI); submit Data Descriptor to *Scientific Data*; respond to reviewer comments | Acceptance letter |
| 4.3 | Publish RunBundle to IPFS with stable CID | CID recorded in L4 cert |
| 4.4 | Author and register L4 cert on PWMRegistry | L4 hash on chain |
| 4.5 | Validate Track 7 agent-query loop returns this cert as the SOTA pointer | Agent demo proven |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 60 | RED-CNN reproduced ± 0.5 dB; transformer + diffusion baselines underway | pending |
| D9 + 90 | 3 baselines reproduced; v0.1 prototype demo at week-9 review | pending |
| D9 + 120 | v0.1 code frozen; handoff to Phase B v1 development | pending |
| D9 + 180 | v1 single-model ablation done; deep-ensemble training started | pending |
| D9 + 270 | v1 deep ensemble + UQ calibration validated; cross-vendor results | pending |
| D9 + 365 | RunBundle packaged; 5-tuple credentials computed; manuscript drafted | pending |
| D9 + 540 | **Corpus deposited + Data Descriptor submitted to *Scientific Data*; L4 cert on chain; agent-query loop validated** | pending |
| D9 + 730 | Paper accepted; method is one of the seed leaderboard entries when WS-4 launches | pending |

---

## Done when

- [ ] Data Descriptor accepted at *Nature Scientific Data* (fallback: MICCAI / *IEEE TMI* via the preserved method draft)
- [ ] Derived-data corpus deposited (figshare/Zenodo DOI, CC BY 4.0) and distinct from the WS-1 raw-scan release
- [ ] Code open-sourced under Apache 2.0
- [ ] L4 cert against WS-1 benchmark on PWM mainnet
- [ ] RunBundle reproducible from IPFS (verified by external party)
- [ ] Per-pixel uncertainty correlates with per-pixel error (Spearman ρ ≥ 0.5 on held-out test)
- [ ] Cross-vendor generalization: < 2 dB PSNR drop on a held-out vendor
- [ ] 5-tuple credentials computed for ≥ 3 clinical tasks per L2 spec
- [ ] First Track 7 agent query for "SOTA 25% dose chest CT" returns this method

---

## Subfolders

| Path | Purpose | Status |
|---|---|---|
| `corpus_emit/` | Credential-emission step: turns cohort task scores into deposit-ready `credential.json` records + `all_credentials.jsonl` index, via the WS-2 library | **wired + tested** (18 tests pass on synthetic scores; real scores arrive Phase 3) |
| `deposit/` | *Scientific Data* deposit kit: checklist + `dataset_metadata.json` schema/template + `package_corpus.py` (fills metadata counts + writes/verifies `MANIFEST.sha256`) | **ready + tested** (13 tests; corpus + DOI gated on Phase 3) |
| `baselines/` | RED-CNN + transformer + diffusion + comparison harness | pending Phase 1 |
| `v0.1/` | Phase 2 prototype | pending Phase 2 |
| `v1/` | Phase 3 production version | pending Phase 3 |
| `runbundle/` | PWM-format RunBundle for L4 cert | pending Phase 3 |
| `paper_draft/` | *Scientific Data* **Data Descriptor** (`manuscript.tex`, 8 pp, compiles clean) + preserved MICCAI method draft (`manuscript_method_miccai.tex`) | reframed; validation tables gated on Phase 3 data + deposit |

---

## Per-baseline contract

Each baseline directory must contain:

```
baselines/<method>/
├── README.md           # paper citation, published numbers, repro recipe
├── Dockerfile          # pinned environment (CUDA 12.x, pinned PyTorch)
├── train.py            # entry point: docker run ... train --seed 42
├── eval.py             # entry point: docker run ... eval --checkpoint X --dataset Y
├── results.json        # PSNR, SSIM, LPIPS, task_AUC, runtime, GPU memory
└── checkpoint/         # (or pointer to HF / IPFS)
```

Reproducibility checklist for every baseline:

- [ ] PyTorch + CUDA version pinned in Dockerfile.
- [ ] Random seed propagated to: torch, numpy, python `random`, CUDA RNG, DataLoader workers.
- [ ] Deterministic CuDNN (`torch.backends.cudnn.deterministic = True`).
- [ ] Data loader is `pwm_ldct_loader` (from WS-1), not a one-off rewrite.
- [ ] Eval metrics computed with the same library as `baselines/comparison/`.

**If a baseline cannot be reproduced within tolerance, that itself is a publishable finding** — and a flag for the field. Document the gap in `<method>/README.md`.

---

## Cross-references

- [`../WS-1_dataset/`](../WS-1_dataset/) — training and evaluation data
- [`../WS-2_framework/`](../WS-2_framework/) — credentials computed against the framework
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — this method is the reference seed entry
- [`../WS-6_foundation_model/`](../WS-6_foundation_model/) — Year-2+ follow-up that drops a CT foundation model into the unrolled-iterative loop's denoiser slot; the explicit reason this method targets *decomposable improvability* rather than SOTA
- [`../pwm_integration/l4_cert.md`](../pwm_integration/l4_cert.md) — on-chain L4 cert (v1; WS-6 will register a v2 variant)
