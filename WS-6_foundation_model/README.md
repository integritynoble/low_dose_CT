# WS-6 — Foundation Model for Low-Dose CT (Track 9 sub-track 9f)

A **CT-specific foundation model** for low-dose reconstruction, deployable as a swappable denoiser inside the WS-3 unrolled-iterative architecture. Year-2+ stretch workstream; complements WS-3 rather than replacing it.

---

## Why this is a separate workstream, not part of WS-3

WS-3's reference method is deliberately small (~4M params, ~20M ensemble) and built on the "decomposable improvability" principle: when a better denoiser is available, swap it in. WS-6 is the natural follow-up workstream that builds and validates that better denoiser as a publishable contribution in its own right, with its own L4 cert variant.

Building this from the start would conflict with WS-3's Year-1 deliverables (compute and data budget) and the team's bandwidth before NIH R21 lands. Separating it as WS-6 lets Year-1 ship on time while creating a clear lane for the Year-2+ contribution once the reference exists.

---

## Goals

1. **Publish a peer-reviewed paper** at **MICCAI 2028** or ***CVPR 2028*** (whichever fits the year-3 timeline) introducing the CT foundation model and demonstrating cross-vendor + cross-task transfer. Fallback: *IEEE Transactions on Medical Imaging*.
2. **Release pretrained weights publicly** on HuggingFace under Apache 2.0, with model card documenting training data, training compute, intended uses, and known failure modes.
3. **Register a second L4 cert (v2)** on PWMRegistry — the foundation-model variant of the reference reconstruction, distinct from WS-3 v1. The two cert versions coexist on the leaderboard so deployers can pick by their compute / quality trade-off.

A successful WS-6 means: an external researcher can `pip install pwm_ct_foundation`, fine-tune the released weights on their institution's data with under one A100-day of training, and produce a method that beats the WS-3 reference on cross-vendor evaluation.

---

## Scope decision (primary path) — fine-tune existing medical foundation model

The Year-1 + Year-2 plan does **not** assume from-scratch foundation-model training. The primary path is to **fine-tune an existing medical foundation model** for low-dose CT denoising. Candidates to evaluate at Phase 1:

| Candidate base model | Pretraining domain | Estimated fine-tune compute (single model) | Risk |
|---|---|---|---|
| **MedSAM** (segmentation FM) | Multi-modal medical imaging | ~100–500 A100-hr (LoRA / adapter) | Adaptation from segmentation to denoising is non-trivial |
| **RadFM** (radiology multi-modal) | CT + MR + X-ray multi-task | ~200–800 A100-hr | Largest base model; biggest deployment burden |
| **CT-CLIP / CT-FM** (vendor-specific or community) | CT-only contrastive | ~100–400 A100-hr | Direct domain match; smallest model + closest fit |
| **Self-supervised MAE on PWM-LDCT** | CT slices only, single-source | ~200–600 A100-hr (pretrain + fine-tune) | Most controlled but smallest pretrain corpus |

Selection is part of Phase 1; defaults to CT-CLIP / CT-FM-style if a community-released CT-domain base model exists at decision time, otherwise MedSAM with a denoising adaptation head.

**Stretch path (Phase 3, contingent on R21 funding)**: train a CT-specific foundation model from scratch on multi-vendor PWM-LDCT v2 plus partner-site data. Compute scale is documented in the Compute budget section below; this becomes the v3 L4 cert.

---

## Compute budget

The compute cost spread for a CT foundation model is wide because ``foundation model'' covers four meaningfully different scales of effort. We document all four so the team can pick the tier that matches funding at decision time, and so external collaborators can calibrate expectations.

### Four tiers

