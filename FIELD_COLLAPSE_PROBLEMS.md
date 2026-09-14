# What the low-dose CT field needs solved before a benchmark can settle claims

_Updated: 2026-09-14 · original review: 2026-09-13 at `acb510774984be05fd94a75725f3bf40c1edf051` · companions: [Director decisions](DIRECTOR_DECISIONS.md) and [Heyang's execution handoff](HEYANG_NEXT_2026-09-13.md)_

_Scientific and implementation review: source at `646daa6c3a01ab807dc729982115c57bdec3ff3a`; reconciled with the published handoff at `92e84d42de1d5ba341caa201258a3d4a91d81844`. This file records the scientific gaps and completion criteria; the handoff assigns the execution work. Dated observations remain tied to their inspected revisions. No experimental problem is declared solved by this documentation revision._

The charter aims to make the PWM Low-Dose CT Challenge a reference point for state-of-the-art claims. That is a useful ambition, not a result already established. A method absent from a leaderboard is **unevaluated by that benchmark**, not necessarily inferior. No finite benchmark makes a scientific field indisputable or removes the need for new research.

The practical goal is narrower and testable: make well-scoped comparisons credible, difficult to game, affordable to reproduce, and useful to researchers and clinicians.

**Are these seven problems sufficient for “domain collapse”? No.** Closing them would establish prerequisites for a credible benchmark. It would not necessarily produce a better reconstruction method, a clinically useful dose reduction, a minimum achievable dose, or independent adoption. The [WS-3 plan](WS-3_reference_method/README.md) explicitly targets an improvable top-quartile reference; completing that plan need not produce the best method.

For this program, the actionable ambition is **decisive evidence about which tested methods meet a defined diagnostic task at which dose and cost, for which patients and acquisition settings**. Evaluation can also decisively find that no tested method meets the target. Adoption by independent groups is a separate observed outcome. Literal closure of all low-dose CT research is not a finite-benchmark claim.

The completion specification therefore adds four obligations to the original seven: mathematical and credential validity (§8), a dose–task operating frontier with credible comparators (§9), independent final evaluation and clinically important failure checks (§10), and demonstrated external decision value (§11). A task, clinically justified margin, target population, acquisition protocol, reference method, and confirmatory analysis must be specified before those obligations can pass. The proposed requirements do not change the current scoring policy or certify a clinical use.

This review distinguishes committed measurements, inspected implementation, checks run for this revision, and proposed work. It changes no scoring rule, tolerance, dataset, release permission, or owner decision. The separate [`ldct_agent`](https://github.com/integritynoble/ldct_agent) CLI was not available locally and was not rerun; implementation findings below concern this repository's `WS-4_leaderboard/scoring` code.

## 1. Scoring: separating a smoothing control is necessary, not sufficient

**Status: a useful counterexample exists; diagnostic validity remains open.**

The committed AAPM artifact reports four held-out patients with paired full-dose/quarter-dose references, 1 mm B30 reconstruction. The quarter-dose reference is **noise-inserted**, not a second physical low-dose acquisition: [AAPM's challenge description](https://www.aapm.org/grandchallenge/lowdosect/) specifies noise insertion into the projection data. These are equal-weight **patient means**, not slice-level independent sample sizes. PSNR is in dB; the other displayed indices are dimensionless.

| Method | PSNR (dB) | SSIM | CNR | ROI BandER | BandER / blur |
|---|---:|---:|---:|---:|---:|
| Gaussian blur control | 41.63 | 0.9653 | 0.1706 | 0.4315 | 1.00× |
| LEARN | 41.61 | 0.9358 | 0.1036 | 3.8539 | 8.93× |
| RED-CNN | 41.20 | 0.9340 | 0.1036 | 3.8762 | 8.98× |
| CTformer | 39.59 | 0.9120 | 0.0863 | 6.7352 | 15.61× |

Source: [patient-level R3 measurements](WS-1_dataset/output/aapm_r3_roi_detectability.json) and [readable summary](WS-1_dataset/output/aapm_r3_roi_detectability_summary.md). The permanent control is a 5×5 Gaussian blur with sigma 1 pixel, specified in [task_spec.py](WS-4_leaderboard/scoring/task_spec.py).

Blur has the highest point estimate on PSNR, SSIM and CNR among these four methods. That does not establish a statistically significant win, nor does smoothing alone prove clinical harm. It shows that these indices cannot, by themselves, distinguish the intended smoothing control from the learned methods in this experiment.

ROI BandER separates this control among the four displayed metrics. It measures high-frequency energy relative to the reference, **not diagnostic information retained**. Values above one are not percentages of clinical benefit. Noise, sharpening or ringing could increase high-frequency energy; those are hypotheses to test, not measured failures of the current methods. Full-image BandER also separates the control in this artifact, so ROI BandER is not uniquely demonstrated to solve the problem.

Next, freeze a small anti-gaming evaluation with smoothing, added noise, oversharpening/ringing, and lesion-erasure or fabricated-structure controls. Include signal-present and signal-absent cases, fidelity checks and a prespecified task-based endpoint. Treat BandER as a diagnostic/control metric until its relationship to task performance is demonstrated on independent cases. Passing a finite control set supports only that tested scope; it is not a proof of being ungameable.

**Evidence needed to close this gap:** a versioned control matrix, independent held-out task results with uncertainty, and explicit examples of what each metric can and cannot detect. No new universal threshold is adopted here.

**2026-09-14 update — direction and task validity are both unresolved.** The newer [direction-analysis script](scripts/prepare-bander-direction-fix.py) recomputes the order from the committed R3 means. Sorting by candidate distance `abs(log(BandER))` instead of descending BandER puts blur first on AAPM and leaves it not worst in two of five reported groups. Neither ordering has thereby been validated against diagnostic performance. The script's displayed noise-control values are hard-coded; this review does not treat them as a fresh image experiment. The [current operator handoff, §3b](HEYANG_NEXT_2026-09-13.md) assigns the remaining real-anatomy control measurements elsewhere.

A control should be rejected as clinically inadequate because it fails the intended task, not simply because it smooths or lacks learning. The scientific validation must test whether the proposed gate rejects task-beneficial methods as well as whether it admits harmful ones. A [primary phantom study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9544990/) found improved modeled detectability with smoother deep-learning reconstruction settings; that does not validate this Gaussian control, but it rules out using “smoother” alone as the harmful-outcome label. Even matching reference high-frequency energy is not proof of preserving lesion location or identity.

## 2. Clinical meaning: define the task before choosing a winning margin

**Status: exploratory differences are measurable; clinical superiority is not established.**

Recomputing CTformer minus RED-CNN ROI BandER from the four patient records gives:

| Quantity | Result | Interpretation |
|---|---:|---|
| Patient differences | 1.6240, 2.5386, 4.6088, 2.6645 | All four BandER differences are positive |
| Mean difference | 2.8590 | Difference on this metric, not a clinical benefit |
| Sample SD of paired differences | 1.2553 | Between-patient spread in this sample |
| Two-sided paired t-test | p = 0.0198; df = 3 | Assumption-dependent, exploratory |
| Exact two-sided Wilcoxon signed-rank test | p = 0.125 | Four nonzero differences with distinct absolute ranks |
| Percentile bootstrap interval, 95% | [1.8841, 4.0913] | Resampling these four patients; not a clinical validation |

The earlier quoted Wilcoxon value, 0.1003, matches a continuity-corrected normal approximation, not the exact small-sample calculation. Here the most extreme signed-rank outcome has two-sided probability `2 / 2^4 = 0.125`. Assumptions and exact-versus-approximate methods must be named; see the [SciPy Wilcoxon documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).

These analyses need not agree at a chosen significance threshold: they use different assumptions and procedures. None was established here as a preregistered, multiplicity-controlled primary analysis. The percentile interval comes from all 256 ordered patient-resampling outcomes and cannot resolve the lack of population coverage. The historical `mde80 = 2.6116` is omitted because its generating CLI and method were not verified. A detectable effect is also not the same as a clinically worthwhile effect.

Only the paired **BandER** differences consistently favour CTformer; the displayed PSNR, SSIM and CNR favour RED-CNN. The missing element is a validated clinical interpretation, not a mathematical unit.

Next, a medical physicist, radiologist team and statistician should specify the intended use, lesion/task, dose regime, primary endpoint, worthwhile benefit or noninferiority margin, and analysis before new confirmatory testing. A radiologist choosing an arbitrary BandER margin after seeing this table would not supply that validation.

Phantom and appropriately validated model-observer studies can provide bounded task-based evidence before a reader study. They do not by themselves establish clinical benefit. [AAPM TG 233](https://www.aapm.org/pubs/reports/RPT_233.pdf) describes task-based assessment and the limitations of traditional image-quality surrogates; it does not supply a universal advanced-metric pass/fail threshold.

**Evidence needed to close this gap:** a prospective task/analysis protocol, validation appropriate to the claimed use, and a reader study if the claim concerns reader performance. Clinical collaboration is important, but it is not the sole prerequisite for useful engineering or scientific progress.

## 3. Generalization: match controls to the group being evaluated

**Status: raw cross-group thresholds are unsupported; a future aggregate is not mathematically ruled out.**

The [cross-group summary](WS-1_dataset/output/aapm_lidc_cross_vendor_spread_summary.md) reports blur ROI BandER of 0.0452 for LIDC-GE and 0.4315 for AAPM-Siemens, about 9.5× apart. This comparison mixes **cohort, vendor, protocol and dose-generation method**—project-simulated LIDC versus Mayo noise-inserted AAPM reference. It does not isolate a vendor effect.

The weakest measured GE model is 0.4377: 9.67× its own control but only 1.014× the AAPM control. It therefore **passes** a rank-only comparison against 0.4315, but would fail a 3× separation requirement against that unmatched control. The similarly named regression test uses synthetic GE data at 0.40; it is not the measured 0.4377 case. See [test_trap_rank.py](WS-4_leaderboard/scoring/tests/test_trap_rank.py).

Keep matched controls and report cohort/vendor/dose strata separately under the current policy. Across the reported groups, the weakest learned method's within-group ratio ranges from 8.93× to 18.96×; these are descriptive results, not validated clinical margins. The four LIDC vendor groups have only two patients each, versus four in the AAPM group.

The summary explicitly describes replicated patient means used as samples for its cross-vendor tests. Such replication does not create independent observations. Do not use those inferential p-values as evidence of generalization; recover genuine patient-level observations and recompute the analysis.

A prespecified, calibrated composite could eventually be useful, but would require justified normalization and weights, coverage rules, uncertainty, sensitivity checks and retained per-group results. These data neither validate such a composite nor prove that all scalar summaries are impossible. Introducing one would require a separate protocol/version decision.

**Evidence needed to close this gap:** independent patient-level evaluation across the claimed regimes, matched controls, and transparent reporting of unsupported or missing strata.

## 4. Evidence and power: count patients and identify how dose data were generated

**Status: limited independent patient evidence; analysis repairs and new evidence are both needed.**

The [AAPM split used in these paired-dose analyses](WS-1_dataset/output/aapm_paired_baselines.json) contains 10 patients: 3 training, 3 validation and 4 test. This is not a claim about every available LDCT dataset or every result in the field.

The [LIDC release documentation](WS-1_dataset/README.md) lists 1,010 patients split 589/216/205; its low-dose data are simulated. A separate [bootstrap report](WS-1_dataset/output/lidc_simulated_bootstrap_report.md) uses 764 distinct test **slices**, not 764 patients. It removed five identical seed copies; removing duplicates is necessary but does not remove within-patient correlation.

Both dose-generation methods support useful but bounded evidence; neither is a second physical low-dose acquisition. The [current manuscript's simulation-versus-reference subsection](WS-1_dataset/paper_draft/manuscript.tex) states this correctly and reports a noise-distribution comparison. Other passages still call the AAPM data repeated physical acquisitions or “genuinely paired real” data. Those descriptions need reconciliation. A comparison against the Mayo noise-insertion reference is not, by itself, validation against re-acquired low-dose scans, nor does noise-distribution agreement establish task-performance equivalence. This review did not rerun that comparison or establish simulation-to-acquisition validation.

Next work can start without acquiring a new cohort:

- Recover a privacy-preserving slice-to-patient map and use patient-level or hierarchical uncertainty estimates; until then, label slice-bootstrap intervals accordingly.
- Remove replicated-mean pseudo-samples from inferential analyses. Label project-simulated, Mayo reference noise-inserted, and any future physically re-acquired low-dose data separately; align conflicting manuscript and artifact descriptions without overwriting historical records.
- Design sample size from the prospective endpoint, relevant effect, patient/reader variability and error control. Do not infer adequate power by comparing a post-hoc MDE to the observed effect.
- Seek additional independent acquisitions or simulator validation where needed; do not assert an unsupported “orders of magnitude” requirement.

**Evidence needed to close this gap:** patient-disjoint provenance, a justified sampling/power plan, appropriately clustered uncertainty, and additional validation matched to the intended claim.

## 5. Reproduction: preserve the old failure and scope the new pass

**Status: the amended log-comparison criterion passes; independent numerical reproduction is not newly certified.**

The [Director record, §2.1](DIRECTOR_DECISIONS.md) reports a deterministic rerun with no same-side differences after substantial GPU work. That reported observation does not uniquely identify the cause of the remaining reference mismatch, and it does not prove that bitwise agreement across environments is impossible. [PyTorch's reproducibility guidance](https://docs.pytorch.org/docs/2.8/notes/randomness.html) warns that cross-release/platform agreement is not guaranteed; that is different from an impossibility theorem.

The existing owner decision selected route (b): relative tolerance `1e-4` for the named floating-point metrics. The [current comparator](WS-1_dataset/R6_recalc/recompare_per_metric.py) also requires exact agreement for `n`. This was an amendment **after the original mismatch was observed**, not a prospectively satisfied original criterion. Preserve the original failure, rationale and amendment history; future protocols should declare criteria before their confirmatory runs.

Running the comparator with `--check` on 2026-09-13 returned exit 0: all five listed models pass, and the committed verdict matches its re-derivation. It checks **previously logged differences**, not original predictions, raw scan processing or a fresh environment's model outputs. Its `PASS` is therefore a log-derived tolerance check, not full independent reproduction.

Generator status also needs correction:

| Component | Current evidence |
|---|---|
| Original `compare_full764.py` | Not found in this source snapshot; original comparison generation remains a provenance gap |
| [recompare_per_metric.py](WS-1_dataset/R6_recalc/recompare_per_metric.py) | Present; re-evaluates committed difference logs under the amended criterion |
| [bootstrap_lidc_sim.py](WS-1_dataset/analysis/bootstrap_lidc_sim.py) | Present; distinct-slice bootstrap is implemented, with the patient-mapping limitation above |

Next, preserve source/data/weight/environment hashes, recover the original comparator or document a validated replacement, and reproduce predictions before comparing metrics. Define coverage, missing/nonfinite-value handling and behaviour near zero explicitly; numerical closeness, complete comparison coverage and clinical equivalence are separate questions. Any tolerance change remains a separate reviewed decision.

**Evidence needed to close this gap:** a pinned, rights-compliant input-to-result recipe run by a separate operator, with full logs, failures and tolerances disclosed.

## 6. Verification: distinguish stored evidence from approved publication

**Status: useful gates and regression controls exist; end-to-end enforcement is not established.**

The inspected implementation is more limited than “closed for rungs 1–6”:

| Observation in this snapshot | Consequence |
|---|---|
| [gates.py](WS-4_leaderboard/scoring/gates.py) registers three named `PROBES` | It does not automatically require probes for every future gate |
| [test_gates.py](WS-4_leaderboard/scoring/tests/test_gates.py) iterates those registrations and can skip unavailable artifacts | Missing evidence is not an exercised pass |
| [rung_registry.py](WS-4_leaderboard/scoring/rung_registry.py) validates registry structure | A well-formed status record is not proof that its scientific check ran |
| [leaderboard.py](WS-4_leaderboard/scoring/leaderboard.py) deliberately records and saves failed trap verdicts | Preserving failed evidence is useful; saving is not publication approval |
| [CLI submission](WS-4_leaderboard/scoring/cli.py) saves, prints `accepted` and returns 0 without the trap-rank publishing assertion | Receipt of a submission must not be presented as a scientifically approved board |

Nine selected synthetic trap-regression tests passed in the **13 September review**. They exercise the named helper behaviours, not the full suite, all ladder rungs or the separate agent's runtime. The **14 September audit** could not collect the selected pytest tests because its interpreter lacked pytest. Its source inspection and dependency-free helper probes are separate evidence; no current full-suite pass was established.

Next, identify every actual publication path and give submission receipt, diagnostic storage and approved publication distinct states. Add an integration test showing that a valid fixture can publish while each invalid fixture cannot publish, without deleting the failed evidence. Include missing controls/metrics, NaN/infinity, unsupported groups, ties and insufficient comparisons. Require each mandatory gate to have both positive and negative probes; fail coverage checks when a gate or probe is omitted.

**Evidence needed to close this gap:** machine-readable gate coverage and end-to-end publication tests, with missing evidence reported as unverified rather than silently passed. This review does not itself change the CLI or close a rung.

**2026-09-14 update — validation must bind the claim to its evidence.** Bounded in-memory checks found that [`check_paired_submission`](WS-4_leaderboard/scoring/verify.py) accepts a wrong task label, NaN values, and nonnumeric strings when the expected fields are present. The trap helper can return `PASS` for a NaN comparison and for zero comparisons; the latter includes a no-claim note that consumers must respect. Source inspection also found that group checks enumerate present groups rather than a required-stratum manifest, and registry load/save helpers ignore the structural validation error list. These are helper/source findings, not a demonstration of a live website publishing invalid results. Require finite typed metrics, exact task/protocol identity, complete required-stratum coverage, and binding to input/model/evaluator hashes in addition to the publication-path checks. A gate executing successfully is still not evidence that its scientific criterion is valid. [Heyang's handoff, §3c](HEYANG_NEXT_2026-09-13.md#3c-fix-acceptance-of-invalid-evidence--engineer-work-then-maintainer-review) specifies the positive and negative integration cases.

## 7. Adoption: release a usable benchmark without releasing restricted assets

**Status as of 2026-09-14: public repository access confirmed; complete external reproduction remains unverified.**

The earlier review recorded private repository visibility. Current GitHub metadata reports this repository **public**, consistent with the [newer handoff](HEYANG_NEXT_2026-09-13.md). Visibility is no longer the outstanding barrier. Public access does not establish that the complete data/weight recipe is available or that its rights and numerical reproduction have been independently verified. The release-blocker discussion below is historical context; resolve present status from the current inventory rather than assuming every old blocker remains open.

[Director decisions, §2.3](DIRECTOR_DECISIONS.md) records release blockers involving Mayo-derived arrays and redistributed third-party weights. CoreDiff source has been un-vendored (`bcc234f`), but its historical result-to-upstream-commit provenance was unresolved in the inspected review. The earlier `acb5107` snapshot prepared CTformer weight fetching; it is not current `main`, nor proof that all release work or rights questions are settled. Check the current acquisition and release inventory. A download script is not permission to use or redistribute an asset.

Next, verify and complete a minimal rights-cleared public package: scoring code, synthetic fixtures, pinned environments, authorized data/weight acquisition instructions, manifests and example result schemas. Keep restricted assets out of that package. Have a fresh operator follow the recipe and record access requirements, runtime and cost. Resolve the relevant rights/DUA questions before distributing additional assets; public repository visibility is already established.

Adoption also needs documented tasks, stable versioning, submission validation, correction/appeal procedures and predictable evaluation cost. Participation should be attractive because the benchmark supports credible claims—not because nonparticipation is labelled evasion.

**Evidence needed to close this gap:** a rights-reviewed release inventory, an accessible package, and a successful fresh-operator run with its limitations disclosed.

## 8. Scientific foundations: correct the claims before issuing credentials

**Status: a substantive definition-level counterexample exists.**

The [current WS-2 manuscript](WS-2_framework/paper_draft/manuscript.tex) calls its per-patient formulation strictly stronger than its aggregate formulation and says the former implies the latter. As written, it does not. Let patient performance difference be zero for 95% of patients and −1 for 5%, with margin 0.02 and allowed patient exception fraction 0.05. The stated per-patient condition holds, but the absolute mean difference is 0.05, outside the aggregate margin. This counterexample uses bounded scores; unbounded tails are not required.

Audit the population estimands, equivalence/noninferiority directions, coverage assumptions, patient/reader clustering, multiplicity, and verdict semantics before treating the framework as an evidentiary foundation. Keep the allowed fraction of exceptional patients separate from the statistical error probability. A population ROC AUC is a cohort functional, not an individual-patient score to average without further definition. Credential validation must check the asserted task, data, model and evaluation provenance rather than only internal JSON consistency.

For a patient-level difference `d` bounded by `abs(d) <= M`, with at most fraction `tau` outside margin `epsilon` and `M >= epsilon`, the general bound is `abs(E[d]) <= (1-tau)*epsilon + tau*M`, not necessarily `epsilon`. Keep `tau` separate from the statistical error probability `alpha`. Correct aggregate, patient-tail and sampling-uncertainty claims separately.

**Evidence needed to close this gap:** corrected definitions and proofs, independent statistical review, and adversarial estimator/credential checks covering boundary cases, clinically important alternatives, declared sampling structures and false-PASS behavior. The counterexample above is exact and does not depend on an estimator or new image experiment. This review does not repair or validate the implementation by changing this paragraph.

## 9. Decisive scientific result: measure dose–task performance against credible alternatives

**Status: a trustworthy leaderboard and a breakthrough method are different deliverables.**

Evaluate the declared task across a prespecified set of dose levels, against an adequate named reference and strong available alternatives. Include relevant classical/iterative, learned and clinical reconstruction configurations where accessible. Separate raw-projection and image-only access, training/adaptation regimes and compute constraints; document unavailable competitors. Keep fidelity and resource cost alongside task performance. Claims are about the tested configurations, not every method in a named family.

For a noninferiority-based dose-reduction claim, define higher-is-better task performance `P`, adequate reference `ref`, and `Delta = P(method, dose, stratum) - P(ref, stratum)`. For **every required stratum**, require all of the following under the frozen analysis:

1. Dose is demonstrably lower: `q < q_ref` in the declared dose quantity, with appropriate uncertainty and any prespecified clinically worthwhile reduction. A lower simulator parameter supports only the validated simulation scope.
2. The lower confidence bound for `Delta` exceeds the negative of the justified noninferiority margin, `-delta`.
3. Any prespecified absolute adequacy floor passes, for example a lower confidence bound for `P` above `p_min`.
4. Upper confidence bounds on critical-error endpoints meet their justified limits.
5. Required data/protocol coverage, input access, integrity and resource constraints pass.

Reference and label quality must be established independently of contender results. Set precision/power targets in advance and account for patient/reader dependence and selection across methods, doses and strata. Bounds must have the coverage required by that plan. Missing evidence is unverified; an interval that crosses a decision boundary is unresolved; evidence supporting unacceptable performance is a failed criterion. None can be relabeled noninferiority.

Use two-sided equivalence only when closeness in both directions is the intended claim. A method that is materially better can fail two-sided equivalence without being worse. Report the **lowest tested dose supported by the evidence** and its uncertainty; do not silently interpolate a minimum or assume monotonic learned performance. [AAPM TG 233](https://www.aapm.org/pubs/reports/RPT_233.pdf) motivates task-specific dose/performance assessment, not a universal acceptance margin.

**Evidence needed to close this gap:** a frozen comparison protocol, task–dose curves with appropriate uncertainty, supported/unsupported operating regions, and a reproducible result that resolves a specific method/dose/cost decision against credible alternatives. A supported negative result can resolve that comparison without delivering a successful dose-reduction method. If the stronger claim is near-optimality, it additionally needs a valid task-specific bound, an achievable method and a quantified gap under matching acquisition and population assumptions. A physical-minimum claim requires an appropriate impossibility bound; failure of current methods supplies no such bound.

## 10. Independent challenge: protect the final test and bound important failures

**Status: independent final evidence and a declared failure envelope are required.**

Predeclare held-out institutions/protocols, patient exclusions, required strata, model freeze and allowed adaptation. Reserve final confirmatory data from metric design, training, tuning, control selection and repeated leaderboard feedback. Record training-data overlap and test access; a frozen container or a file named “heldout” does not provide that protection. [Blum and Hardt](https://proceedings.mlr.press/v37/blum15.html) show why repeated leaderboard feedback can overfit a holdout even without exposing its labels.

Test signal-present and signal-absent cases, small/low-contrast lesions and supported difficult subgroups, including false structure, missed lesions and measurement bias. Synthetic perturbation controls need an independently justified task/harm interpretation. Validate uncertainty against the event being claimed at a specified review/referral workload; pixelwise error correlation is not a calibrated clinical risk bound. Use blinded, appropriately analyzed reader evidence for reader-performance claims. A favorable pooled mean must not silently override a required-stratum failure or missing coverage.

**Evidence needed to close this gap:** a documented untouched final evaluation, task/failure results by required stratum, uncertainty and case-mix sensitivity, and external replication appropriate to the proposed use. Failure or inadequate precision leaves the corresponding claim unsupported. The simulated-to-acquisition scope must remain explicit; additional physical patient scans are not a blanket requirement for every engineering claim.

## 11. Field influence: demonstrate independent decision value

**Status: adoption is an outcome to measure, not a consequence of finishing software.**

An independent operator must be able to obtain authorized inputs, rerun the evaluation, and reproduce the supported decision within the declared numerical and statistical criteria. Independent teams must then be able to submit credible alternatives and challenge the result under the same rules. Publish unresolved ties, failures, costs, revisions and appeal outcomes as well as winners. Biomedical challenge research shows that [case mix, ranking rules and reference annotations can change rankings](https://arxiv.org/abs/1806.02051); a leaderboard number alone is not durable evidence.

Measure whether external groups actually use the benchmark to support or overturn a defined claim, and whether that result survives another prespecified evaluation. Public visibility, paper counts, registry entries, citations and submission counts are not substitutes for this evidence. A reproducible negative finding can be influential even if the reference method never wins.

**Evidence needed to close this gap:** independently documented reproduction and challenges, a consequential scoped decision supported by the final evidence, and recorded external use. These outcomes could make the program a strong reference within its scope; they do not guarantee universal adoption or permanently settle low-dose CT.

## Next work and owner review

These are proposed deliverables, not completed tasks or new spending/data-access grants. Engineering checks can proceed in parallel with protocol design; there is no single blocker whose removal validates everything else.

Completing a listed implementation task is not the same as obtaining a favorable scientific result. Use the completion contract below to decide what the work supports. Validate the meaning of a scientific gate before treating enforcement of it as diagnostic certification. [Heyang's handoff](HEYANG_NEXT_2026-09-13.md) contains the existing merge, measurement and data-copy assignments; this problem list defines the scientific evidence those tasks must ultimately support.

| Priority | Deliverable | Who does the work | Owner checks before accepting |
|---|---|---|---|
| P0 | Separate submission receipt from publication approval; exercise both paths | Benchmark engineer + reviewer | Valid/invalid fixture logs, gate coverage, exact commit |
| P0 | Correct dose provenance, sample units and replicated-mean inference | Analyst + statistician | Consistent source labels, patient provenance and corrected uncertainty report |
| P0 | Correct framework definitions and enforce typed, finite, claim-bound evidence | Statistician + framework/benchmark engineers | Counterexamples resolved, estimands and error rates justified, wrong-task/nonfinite/empty-coverage cases rejected |
| P1 | Freeze anti-gaming tasks, endpoint and analysis plan | Physicist + radiologists + statistician | Intended claim, controls, margins and held-out protocol |
| P1 | Freeze strong comparators, dose levels, resource tracks and the protected final evaluation | Research team + independent evaluator | Input-access policy, adequate reference, task–dose target, required strata and selection-error control |
| P1 | Recover/pin the input-to-result reproduction recipe | Engineer + separate operator | Inputs/hashes, original failure, amended criterion and fresh-run logs |
| P1 | Validate task performance and generalization | Research team | Independent results by supported stratum; reader evidence where claimed |
| P1 | Demonstrate a scoped decision from the task–dose frontier and failure results | Research team + independent evaluator | Practical effect or resolved limitation, uncertainty, competing configurations and critical-error bounds |
| P2 | Publish the minimal rights-cleared package | Asset owners + maintainer | Rights inventory, authorized access recipe and public-package smoke test |
| P2 | Establish independent challenge and actual external use | External groups + maintainer | Reproduced decisions, new challengers, correction record and documented use; no adoption guarantee |

For each deliverable, record `claim + protocol version + input/model/code/evaluator hashes + commands/results + uncertainty + required-stratum coverage + independent check + limitations + decision/date`. Keep **implementation complete**, **technically verified**, **scientifically supported**, **externally used** and **owner accepted** separate. An owner accepting a deliverable does not itself establish its scientific claim. This document records no new owner acceptance.

## Completion contract for a decisive LDCT result

Freeze one versioned claim before confirmatory testing. Missing required information means **unverified**.

| Required record | What must be specified |
|---|---|
| Intended decision | Task/anatomy, population, acquisition settings, exclusions and the method/dose/cost choice the evidence should resolve |
| Dose and access | Dose quantity, units, levels and generation method; raw-projection versus image access; training, pretraining and permitted adaptation |
| Reference and competitors | Adequate reference and validated labels; versions/weights/tuning of strong accessible alternatives; missing competitors and implications |
| Outcomes and resources | Primary task endpoint/direction, justified margins, any adequacy floor, critical-error limits and resource constraints |
| Sampling and analysis | Required external strata, independent patient counts, precision/power target, patient/reader dependence, selection/multiplicity and missing-data rules |
| Evidence protection | Input/model/code/evaluator hashes, freeze date, final-test access and feedback controls, independent evaluator and correction process |

The success claim must name the level actually earned:

| Outcome | Required result |
|---|---|
| Auditable benchmark | Correct definitions/provenance and enforced evidence checks; valid and invalid publication fixtures; independent input-to-result reproduction |
| Decisive scoped comparison | Task validity plus an adequately precise, independently confirmed method/dose/cost decision against credible alternatives under §§9–10; ties and negative findings retain their actual interpretation |
| Successful dose reduction | The lower-dose and diagnostic/critical-error criteria in §9 pass in every required stratum; an inconclusive or equal-dose comparison does not meet this claim |
| Independently useful reference | External groups reproduce, challenge and use the supported decision under a stable accessible process (§11) |
| Near-optimal reconstruction, only if claimed | A valid bound and a quantitatively bounded achievable gap under matching assumptions, with empirical evidence for the stated scope (§9) |

Passing implementation checks does not automatically advance the scientific outcome. Publish unsupported regions, contradictions and unresolved comparisons. If development changes follow a final-test result, use a new protected confirmatory evaluation or a prospectively justified adaptive design; do not tune the criterion on the same final data until it passes.

Solving the eleven problems **with these outcome requirements** could establish a decisive reference for the stated LDCT tasks. It would not guarantee a universal winner, adoption by every group, or permanent closure of the field. A claim beyond the tested scope requires additional evidence.

## Verification record: distinguish 13 September tests from 14 September checks

The following commands document the **13 September review**. They are bounded offline checks, not reconstruction runs or clinical validation.

```bash
# Recheck the committed difference-log verdict; do not use --write.
python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check

# Nine selected synthetic helper-level regression controls only.
(
  cd WS-4_leaderboard || exit 1
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. \
    python3 -B -m pytest scoring/tests/test_trap_rank.py -q -p no:cacheprovider \
    -k 'global_check or multi_vendor_board or group_with_no_trap or entry_below_its_own_group or min_ratio_is_separate or trap_without_the_index or missing_trap or tying_the_trap or old_cnr_led'
)
```

Both commands were recorded as exit 0 on 2026-09-13. Patient-level arithmetic was checked against the committed R3 JSON. These historical results are not a new full-suite result.

On 2026-09-14 at `646daa6`, dependency-free in-memory probes reproduced the wrong-task, NaN/string and zero-comparison behaviors in §6; source inspection identified the publication, group-coverage and registry-validation limitations. Running `python3 -B scripts/prepare-bander-direction-fix.py` rederived the stored R3 ordering in §1; its hard-coded noise values were not new measurements. Running `python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` rederived the amended log-comparison PASS. The §8 counterexample was checked exactly using Python fractions. The selected pytest attempt could not collect because the audit interpreter lacked pytest.

The documentation integration checked links, Markdown structure and the final diff. No original images, predictions or reader results were generated, and no live scoring/publication service was exercised. The review supports the stated corrections and counterexamples, **not a current full-suite pass, clinical superiority, complete reproduction, or independent certification of the benchmark**.
