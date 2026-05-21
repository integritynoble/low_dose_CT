# L3 Spec — PWM Low-Dose CT Benchmark

**Status:** ⏳ Draft pending dataset construction (WS-1).
**Target on-chain date:** D9 + 365.
**Backing paper:** [`../WS-1_dataset/paper_draft/`](../WS-1_dataset/) (target venue: *Nature Scientific Data*).
**Workstream:** WS-1.

---

## Benchmark scope

The L3 spec certifies that a dataset and scoring protocol meet the **PWM Low-Dose CT Benchmark** standard. A submission earns a leaderboard entry only by being evaluated against an L3-certified version of the benchmark.

---

## Inclusion criteria (mandatory)

| Item | Requirement |
|---|---|
| Patient scans, paired (normal + matched low-dose) | ≥ 500 |
| Real low-dose pairs (not just simulated) | ≥ 50 patients |
| Vendor coverage | ≥ 2 of {Siemens, GE, Canon, Philips} |
| Anatomy | Chest (lung-screening) primary; abdomen secondary |
| Sites | ≥ 2 (UTSW + ≥ 1 partner) |
| Annotation | ≥ 2 board-certified radiologists per case; majority-vote ground truth |
| Format | DICOM raw projections + reconstructed images + metadata |
| HIPAA compliance | Safe Harbor or Expert Determination |
| Distribution | PhysioNet credentialed access |
| Patient-level split | 60/20/20 train/val/test; no patient in two splits |

---

## Scoring protocol

Per-method evaluation produces a `results.json` matching the `baselines/comparison/` output schema. Metrics:

| Metric | Definition | Reported with |
|---|---|---|
| PSNR | Peak signal-to-noise ratio (HU values) | 95% bootstrap CI, N = 1,000 |
| SSIM | Structural similarity index | 95% bootstrap CI, N = 1,000 |
| LPIPS | Learned perceptual image patch similarity | 95% bootstrap CI, N = 1,000 |
| task_AUC | AUC of a fixed downstream task (lung nodule detection ≥ 5mm) | 95% bootstrap CI, N = 1,000 |
| inference_seconds_per_slice | Wall-clock inference time | Mean over test set |
| gpu_memory_gb | Peak GPU memory during inference | Single-precision measurement |

Dose levels evaluated: 10%, 25%, 50%, 100%.

A 5-tuple credential per the **L2 spec** ([`l2_spec.md`](l2_spec.md)) is required for at least one clinical task.

---

## Submission contract (for community leaderboard)

Submissions are PWM RunBundles containing:

```
runbundle/
├── method.json              # name, version, paper, license
├── Dockerfile               # pinned reproduction environment
├── eval.py                  # entry point: docker run ... eval --dataset X --out Y
├── results.json             # produced by eval against the L3 benchmark
├── dose_equivalence_credentials.json   # per L2 spec
└── checkpoint/              # or pointer to HF / IPFS
```

The scoring service (`leaderboard/scoring/`) executes the RunBundle in a sandboxed container, verifies the published `results.json` matches the live execution, and posts the verified score to the leaderboard.

---

## Reference baselines

The benchmark is launched with **four** seed entries:
- `baselines/red_cnn/` — RED-CNN (Chen et al. 2017)
- `baselines/transformer/` — Phase 1-selected transformer SOTA
- `baselines/diffusion/` — Phase 1-selected diffusion SOTA
- `reference_method/v1/` — PWM reference method (Track 9 9c)

---

## Versioning

The L3 spec is versioned. **v1.0.0** is the launch version (D9 + 365 target). Subsequent versions extend (more patients, more vendors, pediatric subset, etc.) without breaking backwards compatibility of v1 results.

---

## Registry payload (draft)

```yaml
pwm_l3_spec:
  name: pwm_low_dose_ct_benchmark
  version: 1.0.0
  dataset_paper:
    arxiv: TBD
    venue: nature_scientific_data
    doi: TBD
  dataset_distribution:
    physionet_uri: TBD
    ipfs_cid: TBD
    license: physionet_credentialed_v1
  patient_count: TBD            # ≥ 500
  vendor_set: [TBD]              # ≥ 2 of {siemens, ge, canon, philips}
  site_set: [utsw, TBD]
  scoring:
    metrics: [PSNR, SSIM, LPIPS, task_AUC]
    bootstrap_n: 1000
    dose_levels: [0.10, 0.25, 0.50, 1.00]
    task: lung_nodule_5mm_detection
  reference_baselines:
    - red_cnn_v1
    - transformer_v1
    - diffusion_v1
    - pwm_reference_method_v1
  l2_spec_ref: pwm_l2_spec:dose_equivalence_v1
  content_hash: sha256:TBD
```

---

## Pending work (gate to registration)

- [ ] WS-1 dataset construction complete (≥ 500 paired scans, ≥ 2 vendors, ≥ 2 sites).
- [ ] PhysioNet listing live.
- [ ] *Nature Scientific Data* paper submitted (acceptance not required to register, but required for v1.0.0).
- [ ] L2 spec ([`l2_spec.md`](l2_spec.md)) registered first or concurrently.
- [ ] Four reference baselines have valid `results.json` under this scoring protocol.

---

## Cross-references

- Dataset workstream: [`../WS-1_dataset/README.md`](../WS-1_dataset/README.md)