| Tier | Model size | Approach | GPUs | Wall time | Total GPU-hr | Cloud cost (spot) | Funded by |
|---|---|---|---|---|---|---|---|
| **A. Fine-tune existing medical FM** | 100M–300M (use base as-is) | LoRA / adapter / partial-FT | 1–2× A100 80GB | 3–10 days | 100–500 A100-hr | $300–$2K | Reserve |
| **B. Self-supervised pretrain on PWM-LDCT** | 100–300M params, ~50K slices | MAE / diffusion-denoising obj. | 4–8× A100 | 2–4 weeks | 2K–10K A100-hr | $5K–$30K | Reserve (with approval) |
| **C. Credible CT-specific FM from scratch** | 300M–1B params, ~500K–1M slices | self-supervised + multi-vendor | 8–32× A100 *or* 8–16× H100 | 1–3 months | 20K–100K A100-hr | $50K–$300K | R21 funded **or** academic-cluster partnership |
| **D. SOTA-scale medical FM** | 1B–10B params, ~10M slices | competitive with RadFM-large | 64–256× H100 cluster | 2–8 weeks on real cluster | 100K–1M H100-hr | $300K–$3M | R01 + industry partnership; out of scope for this workstream |

Add a 5-model deep ensemble multiplier (~5×) to any tier if shipping the WS-3-style ensemble. For Tier A this stays Reserve-fundable; for Tier C the ensemble may need to be smaller (3 models) or skipped.

### Calibration against published medical foundation models

| Model (year) | Pretraining corpus | Total compute (reported / estimated) | Cloud-equivalent cost |
|---|---|---|---|
| MedSAM (2024) | 1.5M images, multi-modal medical | ~600 A100-hr (≈ 8× A100 × 3 days) | ~$2K |
| CT-CLIP (2024) | ~50K CT scans | ~1K–3K A100-hr | ~$3K–$10K |
| RadFM (2023) | ~50M images, multi-modal radiology | ~10K–20K A100-hr (estimated) | ~$30K–$60K |

WS-6 Tier A matches the MedSAM-fine-tune scale; Tier B matches a CT-CLIP-scale effort; Tier C is RadFM territory.

### Where to source the GPUs

| Source | Cost | Lead time | Best for |
|---|---|---|---|
| AWS / GCP / Azure spot A100 / H100 | $1–4/hr | hours | Tier A and B; flexible |
| Lambda Labs / RunPod / CoreWeave | similar to spot, often cheaper | hours–days | Tier A and B |
| UTSW BioHPC cluster | typically free for lab members | 1–2 weeks setup | Tier A; check capacity for B |
| NSF ACCESS (Frontera, Bridges-2) | free for academic | 3–6 months proposal → allocation | Tier B and C if we can wait |
| Anthropic / OpenAI / Google research-credit programs | $5K–$50K per award | weeks–months apply | Tier A and B; good for public credibility |
| Cloud-vendor research-credit programs (AWS / GCP / Azure) | $10K–$100K per award | 1–3 months apply | Tier B and C |
| NVIDIA Inception / Healthcare partnerships | in-kind compute | months to negotiate | Tier C; opens after a publication |

### Recommended path by year

| Year | Tier | What we actually do |
|---|---|---|
| **Year 2 (D9+540 → D9+800)** | **Tier A** | 1–2 A100 spot for 2–3 weeks; $2K–$5K Reserve spend. Single researcher runs it; intern owns the data pipeline. Whichever community CT-domain FM has been released by D9+540 becomes the default base; MedSAM is the fallback. |
| **Year 3 (D9+800 → D9+1095)** | **Tier B** (likely), **Tier C** (stretch) | 4–8 A100 for 2–4 weeks self-supervised pretraining on PWM-LDCT, plus fine-tune. ~$10K–$30K Reserve spend if no grant, or step up to Tier C ($50K–$300K) if R21 lands or NSF ACCESS allocation comes through. |
| **Year 4+** | **Tier D as a partnership** | Do not budget. Pursue only as an in-kind contribution from a lab that already has the cluster (Stanford BMI, MIT CSAIL medical groups, NVIDIA Healthcare). |

### What we explicitly do not budget for

