# PWM Low-Dose CT Grand Challenge

**Heyang — current assignment:** [Review and next steps, 20 September](HEYANG_NEXT_2026-09-20.md). Finish `Heyang-paper/` first; then follow the ordered CT + agent tasks.

[![CI](https://github.com/integritynoble/low_dose_CT/actions/workflows/ci.yml/badge.svg?branch=heyang)](https://github.com/integritynoble/low_dose_CT/actions/workflows/ci.yml)
[![WS-3 CI](https://github.com/integritynoble/low_dose_CT/actions/workflows/ws3-ci.yml/badge.svg?branch=heyang)](https://github.com/integritynoble/low_dose_CT/actions/workflows/ws3-ci.yml)

**Implementation home** for the canonical, open, vendor-agnostic **benchmark + theoretical framework + reference algorithm + permanent competition** for low-dose CT reconstruction.

**Five-year goal:**

> *"If your low-dose CT reconstruction method is not on the PWM Low-Dose CT Challenge leaderboard, it is not state-of-the-art."*

---

## How this repo is organized

Seven self-contained folders. Each folder owns one workstream and reads as a single document: **Goal → Tasks → Timeline → Done when**.

| Folder | Workstream | One-line goal |
|---|---|---|
| [`WS-1_dataset/`](WS-1_dataset/) | Dataset (9a) | Publish a multi-vendor paired-dose CT dataset paper at *Nature Scientific Data* and register L3 on PWM mainnet |
| [`WS-2_framework/`](WS-2_framework/) | Signal-equivalence framework (9b) | Publish the formal framework at *Nature Methods* and ship `pwm_dose_equivalence` on PyPI; register L2 |
| [`WS-3_reference_method/`](WS-3_reference_method/) | Reference reconstruction (9c) | Publish an open-source, improvable reference method at MICCAI or *IEEE TMI*; register L4 cert |
| [`WS-4_leaderboard/`](WS-4_leaderboard/) | Permanent competition (9d) | Launch a recurring competition at RSNA/ISBI; publish an *annual* review paper at *npj Digital Medicine* |
| [`WS-5_grants/`](WS-5_grants/) | NIH funding (9e) | Secure NIH R21 funding (then R01) to backfill the work |
| [`WS-6_foundation_model/`](WS-6_foundation_model/) | CT foundation model (9f, Year-2+) | Fine-tune (or train) a CT foundation model as a drop-in WS-3 denoiser; publish at MICCAI / CVPR; register L4 v2 cert |
| [`pwm_integration/`](pwm_integration/) | On-chain protocol | Register L2/L3/L4 on PWMRegistry; prove the Track 7 agent-query loop returns non-empty |

Each WS folder's README is the source of truth for that workstream. There is no separate `plan.md` in this repo — the WS folder READMEs *are* the plan.

**Note on WS-6**: WS-6 is a Year-2+ stretch workstream that builds on WS-3 rather than replacing it. It exists because WS-3's "decomposable improvability" architecture is designed exactly so the denoiser can be swapped for a foundation-model variant in a follow-up; WS-6 is that follow-up. WS-6 does not start until WS-3 v1 ships at D9 + 540.

---

## Timeline at a glance (D9-anchored)

D9 = 2026-05-20 (PWM mainnet deploy day). All dates below are **relative**.

| Date | Milestone | Folder |
|---|---|---|
| D9 + 30 | First Docker-reproducible dataset pipeline; first reproduced baseline | WS-1, WS-3 |
| D9 + 90 | 3 baselines reproduced ± 0.5 dB; framework pilot computed end-to-end | WS-2, WS-3 |
| D9 + 180 | Reference method v0.1 done; framework theory in flight | WS-2, WS-3 |
| D9 + 270 | Framework draft posted; reference method v1 training; R21 LOI prep | WS-2, WS-3, WS-5 |
| **D9 + 365** | **Dataset paper submitted + framework paper submitted + L2/L3 on chain + R21 submitted** | WS-1, WS-2, WS-5 |
| **D9 + 540** | **Reference-method paper submitted + L4 cert on chain + first Track 7 agent query returns non-empty + WS-6 design phase opens** | WS-3, pwm_integration, WS-6 |
| **D9 + 730** | **Competition launched at RSNA/ISBI; ≥ 20 submissions; first annual review paper drafted; R21 funding decision (gates WS-6 Phase 3)** | WS-4, WS-5, WS-6 |
| D9 + 900 | Annual review #1 submitted; R01 LOI prep; WS-6 fine-tuning v0.1 complete | WS-4, WS-5, WS-6 |
| D9 + 1095 (2029) | WS-6 foundation-model paper submitted to MICCAI / CVPR; L4 v2 cert on chain | WS-6, pwm_integration |

---

## Three deliverables per workstream

Every WS folder commits to three outputs, none optional:

1. **A peer-reviewed paper** (named venue + acceptance gate). For WS-5 this is the *funded grant*, not a paper.
2. **A PWM on-chain artifact** (L2, L3, or L4). For WS-4 + WS-5 this is *participation in* the L2/L3/L4 ecosystem rather than registering a new spec.
3. **Code or data that a third party can download, run, and reproduce today.** No paper without a working artifact.

If a deliverable cannot be downloaded today, run today, and scored today, it is not done.

---

## Reproducibility contract

Every code or data artifact in this repo must satisfy:

```
docker run pwm-ldct-<artifact>:<version> --seed 42
```

and reproduce the published numbers bit-identically (within FP tolerance). PWM is a *reproducibility protocol*; its own publications must hold that standard.

---

## Architecture commitments (do not relitigate without strong reason)

- **Reference method targets top-25%, not SOTA.** Improvable beats unbeatable on the leaderboard's long game.
- **Architecture is unrolled iterative** (10-20 iterations, U-Net denoiser with shared weights, TV warm start, deep ensembles for uncertainty). Decomposable improvability is the design principle.
- **Forward model is reused** from PWM's existing CT modality (`packages/pwm_core/contrib/modalities/ct_radon.py`); single source of truth.
- **The framework is modality-general by construction.** Signal-equivalence covers CT dose reduction, MRI accelerated reconstruction, and PET low-activity scans under one formalism. CT is the primary validator; MRI and PET are worked examples.
- **License is Apache 2.0** for all code; datasets follow upstream license.

---

## License

Code: **Apache 2.0** (LICENSE file pending — add before first external submission).
Datasets: as upstream license permits.
- LIDC-IDRI — free, NBIA registration.
- AAPM 2016 — access-controlled, Mayo request.
- UTSW clinical data — PhysioNet-credentialed.

---

*Updated 2026-05-20.*
