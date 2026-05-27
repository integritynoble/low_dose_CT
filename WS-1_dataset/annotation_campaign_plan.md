# PWM-LDCT v0.5 — radiologist annotation campaign plan

Operational plan for producing the v0.5 annotation records. The **methodology** (eligibility,
calibration thresholds, majority-vote rules, drift monitoring, discordance adjudication, κ metrics,
JSON formats) is defined normatively in [`schema/annotation_qa_protocol.md`](schema/annotation_qa_protocol.md);
this document is the *who / what / how much / when / budget / logistics* layer. Values in
**[CONFIRM]** are decisions to finalize before kickoff.

---

## 1. Scope — what is new vs reused
| Task | Cohort | Count | Effort |
|---|---|---|---|
| **Lung-nodule detection (reuse)** | LIDC-IDRI | 1,018 | **No campaign** — convert existing 4-radiologist XML (`pipelines/pwm_ldct_prep/lidc_annotations.py`; see `../data_acquisition/lidc_xml_acquisition.md`) |
| **Lung-nodule top-up (new)** | Mayo **chest** | **99** | ≥2 readers/case, LIDC protocol (bbox + diameter + texture + location) |
| **Diagnostic-quality Likert (new)** | AAPM + Mayo paired-dose | **~209** (199 Mayo + 10 AAPM, minus overlap) | per scan × reconstruction (FBP / vendor-IR where present / TV) × dose level |
| Calibration set | held-out LIDC | 20 | onboarding + rotating drift checks |

**Out of v0.5 scope (deferred to v1.0):** abdominal **liver-lesion segmentation** (AAPM 2016 and
Mayo abdomen). AAPM 2016 is an abdominal cohort, so it contributes to Likert but **not** to the
lung-nodule top-up.

## 2. Panel
- **≥ 2 board-certified radiologists**, ≥ 5 y thoracic-CT experience, for the nodule top-up + Likert.
- **1 additional independent radiologist** for discordance adjudication.
- **[CONFIRM]** named readers, institution, and that each passes the 20-case calibration gate
  (Cohen's κ ≥ **[CONFIRM: 0.60]**, per the QA protocol) before contributing release annotations.

## 3. Tooling & data handling
- Annotation platform with DICOM bounding-box + characteristics support — **[CONFIRM]** (e.g. MD.ai,
  3D Slicer, OHIF + bbox, or in-house), exporting to the **`raw_per_reader` JSON schema**
  (annotation_qa_protocol §7) so outputs drop straight into `annotations/raw_per_reader/{pid}/{reader}.json`
  and `annotations/likert/{series}.json`.
- Readers view the **harmonized, de-identified** images (already HIPAA Safe Harbor + re-verified).
  No patient contact, no new PHI → covered by the UTSW non-human-subjects/exempt determination
  (**[CONFIRM] IRB no.**).

## 4. Workflow (maps to the QA protocol stages)
1. **Onboarding / calibration** — each reader annotates the 20-case held-out LIDC set; gate on κ.
2. **Lung-nodule top-up** — 99 Mayo chest scans, ≥2 readers each, full LIDC nodule protocol.
3. **Discordance adjudication** — referred cases (non-overlapping boxes / diameter ≥1.5× / texture
   class disagreement) go to the 3rd reader; raw per-reader labels preserved.
4. **Likert scoring** — ~209 paired-dose scans scored per reconstruction × dose level.
5. **Drift monitoring** — rotating 5-case recalibration every ~50 cases (~monthly); pause + recal +
   re-annotate the affected window if κ drops.

## 5. Timeline (~6–8 weeks, parallelizable)
| Week | Activity |
|---|---|
| 1 | Platform setup + reader onboarding/calibration (20 cases) |
| 2–5 | Nodule top-up (99 chest) + Likert (~209) in parallel; rolling drift checks |
| 4–6 | Discordance adjudication (rolling) |
| 6–7 | Consolidation (`consolidate_readers`), QA audit, fidelity check vs published LIDC |
| 7–8 | Freeze, package into the release tree, hash into `manifest.sha256` |

## 6. Budget (rough; **[CONFIRM]** honoraria rate)
At ~radiologist honorarium **[CONFIRM: ~$200/hr]**:
- Calibration: 20 × 3 readers × ~5 min ≈ 5 reader-h
- Nodule top-up: 99 × 2 readers × ~5 min ≈ 16.5 reader-h + adjudication (~10% discordant) ≈ 2 h
- Likert: ~209 × ~6 score-sets × ~1 min ≈ 21 reader-h
- ≈ **45–60 reader-hours → ~$9K–$12K** (within the $5K–$15K v0.5 estimate in `data_needs.md`; far
  below v1.0's full-collection budget, because LIDC is reused not re-collected).

## 7. Deliverables → pipeline
The campaign emits `raw_per_reader/{pid}/{reader}.json` + `likert/{series}.json`. The pipeline then
produces the consolidated records (`annotations/lidc_majority_vote/`, `topup_mayo/`, `likert/`) via
`consolidate_readers` (IoU match + majority vote), and the manuscript's **inter-rater reliability**
(`tab:irr_v05`, κ values) and **annotation-reuse fidelity** validations. These κ values also fill the
QA-protocol/manuscript `[CONFIRM]`/`\todo{κ threshold}` placeholders.

## 8. Risks & mitigations
- **Reader availability / throughput** → 2-reader minimum + rolling schedule; start calibration early.
- **κ below gate** → exclude/recalibrate per protocol; recruit a backup reader.
- **Scope creep** → abdomen liver-lesion segmentation is explicitly v1.0; hold the line.
- **Platform export mismatch** → validate the exporter against the §7 JSON schema on the 20-case set
  before the main campaign.

## [CONFIRM] before kickoff
Named readers + institution · annotation platform · honorarium rate/budget approval · IRB
determination no. · κ threshold (must match `annotation_qa_protocol.md` and the manuscript).
