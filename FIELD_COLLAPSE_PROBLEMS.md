# What the low-dose CT field needs solved before a benchmark can settle claims

_Reviewed: 2026-09-13 · source snapshot: `acb510774984be05fd94a75725f3bf40c1edf051` · companion: [Director decisions](DIRECTOR_DECISIONS.md)_

The charter aims to make the PWM Low-Dose CT Challenge a reference point for state-of-the-art claims. That is a useful ambition, not a result already established. A method absent from a leaderboard is **unevaluated by that benchmark**, not necessarily inferior. No finite benchmark makes a scientific field indisputable or removes the need for new research.

The practical goal is narrower and testable: make well-scoped comparisons credible, difficult to game, affordable to reproduce, and useful to researchers and clinicians.

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

Nine selected synthetic trap-regression tests passed for this revision. They exercise the named helper behaviours, not the full suite, all ladder rungs or the separate agent's runtime.

Next, identify every actual publication path and give submission receipt, diagnostic storage and approved publication distinct states. Add an integration test showing that a valid fixture can publish while each invalid fixture cannot publish, without deleting the failed evidence. Include missing controls/metrics, NaN/infinity, unsupported groups, ties and insufficient comparisons. Require each mandatory gate to have both positive and negative probes; fail coverage checks when a gate or probe is omitted.

**Evidence needed to close this gap:** machine-readable gate coverage and end-to-end publication tests, with missing evidence reported as unverified rather than silently passed. This review does not itself change the CLI or close a rung.

## 7. Adoption: release a usable benchmark without releasing restricted assets

**Status: external access and release readiness remain open; this is more than a visibility switch.**

Authenticated GitHub metadata reported the repository private during this review. An unauthenticated outsider therefore cannot use this repository as the public reproducibility entry point; this does not rule out evaluation by authorized collaborators or other available artifacts.

[Director decisions, §2.3](DIRECTOR_DECISIONS.md) records release blockers involving Mayo-derived arrays and redistributed third-party weights. CoreDiff source has now been un-vendored (`bcc234f`), but its historical result-to-upstream-commit provenance is still unresolved. The latest commit (`acb5107`) prepares CTformer weight fetching; it does not establish that removal/release work has been applied or that all rights questions are settled. A download script is not permission to use or redistribute an asset.

Next, prepare a minimal rights-cleared public package: scoring code, synthetic fixtures, pinned environments, authorized data/weight acquisition instructions, manifests and example result schemas. Keep restricted assets out of that package. Have a fresh operator follow the recipe and record access requirements, runtime and cost. Obtain the relevant rights/DUA review and owner release approval before changing visibility or distributing data.

Adoption also needs documented tasks, stable versioning, submission validation, correction/appeal procedures and predictable evaluation cost. Participation should be attractive because the benchmark supports credible claims—not because nonparticipation is labelled evasion.

**Evidence needed to close this gap:** a rights-reviewed release inventory, an accessible package, and a successful fresh-operator run with its limitations disclosed.

## Next work and owner review

These are proposed deliverables, not completed tasks or new spending/data-access grants. Engineering checks can proceed in parallel with protocol design; there is no single blocker whose removal validates everything else.

| Priority | Deliverable | Who does the work | Owner checks before accepting |
|---|---|---|---|
| P0 | Separate submission receipt from publication approval; exercise both paths | Benchmark engineer + reviewer | Valid/invalid fixture logs, gate coverage, exact commit |
| P0 | Correct dose provenance, sample units and replicated-mean inference | Analyst + statistician | Consistent source labels, patient provenance and corrected uncertainty report |
| P1 | Freeze anti-gaming tasks, endpoint and analysis plan | Physicist + radiologists + statistician | Intended claim, controls, margins and held-out protocol |
| P1 | Recover/pin the input-to-result reproduction recipe | Engineer + separate operator | Inputs/hashes, original failure, amended criterion and fresh-run logs |
| P1 | Validate task performance and generalization | Research team | Independent results by supported stratum; reader evidence where claimed |
| P2 | Publish the minimal rights-cleared package | Asset owners + maintainer | Rights inventory, authorized access recipe and public-package smoke test |

For each deliverable, record `artifact path + commit/hash + commands/results + limitations + owner decision/date`. Keep **implementation complete**, **technically verified** and **owner accepted** separate. This document records no owner acceptance.

## Checks run for this revision

From the repository root, the following are bounded, offline checks. They do not run reconstruction, download data, call a model provider or certify clinical performance.

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

Both commands returned exit 0 on 2026-09-13. Patient-level arithmetic was checked against the committed R3 JSON; no original image reconstruction or new reader study was performed. The review supports the specific corrections above, **not a fully passing suite, clinical superiority, complete reproduction, or independent certification of the benchmark**.
