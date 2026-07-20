# Cover letter — *Scientific Data* Data Descriptor submission

> Draft template. Fill every `TODO` at submission. Keep this short (≤ 1 page);
> the editor screens on scope, non-redundancy, and repository/DOI compliance —
> address those three explicitly.

---

**To:** The Editors, *Scientific Data* (Nature Portfolio)

**Re:** Submission of a Data Descriptor — *"A Multi-Vendor Corpus of Reference
Low-Dose CT Reconstructions with Calibrated Per-Pixel Uncertainty and
Signal-Equivalence Credentials"*

Dear Editors,

We submit the enclosed Data Descriptor for consideration in *Scientific Data*.

**What the dataset is.** We describe a deposited, reusable **derived-data
corpus** built on the multi-vendor PWM-LDCT benchmark. For every held-out test
scan, at three reduced-dose levels (10%, 25%, 50%) and across multiple CT
vendors, the corpus releases: a reference reconstruction, a per-pixel ensemble
**uncertainty** map, the paired per-pixel **error** map against the full-dose
reference, a downstream lung-nodule **task-score** map, and a machine-readable
**signal-equivalence credential** — plus matched reconstructions of five
baseline methods. Every record is content-addressed and regenerable
bit-for-bit (within floating-point tolerance) from a pinned, Apache-2.0 Docker
RunBundle.

**Why it fits *Scientific Data*.** The reviewed object is the **data**, not an
algorithm: the reconstruction pipeline is described only as data provenance
(Methods). The contribution is the derived layer the low-dose CT field
currently lacks — reconstructed volumes, per-pixel uncertainty, paired error,
task outputs, and equivalence certificates that a third party can download and
reuse without retraining any model. The paired (uncertainty, error) records are
a ready-made uncertainty-calibration benchmark; the vendor labels support
cross-vendor robustness studies; the frozen-detector task maps support
dose-dependent downstream-task evaluation.

**Repository and licensing.** The corpus is deposited at
TODO(figshare/Zenodo) under DOI TODO(10.xxxx/xxxxxx), with per-source
licensing (numerical records CC BY 4.0; LIDC-derived pixel records CC BY 3.0;
AAPM/Mayo-derived pixel records not redistributed and regenerated locally from
the reuser's own authorised source copies via the RunBundle). A content-hash
mirror (IPFS RunBundle CID, anchored by a PWM L4 certificate) is provided as a
**supplementary** integrity anchor, not as the primary repository.

**Related submissions (declared for transparency).** This corpus is
deliberately **disjoint** from two companion submissions from our group:

- **WS-1** — the *raw paired CT scans* (the input benchmark), submitted
  separately to *Scientific Data* [TODO: status / manuscript ID if co-submitted].
  The present corpus releases the *reconstruction, uncertainty, error,
  task-output, and credential records derived from* those scans; the two are
  intended to be cited together, and the distinctness is stated explicitly in
  our Background & Summary.
- **WS-2** — the *signal-equivalence framework and credential schema*
  (`pwm_dose_equivalence`), submitted to *Nature Methods* [TODO: status]. Our
  credentials are computed with, and cite, that framework.

We flag these so the editorial office can confirm the present descriptor is not
redundant with the companion WS-1 dataset paper.

**Ethics.** The corpus contains no new human-subjects data and no protected
health information: every record is a derived image or numerical summary
computed from the PWM-LDCT benchmark, whose acquisitions, IRB approvals, and
consent basis are governed by the source data providers (TODO: name the WS-1
IRB protocol and the Mayo/AAPM data-use agreements).

The manuscript has not been published elsewhere and is not under consideration
by another journal. All authors have approved the submission and declare the
competing interests stated in the manuscript.

Thank you for your consideration.

Sincerely,

TODO(Corresponding author name), on behalf of all authors
TODO(affiliation, email, ORCID)
