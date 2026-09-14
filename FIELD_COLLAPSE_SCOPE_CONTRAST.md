# Contrast phase: an undeclared boundary of the field this program proposes to collapse

_Written 2026-09-14 against `646daa6c3a01ab807dc729982115c57bdec3ff3a`; cited sections re-verified against `e9985a7` after the outcome-requirements revision landed · companions: [what the field needs solved](FIELD_COLLAPSE_PROBLEMS.md), [acceptance](FIELD_COLLAPSE_ACCEPTANCE.md), [implementation audit](FIELD_COLLAPSE_IMPLEMENTATION_AUDIT_2026-09-14.md)_

This note raises one scoping question and proposes one cheap corpus change. It changes no scoring rule, tolerance, dataset, release permission or owner decision, and it declares no experimental problem solved. It reports checks run against the revision above; it generates no images, predictions or reader results.

[`FIELD_COLLAPSE_PROBLEMS.md`](FIELD_COLLAPSE_PROBLEMS.md) asks whether closing its problems would be sufficient for domain collapse and answers no, then adds four obligations — §8 to §11 — the last of which is demonstrated external decision value. **This note argues that one term is missing from the scope those obligations are stated over: whether the field being collapsed includes contrast-enhanced CT.** At present the corpus cannot answer that question about its own scans, which makes the boundary neither included nor excluded but unrecorded.

## 1. Dose and contrast do not separate, so the boundary is not cosmetic

Two reasons the answer changes depending on which side of the boundary a scan sits.

**Acquisition.** In contrast-enhanced CT the operating point is a three-way trade between radiation dose, tube voltage and iodine load. Lowering kVp moves the beam spectrum toward iodine's K-edge at about 33.2 keV, raising enhancement per unit iodine, which is conventionally spent on either less iodine or less dose. A dose-reduction frontier measured on unenhanced scans is therefore measured at a different operating point from the enhanced one, not merely on a different cohort. §9's "dose–task operating frontier" inherits this: a frontier is a claim about an operating point, and phase is one of its coordinates.

**The task.** The committed task is an SKE Gaussian lesion at 20 HU peak contrast inserted into a noise ROI band of [10, 120] HU ([`task_spec.py`](WS-4_leaderboard/scoring/task_spec.py)). That band selects physically different tissue depending on phase: unenhanced soft tissue sits near 40–60 HU, whereas enhanced liver parenchyma in the portal-venous phase sits near the top of the band, with vessels above it. The clinical detection problem also changes shape — a hypodense lesion against enhanced parenchyma, or an enhancing rim, is an edge-preservation problem at a different spatial frequency than a low-contrast blob in uniform tissue.

Neither point is a measured failure of the current methods. Both are reasons that a result obtained on one side of the boundary is not evidence about the other, which is the same logic §3 already applies to cohort, vendor and dose-generation method.

## 2. The phase is currently unknown, not excluded

**Status: the corpus does not record contrast administration; the affected comparison is already committed.**

Three checks against `646daa6`, offline and read-only:

```bash
# 1. Any contrast vocabulary anywhere in the repository. Excludes the task
#    spec's own unrelated uses (peak_contrast, low-contrast, contrast_hu).
grep -rniE "contrast[- ]enhanc|iodine|iodinated|portal venous|non-contrast|contrast agent|contrast bolus" \
  --include=*.md --include=*.py --include=*.json --include=*.tex .   # -> 0 matches

# 2. Contrast administration recorded at ingestion.
grep -c "0018,0010\|ContrastBolus" WS-1_dataset/schema/dicom_to_hdf5_mapping.md   # -> 0
```

The third is a reading, not a command: [`WS-1_dataset/README.md`](WS-1_dataset/README.md) line 31 declares anatomy as "Chest (lung-screening primary; LIDC)" against "Chest + abdomen at multi-site scale (AAPM/Mayo oncology + prospective)".

The [DICOM-to-HDF5 mapping](WS-1_dataset/schema/dicom_to_hdf5_mapping.md) carries KVP (0018,0060), exposure (0018,1152/1151/1150), ConvolutionKernel (0018,1210), Manufacturer and Model (0008,0070/1090) and pitch. It does not carry **ContrastBolusAgent (0018,0010)**, ContrastBolusStartTime (0018,0012) or ContrastBolusRoute (0018,1040). So no released record states whether a given scan was enhanced, and no downstream analysis can stratify on it.