The team is **not** planning Tier D from-scratch. SOTA-scale medical FMs (RadFM-large class and beyond) require 64–256-GPU clusters and $300K+ training budgets that are beyond Reserve, R21, and even most R01 awards. The intended path for that scale is contributing the PWM-LDCT dataset, the signal-equivalence framework, and the Tier A/B/C trained variants to a partner lab that already operates a cluster, and co-authoring the resulting paper.

---

## Tasks

### Phase 1 — Architecture selection (D9 + 540 → D9 + 600)

| # | Task | Output |
|---|---|---|
| 1.1 | Literature review of medical foundation models released since WS-3 v1 (paper drop date) | `phase1/literature_review.md` |
| 1.2 | Evaluate 2-3 base-model candidates on the WS-3 unrolled-iterative architecture (denoiser slot) | `phase1/candidate_benchmark.json` |
| 1.3 | Select primary base model + fallback | Decision recorded in `phase1/architecture_decision.md` |
| 1.4 | Compute budget agreed with funding source (Reserve, R21, partner GPU cluster) | Approved compute plan |

### Phase 2 — Fine-tuning + evaluation (D9 + 600 → D9 + 800)

| # | Task | Output |
|---|---|---|
| 2.1 | Fine-tune base model on PWM-LDCT~\citep{ws1dataset} training split with low-dose paired supervision | Fine-tuned checkpoint v0.1 |
| 2.2 | Drop-in replace the WS-3 U-Net denoiser; verify the unrolled-iterative wrapper works | `v0.1/` working pipeline |
| 2.3 | Cross-vendor evaluation: leave-one-vendor-out per WS-3 protocol; compare to WS-3 v1 baseline | Cross-vendor comparison table |
| 2.4 | Hyperparameter search (LR, fine-tune-only vs full-FT, prompt-tuning vs adapter-tuning) | Best-config checkpoint |
| 2.5 | Deep-ensemble extension: 5-member ensemble of fine-tuned variants (different seeds + different fine-tune subsets) | Ensemble checkpoint set |
| 2.6 | Compute 5-tuple credentials under WS-2 framework | `credentials.json` for FM variant |

### Phase 3 — Stretch: from-scratch training (D9 + 800 → D9 + 1100, contingent on funding)

| # | Task | Output |
|---|---|---|
| 3.1 | Acquire pretraining corpus: PWM-LDCT v2 + partner-site bulk CT + public unlabeled CT | Pretraining manifest |
| 3.2 | Self-supervised pretraining (MAE or diffusion-denoising objective) at ~100M-300M param scale | Pretrained backbone |
| 3.3 | Fine-tune for low-dose denoising; compare against Phase 2 fine-tuned baseline | v2.0 checkpoint |
| 3.4 | Validate cross-vendor + cross-task transfer (e.g., to abdominal, pediatric subsets) | Transfer evaluation report |

### Phase 4 — Paper + L4 v2 cert (D9 + 800 → D9 + 1095)

| # | Task | Output |
|---|---|---|
| 4.1 | Draft manuscript (Methods, Fine-tuning protocol, Cross-vendor results, Comparison to WS-3 v1, Transfer studies) | Draft v1 |
| 4.2 | Submit to MICCAI 2028 or CVPR 2028 | Submission |
| 4.3 | Publish RunBundle to IPFS; register L4 v2 cert on PWMRegistry as distinct version | L4 v2 hash on chain |
| 4.4 | Release pretrained weights on HuggingFace; publish model card | Public release |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 540 | WS-3 v1 paper submitted; WS-6 design phase opens | pending (Year 2) |
| D9 + 600 | Architecture decision; base model selected | pending |
| D9 + 730 | R21 funding decision; Phase 3 go/no-go | pending |
| D9 + 800 | Fine-tuning v0.1 complete; cross-vendor results | pending |
| D9 + 900 | v0.1 manuscript drafted; if Phase 3 funded, pretraining started | pending |
| D9 + 1095 (2029) | **Paper submitted to MICCAI / CVPR; L4 v2 cert on chain; weights on HuggingFace** | pending |
| D9 + 1300 | **Paper accepted; second seed entry on the recurring leaderboard** | pending |

