# Related work — what does the field already call this?

**Status:** Seeded 2026-06-01 alongside the manuscript A6 intro-paragraph insert. This is the skeleton for the [`open_questions.md`](open_questions.md) §1 deliverable (literature pass, SHARPEN priority, 1.5 weeks). The manuscript intro already cites the four anchor entries below; this memo expands them into the 1-paragraph-each summaries and the explicit "what is genuinely new" memo that gates the v0.2 framework draft.

**Convention:** each entry summarizes the paper, names the specific construct that overlaps with signal-equivalence, and records the gap that signal-equivalence fills. Entries are ordered by lineage proximity, not chronologically.

---

## §1. Statistical lineage — test-of-equivalence

### Schuirmann 1987 (TOST) — [BibTeX: `schuirmann1987tost`]
Foundational paper for the two one-sided tests procedure in bioequivalence. Establishes that an equivalence claim must be reported with a pre-specified margin and a pre-specified significance level, and that the procedure rejects the null of non-equivalence iff both one-sided CIs lie in the equivalence band. **Overlap with signal-equivalence:** the inner statistical mechanism is identical (a two-sided equivalence test against a margin). **Gap:** Schuirmann is per-subject pharmacokinetic AUC; medical imaging needs a paired-on-patient estimator over a *task* on an *image*, plus a subpopulation field and a signal-reduction operator. None of those four extensions are in the TOST literature.

### Piaggio 2012 (CONSORT non-inferiority extension) — [BibTeX: `piaggio2012ni`]
Mandates that randomized-trial publications report the equivalence margin, the analysis population, the CI, and the comparator. **Overlap:** the discipline of "every margin and confidence explicit" — what signal-equivalence imports as a reporting standard. **Gap:** CONSORT is for trial endpoints, not for reconstruction-method publications; the medical-imaging methods community has not adopted an analogous standard.

---

## §2. Imaging lineage — task-based image-quality assessment (TB-IQ)

### Barrett 1990 — Objective assessment of image quality — [BibTeX: `barrett1990objective`]
The canonical statement that image-quality metrics must be tied to a task performed on the image, not to scalar fidelity. Establishes that the figure of merit is observer-dependent and that the ideal-observer SNR is the natural upper bound. **Overlap:** the principle that "task is a first-class object" is shared verbatim. **Gap:** Barrett 1990 is about evaluating a single system; it does not formalize pairwise equivalence between two systems at a reduced operating point, does not carry an explicit subpopulation field, and does not define a signal-reduction operator.

### Barrett & Myers 2013, *Foundations of Image Science* — [BibTeX: `barrett2013foundations`]
The textbook treatment. Part IV (chapters on Hotelling and channelized-Hotelling observers, model observers and the ideal observer) is the formal apparatus that AAPM TG-233 builds on. **Overlap:** any task-output figure of merit defined in the textbook is a valid choice for the metric $P$ inside a signal-equivalence credential — the framework's $P$ slot is intentionally permissive. **Gap:** the textbook is silent on equivalence-margin reporting, on the credential-as-content-addressed-artifact discipline, and on the multi-modality, multi-method-pair comparison setting that signal-equivalence targets.

### Samei et al.\ 2019, AAPM Task Group 233 — [BibTeX: `samei2019tg233`]
The CT-specific TB-IQ standard. Specifies model-observer-based detectability indices, standardized phantoms, and reporting conventions for CT system performance. **Overlap:** TG-233's task-conditional performance-evaluation discipline is the closest existing standard to what signal-equivalence proposes for CT. **Gap:** TG-233 (a) is CT-only, not modality-general; (b) is system-evaluation, not pairwise-method-equivalence; (c) does not specify an equivalence margin or significance level; (d) does not carry a subpopulation-as-measure field; (e) uses standardized phantoms rather than patient subpopulations, so its reference distribution differs in kind from $\Pi$.

---

## §3. Reproducibility / drift lineage (cited but not in this memo's depth pass)

- Wang, Ye & De Man 2020, *Deep Learning for Tomographic Image Reconstruction* (Nat MI). Cited in the manuscript as the survey establishing the longitudinal-comparison drift problem. Not a TB-IQ paper; relevant for motivating the content-addressed schema.
- FDA AI/ML SaMD draft guidance (2024). Cited for subgroup-stratified performance reporting and predetermined-change-control-plan expectations. Not a methods paper; a regulatory benchmark.

---

## §4. "What is genuinely new" — the gate for v0.2

The four contributions enumerated in the manuscript intro are the result of asking: *for each of the four anchor papers above, what does signal-equivalence add that is not present in the source?* The current answer is:

1. **Type-signature discipline tying an equivalence claim to a signal-reduction operator $T_r$.** Not in Schuirmann, Piaggio, Barrett 1990, Barrett & Myers, or TG-233. The closest precedent is fastMRI's mask-family conventions, which are operational rather than definitional.
2. **Paired-on-patient bootstrap with BCa / DeLong / percentile auto-selection.** Standard bootstrap variants individually; the credential-aware auto-selection rule is the new piece.
3. **Modality-general single API.** Not present in TG-233 (CT-only), fastMRI evaluator (MRI-only), or any vendor toolchain.
4. **Content-addressed credential schema with hash-resolved framework version.** Borrows from the software-supply-chain literature (`sigstore`, `Sylk`) rather than from imaging, but appears not to have been applied to a reporting standard for medical-imaging methods.

**Falsifier:** if a reader finds one of the four anchor papers (or a near-anchor not on this list) that *already* contains construct $k$ above, the corresponding contribution should be downgraded from "novel" to "explicit codification of existing practice." This is the explicit acceptance criterion for the v0.2 draft.

---

## §5. Candidates to read end-to-end for the full memo (open_questions §1)

The four anchor papers above are cited; the full open_questions §1 deliverable adds depth-pass reading of:

1. fastMRI reader-study papers (Knoll, Recht et al.) — reader-study + model-observer hybrid evaluation in accelerated MRI; tests our claim that signal-equivalence is genuinely new for MRI.
2. A recent channelized-Hotelling-observer paper for low-dose CT (candidate: Solomon & Samei, or Yu & McCollough lineage) — confirms TB-IQ pipeline integrates as $P$.
3. Wunderlich & Noo (or Eckstein) on observer-model variance / sample-size — informs the open_questions §2 sample-size formula.

These are not blockers for the v0.1 → v0.2 manuscript pass; they are blockers for committing to the novelty claims in §4 above with high confidence.

---

## Cross-references

- [`open_questions.md`](open_questions.md) §1 — this memo is the deliverable.
- [`../paper_draft/manuscript.tex`](../paper_draft/manuscript.tex) intro — paragraphs "Relation to existing equivalence statistics" and "Relation to task-based image-quality assessment" reflect this memo's positioning.
- [`../paper_draft/refs.bib`](../paper_draft/refs.bib) — `barrett1990objective`, `barrett2013foundations`, `samei2019tg233` added 2026-06-01.

---

*Seeded v0.1 — 2026-06-01. Expand each entry to ~1 paragraph of depth-pass notes once the read-pass for open_questions §1 begins; revise the §4 novelty claims if any depth-pass finding contradicts them.*
