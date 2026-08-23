# Cover letter — *Scientific Data* submission

Paste-ready; fill **[CONFIRM]** (corresponding author, affiliation, DOIs) before sending.

---

[CONFIRM date]

To the Editors, *Scientific Data*

**Re: Submission of a Data Descriptor — "PWM-LDCT v0.5: A Content-Addressed Harmonization of the
LIDC-IDRI Low-Dose CT Dataset with Simulated Reduced-Dose Records for Reproducible Reconstruction Benchmarking"**

Dear Editors,

We are pleased to submit the above Data Descriptor for consideration in *Scientific Data*. Low-dose
CT (LDCT) reconstruction research is anchored on public datasets — above all LIDC-IDRI, the most
widely used public thoracic CT collection — yet they are distributed in incompatible formats, carry
heterogeneous (or absent) annotations, and have no shared, frozen version identifier. The result is
per-paper re-implementation of preprocessing, unreliable cross-paper comparisons, and benchmark
drift. Our descriptor addresses this by releasing v0.5, a unified, content-addressed harmonization
of the LIDC-IDRI source together with new, openly-licensed value-added data records. The AAPM 2016
Low-Dose CT Grand Challenge and Mayo LDCT-and-Projection-Data collections are planned additions on
the v1.0 roadmap under the same schema.

**What the release contributes for reuse.** Beyond a common schema and a pip-installable loader, the
deposit provides genuinely new data records that are independently reusable: harmonized multi-task
annotations for LIDC (majority-vote lung-nodule labels consolidated from the four-radiologist LIDC
annotations, per-reader raw labels preserved for uncertainty-aware work), physically-derived
simulated low-dose images for the full-dose-only LIDC scans (dose ratios 0.10/0.25/0.50),
harmonized per-scan metadata, and deterministic patient-level splits (train 589 / val 216 /
test 205 of 1,010 patients). The entire release is identified by a SHA-256 content hash, so any
result citing it refers to bit-identical content. The LIDC cohort spans four manufacturers (GE,
Siemens, Philips, Toshiba), so the release already supports genuine cross-vendor evaluation that no
prior single public LDCT dataset enabled at this scale.

**Fit with *Scientific Data*.** The descriptor is designed for reuse and reproducibility: it is
technically validated (harmonization consistency, annotation-reuse fidelity against the published
LIDC reference, inter-rater agreement over the inherited four-radiologist annotations, and baseline
reproductions), the analysis and preprocessing code is open-source and version-pinned, and the
value-added records are deposited in an approved repository — PhysioNet (DOI [CONFIRM]), mirrored
to Zenodo (DOI [CONFIRM]) — under CC BY 4.0 (code Apache-2.0). The underlying DICOM scans are not
redistributed; users obtain them from their original repository and regenerate bit-identical
artifacts locally, in compliance with the source's data-use terms.

**Scope, stated plainly.** This is a public-data-only v0.5 release (LIDC-IDRI). The reduced-dose
records are simulated via a physically-grounded projection-domain forward model (not a re-acquired
scan), and no real paired-dose data are included; the AAPM/Mayo real paired-dose sources are planned
for the v1.0 roadmap. A prospective, multi-site, additional-vendor extension is planned as a
separate companion descriptor.

**Declarations.** This manuscript is original, is not under consideration elsewhere, and all authors
have approved the submission. No new data were collected; the source dataset is de-identified to
HIPAA Safe Harbor by its original team, and the annotation activity (planned top-up in v1.0)
received a UTSW non-human-subjects-research / exempt determination. Competing interests (including
an authorial affiliation with the PWM Protocol Foundation) are disclosed in the manuscript; the
dataset is fully usable and verifiable independent of any Foundation infrastructure. A completed
Nature Portfolio Reporting Summary accompanies this submission.

We believe PWM-LDCT v0.5 will be a durable, citable substrate for the LDCT reconstruction community
and a strong fit for *Scientific Data*. We thank you for considering it.

Sincerely,

[CONFIRM corresponding author name], on behalf of all authors
[CONFIRM affiliation] · [CONFIRM email] · [CONFIRM ORCID]