---

## Done when

- [ ] Paper accepted at MICCAI / CVPR 2028 (or fallback *IEEE TMI*)
- [ ] Pretrained weights publicly released on HuggingFace under Apache 2.0
- [ ] L4 v2 cert registered on PWM mainnet
- [ ] WS-6 method beats WS-3 v1 reference on cross-vendor PSNR by ≥ 1 dB, OR
- [ ] WS-6 method achieves comparable cross-vendor PSNR at < 10% of inference compute, OR
- [ ] WS-6 method shows transfer learning to a clinical task not seen during fine-tuning (e.g., abdominal segmentation)
- [ ] At least one of those three superiority criteria holds with a passing signal-equivalence credential per WS-2

---

## Subfolders (created on demand)

| Path | Purpose | Status |
|---|---|---|
| `phase1/` | Literature review, candidate-model benchmarks, architecture decision | pending Phase 1 |
| `v0.1/` | Fine-tuned base model | pending Phase 2 |
| `v1/` | Production fine-tuned + ensemble | pending Phase 2 |
| `pretrained_from_scratch/` | Phase 3 from-scratch model (contingent on funding) | stretch |
| `runbundle/` | PWM-format RunBundle for L4 v2 cert | pending Phase 4 |
| `paper_draft/` | MICCAI / CVPR manuscript | pending Phase 4 |
| `model_card/` | HuggingFace model card | pending Phase 4 |

---

## Dependencies

- **WS-3 v1 must exist** as a baseline to compare against. WS-6 cannot ship before WS-3's L4 cert is on chain.
- **WS-1 PWM-LDCT v1.0.0+** for fine-tuning data; v2 (with partner-site expansion) for Phase 3 stretch.
- **WS-2 framework v1.0.0** for credential computation.
- **Compute**: either NIH R21 funding (D9+730 stretch), academic GPU cluster partnership, or cloud credit grant. Fine-tuning is feasible on Reserve PWM (~$5-15K cloud spend); from-scratch is not.
- **Base model availability**: depends on which medical foundation models are released between now and D9+540. The architecture decision (Phase 1) is intentionally deferred to that date.

---

## Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| No suitable medical foundation model released by D9+540 | Low (15%) | Use self-supervised MAE on PWM-LDCT as fallback base; smaller but still publishable |
| Fine-tuning does not beat WS-3 v1 on cross-vendor | Medium (30%) | Frame paper as a negative-result + scaling-law contribution; still publishable and valuable to the field |
| R21 not funded → Phase 3 from-scratch infeasible | High (75% base rate) | Ship Phase 2 fine-tuned model only; stretch to from-scratch in WS-6 v2 once R21/R01 lands |
| Existing base model has restrictive license | Medium (25%) | Default to permissive-license bases; if must use restrictive base, release fine-tuning recipe under Apache 2.0 separately |
| Inference compute too large for the target deployment use case | Low (20%) | Distillation pass after Phase 2; ship a small + a large variant |

---

## Cross-references

- [`../WS-3_reference_method/README.md`](../WS-3_reference_method/README.md) — the reference method that WS-6 builds on / drops into
- [`../WS-1_dataset/README.md`](../WS-1_dataset/README.md) — training data
- [`../WS-2_framework/README.md`](../WS-2_framework/README.md) — credential format for the WS-6 L4 cert
- [`../WS-4_leaderboard/README.md`](../WS-4_leaderboard/README.md) — both WS-3 v1 and WS-6 variants compete on the same leaderboard
- [`../pwm_integration/l4_cert.md`](../pwm_integration/l4_cert.md) — current L4 cert structure; WS-6 will register a v2 variant
- [`../WS-5_grants/README.md`](../WS-5_grants/README.md) — R21 funding gates the Phase 3 stretch
