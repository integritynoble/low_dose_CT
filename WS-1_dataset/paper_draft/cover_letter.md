# Cover letter — *Scientific Data* submission

Paste-ready; fill **[CONFIRM]** (corresponding author, affiliation, DOIs) before sending.

---

[CONFIRM date]

To the Editors, *Scientific Data*

**Re: Submission of a Data Descriptor — "PWM-LDCT v0.5: A Content-Addressed, Multi-Task
Harmonization of Three Public Low-Dose CT Datasets for Reproducible Reconstruction Benchmarking"**

Dear Editors,

We are pleased to submit the above Data Descriptor for consideration in *Scientific Data*. Low-dose
CT (LDCT) reconstruction research is anchored on three public datasets — LIDC-IDRI, the 2016
AAPM-Mayo Low-Dose CT Grand Challenge, and the Mayo LDCT-and-Projection-Data collection — yet they
are distributed in incompatible formats, carry heterogeneous (or absent) annotations, and have no
shared, frozen version identifier. The result is per-paper re-implementation of preprocessing,
unreliable cross-paper comparisons, and benchmark drift. Our descriptor addresses this by releasing
a unified, content-addressed harmonization of these sources together with new, openly-licensed
value-added data records.

**What the release contributes for reuse.** Beyond a common schema and a pip-installable loader, the
deposit provides genuinely new data records that are independently reusable: harmonized multi-task
annotations across all three sources (majority-vote lung-nodule labels consolidated from the
four-radiologist LIDC annotations and topped up by board-certified radiologists on the AAPM and Mayo
cases, per-scan diagnostic-quality Likert scores, and the raw per-reader labels for
uncertainty-aware work), physically-derived simulated low-dose images for the full-dose-only LIDC
scans, harmonized per-scan metadata, and deterministic patient-level splits. The entire release is
identified by a SHA-256 content hash, so any result citing it refers to bit-identical content.
Notably, the public Mayo cohort spans two manufacturers (approximately half GE and half Siemens),
so the release supports genuine cross-vendor (GE↔Siemens) paired-dose evaluation that no prior
single public LDCT dataset enabled.

**Fit with *Scientific Data*.** The descriptor is designed for reuse and reproducibility: it is
technically validated (cross-source harmonization consistency, annotation-reuse fidelity against
the published LIDC reference, inter-rater agreement, simulation-vs-reference comparison, and
baseline reproductions), the analysis and preprocessing code is open-source and version-pinned, and
the value-added records are deposited in an approved repository — PhysioNet (DOI [CONFIRM]), mirrored
to Zenodo (DOI [CONFIRM]) — under CC BY 4.0 (code Apache-2.0). The underlying DICOM scans are not
redistributed; users obtain them from their original repositories and regenerate bit-identical
artifacts locally, in compliance with each source's data-use terms.

**Scope, stated plainly.** This is a public-data-only v0.5 release. We are explicit throughout that
the AAPM/Mayo reduced-dose data is produced by validated projection-domain noise insertion (not a
re-acquired scan), that vendor coverage is two-vendor (GE + Siemens; not Canon/Philips), and that
the head subjects are credentialed-access and out of scope. A prospective, multi-site, additional-
vendor extension (v1.0) is planned as a separate descriptor.

**Declarations.** This manuscript is original, is not under consideration elsewhere, and all authors
have approved the submission. No new data were collected; the source datasets are de-identified to
HIPAA Safe Harbor by their original teams, and the radiologist annotation activity received a UTSW
non-human-subjects-research / exempt determination. Competing interests (including an authorial
affiliation with the PWM Protocol Foundation) are disclosed in the manuscript; the dataset is fully
usable and verifiable independent of any Foundation infrastructure. A completed Nature Portfolio
Reporting Summary accompanies this submission.

We believe PWM-LDCT v0.5 will be a durable, citable substrate for the LDCT reconstruction community
and a strong fit for *Scientific Data*. We thank you for considering it.

Sincerely,

[CONFIRM corresponding author name], on behalf of all authors
[CONFIRM affiliation] · [CONFIRM email] · [CONFIRM ORCID]
