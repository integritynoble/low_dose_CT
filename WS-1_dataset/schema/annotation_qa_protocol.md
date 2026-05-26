# PWM-LDCT v0.5 — Annotation QA protocol

Normative protocol for the v0.5 annotation campaign and its quality-assurance loop, referenced by
the manuscript's *Methods → Annotation harmonization* (the paragraphs on annotator training,
the ongoing QA loop, discordance adjudication, and calibration provenance) and *Technical
Validation → Inter-rater annotation reliability*.

- **Schema version:** `0.5.0`. Companion: [`dataset_schema.md`](dataset_schema.md) §6.
- Pre-registered thresholds are marked **[CONFIRM]**; they must equal the manuscript's `\todo{}`
  values at submission.

---

## 1. Tasks and label definitions

| Task | Scope | Label content | Scale |
|---|---|---|---|
| **Lung-nodule detection** | chest scans (all sources) | per-nodule `bbox_xyxy`, `diameter_mm`, `texture`, `location` | LIDC nodule protocol |
| **Diagnostic-quality Likert** | AAPM + Mayo paired-dose scans | per (reconstruction × dose level) confidence score | 1–5 |

The nodule task **reuses** LIDC-IDRI's existing four-radiologist annotations (consolidated, §3) and
**tops up** the AAPM and Mayo chest cases that lack equivalent labels, following the *same* LIDC
protocol so the harmonized convention is uniform across sources.

---

## 2. Annotator eligibility & onboarding

- **Eligibility:** board-certified radiologist, ≥ 5 years post-residency thoracic CT experience.
- **Calibration onboarding (required before any release annotation):** each reader annotates a
  fixed **20-case** set drawn from a held-out LIDC-IDRI subset that is **excluded from the release**.
  The reader's labels are scored against the LIDC majority-vote ground truth (§5).
- **Pass criterion:** calibration-set agreement **Cohen's κ ≥ [CONFIRM: 0.60]** (substantial).
  Readers below threshold are excluded and do not contribute.
- The held-out calibration cases never enter `train/val/test` (enforced by `splits/` and checked by
  `pwm_ldct_loader.validate`).

---

## 3. Majority-vote consolidation (nodule task)

1. **Nodule matching across readers.** Two readers' nodules are the same physical nodule iff their
   bounding boxes overlap with **IoU ≥ [CONFIRM: 0.3]** on the same slice (3-D adjacency across ±1
   slice allowed). Matched sets form a candidate nodule.
2. **Inclusion (majority).** A candidate nodule is included in the ground truth iff **> 50 %** of
   the qualified readers for that case marked it (for LIDC, ≥ 3 of 4; for top-up, both of 2 — see §4
   for ties).
3. **Attribute consolidation.** `bbox_xyxy` = element-wise median of contributing boxes;
   `diameter_mm` = median; `texture` = median of the ordinal texture scores; `location` = mode.
4. **Provenance.** Each consolidated nodule records `ground_truth: "majority_vote"` and the
   `calibration_window` (§6) under which its contributing labels were produced.

---

## 4. Ongoing QA loop

Mirrors the three mechanisms in the manuscript:

### 4.1 Drift monitoring
- Every reader re-annotates a **rotating 5-case calibration subset** every **~50 cases**
  (≈ monthly cadence).
- A running κ against the calibration majority-vote is tracked. If it drops **below [CONFIRM: 0.60]**,
  the reader is **paused and re-calibrated**.
- **All cases annotated since that reader's last passing calibration window are re-annotated by an
  alternate qualified reader** and the affected ground truth is recomputed.