**Why this reaches a committed result.** §3 observes that the cross-group comparison "mixes cohort, vendor, protocol and dose-generation method" and therefore does not isolate a vendor effect. The groups are four LIDC vendors at two patients each plus AAPM-Siemens at four ([`cross-vendor summary`](WS-1_dataset/output/aapm_lidc_cross_vendor_spread_summary.md)). LIDC is lung-screening chest, which is unenhanced by protocol; the AAPM arm is 1 mm B30, a soft-tissue body kernel, and the repository's own anatomy row places AAPM/Mayo in oncology. Whether those scans were enhanced is exactly what is not recorded.

**Contrast phase is therefore a fifth term in §3's list, and the only one that cannot currently be named.** The four LIDC vendor groups are internally consistent in phase whatever it is; the LIDC-versus-AAPM contrast is where the term would act. This note does not assert that the AAPM scans are enhanced, does not quantify any effect, and does not revise any reported number. It reports that the question cannot be answered from the corpus.

## 3. The one-field fix

Map **(0018,0010) ContrastBolusAgent** into the acquisition block at ingestion, beside `acquisition.kvp` and `acquisition.recon_kernel`, with ContrastBolusStartTime and ContrastBolusRoute if they are present. Record it verbatim and record absence as absence rather than as "none", because an empty tag is not proof of an unenhanced acquisition.

This is a corpus-provenance change on the machine that holds the DICOM, not an analysis change. It cannot be done by the [`ldct_agent`](https://github.com/integritynoble/ldct_agent) verifier, which holds no data roots and refuses DICOM by suffix precisely because headers carry identifiers. The tag is an acquisition parameter and carries no patient identifier itself; the existing [DICOM cleaning spec](WS-1_dataset/schema/dicom_cleaning_spec.md) governs what else may travel with it.

Once recorded, the phase becomes available as a declared stratum, and the question of whether the LIDC and AAPM arms differ in it becomes answerable rather than open.

## 4. Two routes, and what each obliges

Both are defensible. What is not defensible is the present state, in which the boundary is undeclared and the corpus cannot locate it.

**(a) Narrow the declared field.** State that the program addresses *unenhanced* low-dose CT detectability, list contrast-enhanced CT among the things the project cannot claim — the same discipline [`data_needs.md`](WS-1_dataset/data_needs.md) already applies to sinogram scale, prospective acquisition and ≥500-patient cohorts — and carry the limitation into §9's frontier and §11's decision-value claim. Cost: one declaration, plus the ingestion field above to confirm the corpus matches the declaration.

**(b) Keep the broad field.** Then phase becomes a declared factor: recorded at ingestion, stratified alongside vendor and dose wherever §3's no-averaging policy applies, carried into any declared comparison family, and reported in the operating frontier per phase as well as per vendor. Any reader study would have to declare phase too, since reading enhanced and unenhanced studies are different tasks. Cost: enhanced paired-dose data the project does not hold, which places this on the same footing as the other acquisitions §4 says it cannot currently obtain.

Route (a) is the cheaper and, on present evidence, the accurate one. It is also the route that keeps the collapse claim true rather than merely large.

## 5. Why this bears on collapse specifically

The distinction worth preserving is between a field that closes because everything checkable has been checked and one that closes because nobody acts on the result. They are hard to tell apart from inside, and only whether anyone acts separates them.

If the clinical majority of body CT at the dose levels in question is contrast-enhanced, and the defensible operating point this program produces comes from unenhanced screening data, then the output of §9 and §11 is a document that does not answer the protocol question a medical physicist is asking. That is the second kind of closure wearing the first kind's clothes. Declaring the boundary — either route — is what keeps the two distinguishable.

**Evidence needed to close this gap:** the acquisition field recorded for every released scan, a declared field boundary consistent with what that field shows, and, under route (b) only, independent enhanced paired-dose evidence with phase-stratified results.

## Verification record

Checked on 2026-09-14 at `646daa6`: the three greps in §2, run against the working tree; §3's quoted mixed-factor sentence, §9 and §11 re-read at `e9985a7` and unchanged there; the DICOM tag list read from [`dicom_to_hdf5_mapping.md`](WS-1_dataset/schema/dicom_to_hdf5_mapping.md); the group composition and anatomy row read from the [cross-vendor summary](WS-1_dataset/output/aapm_lidc_cross_vendor_spread_summary.md) and [`WS-1_dataset/README.md`](WS-1_dataset/README.md). No image, prediction, reconstruction or reader result was generated, no scoring or publication service was exercised, and no DICOM header was opened — the absence reported in §2 is an absence in the schema, not an inspection of patient data. The physics in §1 is textbook background, not a measurement made here, and the clinical-majority premise in §5 is stated as a conditional because this repository holds no evidence for or against it.
