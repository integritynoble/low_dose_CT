# L4 Cert — PWM Reference Reconstruction Method

**Status:** ⏳ Draft pending Phase B+C reference-method development (WS-3).
**Target on-chain date:** D9 + 540.
**Backing paper:** [`../WS-3_reference_method/paper_draft/`](../WS-3_reference_method/) (target venue: MICCAI / *IEEE TMI*).
**Workstream:** WS-3.
**Cert authority:** PWM Track 9 team — first L4 cert against the L3 benchmark.

---

## What this cert claims

> "The PWM reference reconstruction method **v1.0** achieves the published `results.json` metrics on the PWM Low-Dose CT Benchmark **v1.0**, and the published 5-tuple credentials are valid under the **Dose-Equivalence Framework v1.0**."

A third party can verify the claim by:
1. Pulling the L3 dataset from PhysioNet (per L3 spec access protocol).
2. Pulling the RunBundle from IPFS (CID below).
3. Executing `docker run` per the RunBundle's eval entry point.
4. Comparing the produced `results.json` to the published `results.json` (bit-identical within FP tolerance).

---

## Method summary

| Item | Value |
|---|---|
| Architecture | Unrolled iterative reconstruction (10-20 iterations) |
| Per-iteration denoiser | U-Net (weights shared across iterations) |
| Forward model | `packages/pwm_core/contrib/modalities/ct_radon.py` |
| Uncertainty quantification | Deep ensemble (5 models) |
| Training data | L3 benchmark train split (60% of patients) |
| License | Apache 2.0 |
| Code repository | (TBD — likely github.com/integritynoble/pwm-ldct-reference) |
| Trained weights | (TBD — HF / IPFS) |

---

## Performance (to be filled at submission)

```yaml
l4_results:
  benchmark: pwm_low_dose_ct_benchmark_v1
  evaluated_at: TBD
  dose_levels:
    "0.10":
      PSNR: { mean: TBD, ci_95: [TBD, TBD] }
      SSIM: { mean: TBD, ci_95: [TBD, TBD] }
      LPIPS: { mean: TBD, ci_95: [TBD, TBD] }
      task_AUC: { mean: TBD, ci_95: [TBD, TBD] }
    "0.25":
      ...
    "0.50":
      ...
    "1.00":
      ...
  inference_seconds_per_slice: TBD
  gpu_memory_gb: TBD
  cross_vendor_psnr_drop: TBD          # vendor in training → vendor held out
  uncertainty_calibration:
    spearman_rho: TBD                  # per-pixel UQ vs. per-pixel error
```

---

## 5-tuple credentials (per L2 spec)

The reference method is certified for at least three clinical tasks. Filled at submission:

```yaml
dose_equivalence_credentials:
  - dose_ratio: 0.25
    task: lung_nodule_5mm_detection
    epsilon: 0.02
    alpha: 0.05
    subpopulation: adult_chest_pwm_l3_test
    verdict: TBD
    confidence_interval: TBD
  - dose_ratio: 0.25
    task: liver_lesion_segmentation_dice
    epsilon: 0.03
    alpha: 0.05
    subpopulation: adult_abdomen_pwm_l3_test
    verdict: TBD
    confidence_interval: TBD
  - dose_ratio: 0.10
    task: lung_nodule_5mm_detection
    epsilon: 0.05
    alpha: 0.05
    subpopulation: adult_chest_pwm_l3_test
    verdict: TBD
    confidence_interval: TBD
```

---

## Registry payload (draft)

```yaml
pwm_l4_cert:
  name: pwm_reference_reconstruction_method
  version: 1.0.0
  l3_spec_ref: pwm_l3_spec:pwm_low_dose_ct_benchmark:1.0.0
  l2_spec_ref: pwm_l2_spec:dose_equivalence_v1:0.1.0
  paper:
    arxiv: TBD
    venue: TBD              # miccai or ieee_tmi
    doi: TBD
  runbundle_cid: ipfs://TBD
  runbundle_docker_image: TBD@sha256:TBD
  trained_weights_cid: ipfs://TBD
  results_hash: sha256:TBD
  license: apache_2_0
  authors:
    - TBD                    # filled at submission per contributions
  content_hash: sha256:TBD
```

---

## Why this cert matters beyond the paper

**This is the first L4 cert against the L3 benchmark.** Future community submissions reproduce this pattern. If the cert is sloppy (missing seeds, ambiguous evaluation protocol, irreproducible RunBundle), every community submission inherits the sloppiness. Cleanliness here scales.

When a Track 7 agent asks PWM *"what is the current SOTA low-dose CT method?"* and gets back this cert plus the leaderboard top entry, the protocol's flagship sentence becomes literally true.

---

## Pending work (gate to certification)

- [ ] WS-3 reference method v1 trained and evaluated on full L3 benchmark.
- [ ] Deep ensemble (5 models) trained; UQ calibration validated.
- [ ] Cross-vendor experiment complete (train on Siemens, test on GE, etc.).
- [ ] RunBundle published to IPFS with stable CID.
- [ ] 5-tuple credentials computed for ≥ 3 clinical tasks per L2 spec.
- [ ] Method paper submitted to MICCAI or *IEEE TMI*.
- [ ] L2 spec ([`l2_spec.md`](l2_spec.md)) and L3 spec ([`l3_spec.md`](l3_spec.md)) registered first.

---

## Cross-references

- Reference method workstream: [`../WS-3_reference_method/README.md`](../WS-3_reference_method/README.md)
- L2 spec (framework): [`l2_spec.md`](l2_spec.md)
- L3 spec (benchmark): [`l3_spec.md`](l3_spec.md)
- Agent query examples: [`agent_query_examples.md`](agent_query_examples.md)