### 4.2 Discordance adjudication (top-up, 2-reader cases)
A case is **discordant** if any of:
- non-overlapping bounding boxes (a nodule marked by one reader, IoU `< [CONFIRM: 0.3]` with any of
  the other's), **or**
- **diameter disagreement ≥ 1.5×** (ratio of larger to smaller), **or**
- **texture-class disagreement** (different ordinal texture bin).

Discordant cases are referred to a **third independent radiologist**, whose label becomes the
released ground truth (`ground_truth: "adjudicated"`). The two original readers' raw labels are
**preserved** in `annotations/raw_per_reader/` for uncertainty-aware methods.

### 4.3 Calibration provenance
- Every released annotation carries the `calibration_window` identifier under which it was produced
  (§6).
- If a post-hoc audit **invalidates** a calibration window, **only the scans annotated in that
  window** are flagged for re-annotation in the next **PATCH** release (manuscript *Errata* policy);
  unaffected scans are untouched and their content hashes are unchanged.

---

## 5. Inter-rater reliability metrics (reported in the manuscript)

- **Detection κ:** Cohen's κ computed on per-candidate-nodule presence/absence after IoU matching
  (§3.1), pairwise between readers and between each reader and the majority vote.
- **Texture κ:** linearly-weighted Cohen's κ on the 1–5 ordinal texture score over matched nodules.
- **Likert agreement:** intraclass correlation coefficient (ICC(2,k)) across readers per
  (reconstruction × dose level).
- Reported per LIDC reader pair and for each top-up reader vs the LIDC calibration majority vote
  (manuscript Table *Inter-rater annotation reliability*). Calibration-set κ values are also the
  pass/fail gate of §2.

---

## 6. Calibration windows

A **calibration window** is the span between two consecutive passing calibration checkpoints for a
reader. Identifier format: `cw-{reader_id}-{NNN}` (monotonic per reader). Each window stores its
open/close timestamps, the calibration κ that opened it, and the set of `scan_uid`s annotated within
it. Windows are recorded in `annotations/calibration_windows.json` and hashed into
`manifest.sha256`, so the provenance of every label is frozen and auditable.

---

## 7. Annotation file formats

### 7.1 Consolidated nodules — `annotations/{lidc_majority_vote,topup_aapm,topup_mayo}/{patient_id}.json`
```jsonc
{
  "patient_id": "string",
  "series_id": "string",
  "source": "lidc|aapm|mayo",
  "nodules": [
    {
      "nodule_id": "string",
      "slice_index": 0,                 // Z index in recon/*  (a nodule may span ±1 slice)
      "bbox_xyxy": [x0, y0, x1, y1],     // pixels in the slice [H,W] frame
      "diameter_mm": 0.0,
      "texture": 3,                      // 1–5 (LIDC texture scale)
      "location": "string",
      "ground_truth": "majority_vote|adjudicated",
      "n_contributing_readers": 0,
      "calibration_window": ["cw-r1-004", "cw-r2-002"]
    }
  ]
}
```

### 7.2 Per-reader raw — `annotations/raw_per_reader/{patient_id}/{reader_id}.json`
Same `nodules` shape as §7.1 **minus** `ground_truth`/`n_contributing_readers`, **plus**
`reader_id` and the reader's per-nodule `confidence` (1–5). These are the pre-consolidation labels.

### 7.3 Likert — `annotations/likert/{series_id}.json`
```jsonc
{
  "series_id": "string",
  "scores": [
    {"reconstruction": "fbp|ir|tv", "dose_ratio": 0.25, "scores_per_reader": [4, 3], "consensus": 4}
  ],
  "n_readers": 2
}
```
`reconstruction: "ir"` (vendor iterative) is present only where the source provides it; full-dose-only
LIDC scans receive a single full-dose Likert at `dose_ratio: 1.0`, `reconstruction: "fbp"`.

---

## 8. Reproducibility & release gate

- Consolidation (§3), matching thresholds, and metrics (§5) are implemented in
  `pwm_ldct_loader.annotations` and run deterministically from the raw-per-reader files; the
  consolidated outputs are therefore regenerable from the deposited raw labels.
- A scan's nodule/Likert annotations enter the release only when (a) every contributing reader's
  governing calibration window is in `pass` state and (b) all discordances are adjudicated. The
  audit of these gates is published as Supplementary Material alongside the inter-rater table.
