# heyang — next steps, updated 14 September 2026

Supersedes [`HEYANG_NEXT_2026-09-08.md`](HEYANG_NEXT_2026-09-08.md). Original assignments were
written against `main` @ `72ba063`; the 14 September scientific and implementation review used
`main` @ `646daa6c3a01ab807dc729982115c57bdec3ff3a`. Branch divergence, test counts and merge conflicts
below are historical observations: recheck them on the commits you actually merge.
The 14 September audit used source inspection and bounded helper/script checks. Its selected pytest
tests could not collect because the audit interpreter lacked pytest; it established no current
full-suite pass and did not rerun image experiments.

**14 September update.** The review of [`FIELD_COLLAPSE_PROBLEMS.md`](FIELD_COLLAPSE_PROBLEMS.md)
found that fixing its seven benchmark problems does not by itself establish a useful dose reduction,
a best reconstruction method, or field-wide adoption. This file now includes the additional work and
acceptance criteria in §§3c–3e. They are proposed tasks, not completed experiments or permission to
change a score, tolerance, registry status or clinical protocol. No new clinical study or spending
commitment is made here.

> **Please read this file rather than GitHub issues.** Six issues (#3, #4, #5, #22, #23, #24) were
> opened and assigned to the `BeiTa9` account between 4 and 13 September. That account has shown no
> activity since June, so the assignments almost certainly never reached you. Everything actionable
> from all six is reproduced here. That was our mistake in channel, not yours — the file convention
> this project has always used is the one that works, and we left it.

---

## Priority and responsibility

| Priority | Work | Lead and review | What comes back |
|---|---|---|---|
| P0 | Existing merge/rebase repairs (§§1–2) | Heyang; independent Linux check | Exact commits, current test results and preserved R6 amendment history |
| P0, in parallel | Preserve the authorized dataset substrate (§§4–4b) | Data operator; owner for any access/rights decision | Copy manifest and source checks; restricted images remain under the stated controls |
| P0 | Repair invalid-input and publication checks (§3c) | Heyang/benchmark engineer; maintainer review | Positive/negative integration tests and evidence-to-claim validation |
| P0 | Correct framework definitions (§3d) | Framework author and statistician; Heyang supplies implementation mapping | Corrected claims, counterexamples and estimator/credential checks |
| P1 | Complete the existing BandER control work (§3b) | Heyang on the machine holding the images | Same-case/ROI measurements, patient-level uncertainty, honest negative results |
| P1 | Freeze and test a dose–task claim (§3e) | Physicist, radiologists, statistician and independent evaluator; engineer implements the frozen protocol | Strong-comparator dose curves, protected final test and supported/unsupported conclusions |
| P2 | Establish external decision value (§3e) | Maintainer and independent groups | Reproduction, challenges and actual use; adoption is measured rather than promised |

The merge repairs remain the first code dependency. They do not validate the scientific meaning of
BandER. Clinical margins and mathematical guarantees need the named collaborators; they are not
questions Heyang should settle by selecting a convenient threshold.

---

## 1. Two failing tests block the merge — fix these first

On `heyang` @ `2b5e379`: **2 failed, 124 passed, 10 skipped**.

```
scoring/tests/test_trap_numbers.py::test_trap_metrics_still_match_their_source_run
scoring/tests/test_trap_numbers.py::test_vendor_trap_metrics_still_match_their_source_run
```

**The data is completely fine.** We diffed both source runs between `main` and `heyang`: every
measured value, `updated_at` and key set is identical, and the parsed JSON compares equal. Nothing
about the trap moved. This is a line-ending trap, not a science problem:

| file | LF (Linux/CI) | CRLF (your Windows checkout) |
|---|---|---|
| `aapm_r3_roi_detectability.json` | `9987864a…` | **`49dddf9d…`** ← the constant in `leaderboard.py` |
| `aapm_lidc_cross_vendor_spread.json` | `c4364074…` | **`5b67f1f9…`** ← same |

Both constants are the **CRLF** hashes. Git converted line endings on checkout, the hash was taken
of the on-disk bytes, and those constants can now never match on any LF machine. The root cause is
that there is **no `.gitattributes` at the repo root**, so a byte-level hash of a text file is
platform-dependent and this will recur on the next provenance hash anyone adds.

Three parts, all needed:

1. Repo-root `.gitattributes`:
   ```
   *.json    -text
   *.sha256  -text
   ```
2. Restore the **LF** hashes in `leaderboard.TRAP_SOURCE` and `VENDOR_TRAP_SOURCE`
   (`9987864a…`, `c4364074…`).
3. Make the check line-ending-proof — normalise `\r\n` → `\n` before hashing, or hash the
   recanonicalised JSON rather than raw bytes. Part 1 stops it happening; part 3 stops it mattering.

**Done when** `python3 -m pytest scoring/tests` is green from the same commit on **both** your
Windows checkout and a Linux one. Please confirm both — a one-sided pass is what produced this.

The test did its job here. It refused to let the board's trap drift away from the run that produced
it; the failure is the mechanism working, not misfiring.

---

## 2. Rebase onto `main` in the same pass

`heyang` is **19 ahead** of a `main` that has moved **10+** since your merge base (`dd8e395`) — the
exact count keeps rising, so check it rather than trusting this line:

```bash
git fetch origin && git rev-list --left-right --count origin/main...origin/heyang
```

Four files conflict, all R6:

```
DIRECTOR_DECISIONS.md
WS-1_dataset/R6_recalc/R6_recalc_report.md
WS-1_dataset/R6_recalc/results/comparison_full764.json
WS-1_dataset/R6_recalc/R6独立复算操作指南.md
```

### ⚠️ `comparison_full764.json` — take `main`'s version, not yours

| | `main` | `heyang` |
|---|---|---|
| `overall` | **PASS** | FAIL |
| per-model | all five PASS | red_cnn / ctformer / corediff FAIL |
| criterion | per-metric, superseded state recorded | `tolerance_kind: absolute`, 1e-6 |

`main` carries the route (b) outcome the Director decided (`b472707`): the per-metric relative
criterion, verdict flipped to PASS and **derived rather than asserted**. Your branch still holds the
superseded absolute-1e-6 FAIL. **Keeping your side would silently revert that decision.**

Your ~48 GPU-hours are not lost by taking `main` — `routeA_rerun_evidence` and
`per_metric_declaration` are both preserved in it. The owner cited the route (a) finding when choosing
route (b); retaining it documents the decision without establishing the cause of the mismatch.

During a rebase `--ours` means `main` and `--theirs` means your own commits — inverted from normal
usage, which is exactly how people take the wrong side without noticing. So verify rather than trust
the flag:

```bash
git checkout --ours WS-1_dataset/R6_recalc/results/comparison_full764.json
python3 -c "import json;d=json.load(open('WS-1_dataset/R6_recalc/results/comparison_full764.json'));print(d['overall'],'|','routeA_rerun_evidence' in d)"
# expect: PASS | True        (if it prints FAIL, you took the wrong side)
```

Better still, **regenerate** rather than hand-merge — an 800-line generated JSON should not be
reconciled by hand. Note the two sides carry different generators, and after the rebase you will have
both:

| script | on | role |
|---|---|---|
| `compare_full764.py` | `heyang` only | the original absolute-tolerance comparator |
| `recompare_per_metric.py` | `main` only | **produced the PASS verdict** under the per-metric criterion |

So regenerate with **`recompare_per_metric.py`** — it is the one whose output `main` carries. Running
`compare_full764.py` would reproduce the original absolute-1e-6 FAIL. Preserve that historical
result, but do not substitute it for the owner's amended comparison artifact during this merge.
The amended comparator evaluates committed logs; running it is not a fresh prediction reproduction.

### The other three

Prose — merge them, do not pick a side. `main` has the route (b) amendment, yours has the route (a)
run detail. Preserve the sequence: the original declared criterion failed → route (a) tested
within-recalculation determinism → the reference mismatch remained → the owner amended the
per-metric criterion. The no-difference rerun does not uniquely identify cuDNN or any other cause
of the reference mismatch. The tolerance amendment was made **after observing the mismatch**;
do not describe it as a prospectively satisfied original criterion. `DIRECTOR_DECISIONS.md` is the Director's file: take `main` and raise disagreements rather
than editing it inside a rebase.

### Before pushing

- [ ] Suite green on **Linux**, not only Windows
- [ ] `overall` is `PASS` and `routeA_rerun_evidence` present
- [ ] `git rev-list --objects heyang | grep -c test_img/L506` → `0`
- [ ] Record current full-suite counts and reasons for skips on both commits. The earlier
      `main` count was **108 passed / 10 skipped**; that is a historical baseline, not a current
      acceptance target. Missing scientific evidence cannot become a pass through a skip.

Force-pushing your own branch after a rebase is expected and fine. Do not force-push `main`.

---

## 3. Two questions only you can answer — a comment is enough, no runs

The current evidence leaves both metric direction and diagnostic interpretation unresolved:

- **Current direction (higher better):** the direction-analysis script prints noise-control values
  near 183 and 1598, but these are **hard-coded values** in
  [`scripts/prepare-bander-direction-fix.py`](scripts/prepare-bander-direction-fix.py), not an
  image experiment rerun by the 14 September review. Recover the generating artifact and input/ROI
  provenance before treating those numbers as verified measurements. Descending energy can reward
  added high-frequency content; the real-anatomy controls in §3b test this directly.
- **Candidate symmetric direction (`|log BandER|`):** recomputing from the committed R3 means puts
  blur first on AAPM, since 0.432 is closer to 1 than CTformer's 6.735. Blur also stops being last in
  two of five reported groups. This reordering is reproducible, but it validates neither direction
  as a diagnostic measure. Matching reference energy does not establish correct lesion content.

Metric validity and software validation are separate problems. The ranking helper can implement an
ordering correctly while the index fails the clinical task, and §3c also identifies actual invalid-input
acceptance gaps. Smoothing is not automatically clinically harmful: task-beneficial methods must
not be rejected solely for smoothing or for lacking learning. [AAPM TG 233](https://www.aapm.org/pubs/reports/RPT_233.pdf)
explains the need for task-specific evaluation and supplies no universal BandER pass threshold.

**(a)** The three displayed learned methods have AAPM ROI BandER around 3.9–6.7 relative to the
full-dose reference. Please describe whether the output images suggest residual noise, sharpening,
ringing or another source of texture. Record these observations as hypotheses to test with the
controls, not as a mechanism established by appearance alone.

**(b)** In `detectability-freq-v1` **as you designed it**, was "higher ROI BandER is better" intended,
or was *closer to the full-dose reference* the intent, with the trap merely sitting at the low end?
The leaderboard's descending sort is not yours — that is `leaderboard.py`, written elsewhere. If the
intent was the second, the leaderboard has been reading your index backwards since it was wired in.

**"I don't remember, it wasn't a deliberate choice" is a perfectly good answer** — better than a
reconstructed rationale. Your answer establishes the intended definition; experimental checks
are still needed to establish which interpretations the data support. Reply in a commit message, a file, or however suits you.

---

## 3b. Two measurements only your machine can do — BANDER-2 and BANDER-6

**Added 13 September, after the RTX 5090 handed this back.** The assignment originally went there on
the assumption that the AAPM and LIDC trees were on that workstation. They are not — the R3
artifact's own `tree` field and all 25 lines of `WS-1_dataset/R6_recalc/hashes/aapm_hashes.txt` point
at `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pipelines\_runtime\aapm_tree_v1`, which is **your
machine**. That was our error, caught by the operator. So these two land with you, because the data
is with you.

Both are **CPU work** — deterministic image operations and a few lines of numpy. If you find yourself
waiting on a GPU, something is mis-scoped.

### Start from the branch — do not rewrite it

```bash
git fetch origin && git checkout bander/control-matrix    # a42ad27, off main @ 72ba063
```

`scripts/bander_controls.py` already implements the five controls as pure functions of the full-dose
image — blur, additive Gaussian noise at a fixed seed, unsharp oversharpening, truncated-frequency
ringing, and lesion erasure inside a disc — with 10 passing unit tests. **BANDER-1 is done. Do not
redo it.**

### BANDER-2 — the controls on the real slices

Compute ROI BandER for every control on the **same slices and the same tissue ROIs** the committed R3
artifact used, with the protocol code unmodified. The point is a table of control-vs-BandER that is
directly comparable to the committed real-method values. Then repeat on the LIDC four-vendor slices
(that part is BANDER-4) so the answer is not one cohort.

**Reported branch result, on a phantom rather than these patient slices:** the tested directions
(raw descending, `|log B|` and `|B-1|`) did not separate all five controls. Lesion erasure reportedly
leaves whole-region BandER near 0.999 while the lesion-local value changes from 0.9992 to 0.0997;
the changed disc covers 317 of 65,536 pixels. Retain the branch commit, code, logs and measurement
provenance with that claim. This is evidence to investigate spatial aggregation, not a proof about
every possible scalar transform. The 14 September review did not rerun that branch experiment.

Confirm or refute the reported behavior on the specified patient anatomy. A negative result is a
complete answer. Include signal-present and signal-absent cases, lesion-local and whole-region
measurements, and patient-level uncertainty. Report actual independent patient counts; additional
slices and repeated seeds do not create additional patients. Diagnostic validity still requires the
prospective task evidence in §3e, including checks for useful methods wrongly rejected by the gate.

### BANDER-6 — is the excess high-frequency energy a simulator artefact?

This comparison asks whether the elevated high-frequency energy differs across cohorts. The
existing PSNR table at nominal dose ratio 0.25 is:

| method | LIDC project-simulated | AAPM challenge noise-inserted | difference | BandER on AAPM |
|---|---:|---:|---:|---:|
| **blur control** | 41.65 | 41.63 | 0.02 dB | 0.432 |
| RED-CNN | 53.65 | 41.20 | 12.45 dB | 3.876 |
| LEARN | 57.06 | 41.61 | 15.45 dB | 3.854 |
| CTformer | 55.32 | 39.59 | 15.73 dB | 6.735 |

The AAPM patient quarter-dose reference was generated by **projection-domain noise insertion**, not
by a separate physical low-dose patient acquisition; see the [challenge description](https://www.aapm.org/grandchallenge/lowdosect/).
Use this label in new tables and reconcile contradictory `real QD`/physical-acquisition wording in
active manuscripts and validation notes. Preserve historical raw records with a correction note.

The nearly equal blur PSNR does not establish that blur alone transfers successfully. The comparison
changes cohort, anatomy/protocol mix, vendor and dose-generation process; confirm consistent PSNR
normalization, reconstruction settings and input access before interpreting the difference. These
point estimates do not isolate a simulator effect or prove diagnostic performance.

**Measure BandER per method on LIDC-simulated and AAPM noise-inserted slices side by side, using
one fixed measurement protocol and each cohort's matched controls.** Preserve the patient-level
outputs, identify the cases/ROIs and report which differences are confounded by cohort or protocol.
A larger excess on AAPM would be consistent with a transfer problem but would not identify its cause;
similar excess in both cohorts would weaken that particular explanation. Report residual-noise,
sharpening and simulator-related explanations as hypotheses unless an additional controlled
experiment distinguishes them. Either result is useful evidence.

### Rules

Do **not** tune a control until it fails, drop one because it is inconvenient, or search over scores
until one passes and report only that. And separation from a cheat is not evidence the index tracks
diagnostic content — BandER has still never been checked against a reader.

**Do not change any scoring rule, gate, tolerance or registry status.** This produces evidence for a
decision the Director has not taken. Code belongs on the branch; keep raw logs, images and data on
your machine.

**This measurement work follows §§1–2.** The merge comes first; the new verifier and framework
repairs in §§3c–3d are also prerequisites for treating an eventual result as certified evidence.

---

## 3c. Fix acceptance of invalid evidence — engineer work, then maintainer review

**Added 14 September; observations at `646daa6`.** Source inspection and direct in-memory probes found:

| Current helper behavior | Required regression case |
|---|---|
| `check_paired_submission` accepts an unrelated task label | Reject a task/protocol identity that does not match the versioned claim |
| The same helper accepts NaN and nonnumeric strings in expected metric fields | Reject nonfinite or wrongly typed metrics before ranking or statistical decisions |
| `trap_rank_report` can return `PASS` for a NaN method | No invalid comparison may authorize publication |
| A trap-only board returns `PASS` with zero comparisons | Return an explicit no-claim/unverified outcome; do not publish it as verified comparison evidence |
| Group checks enumerate only groups present in the submission | Check against the required-stratum manifest; missing groups remain unverified |
| CLI submission saves and prints `accepted` without the publication assertion | Separate receipt, preserved diagnostic evidence and approved publication |

Source: [`verify.py`](WS-4_leaderboard/scoring/verify.py),
[`leaderboard.py`](WS-4_leaderboard/scoring/leaderboard.py),
[`cli.py`](WS-4_leaderboard/scoring/cli.py). These are reproduced helper/source findings, not a claim
that a live website published invalid results. The registry load/save helpers also ignore the error
list returned by `validate_registry`; surface those failures rather than treating a well-formed-looking
status record as proof that its check ran.

**Heyang/engineer deliverable:** bind every claimed result to the declared task/protocol, input/data
manifest, model/weight and evaluator versions; validate finite typed metrics and complete required
coverage; enumerate every actual publication path. Add end-to-end positive and negative fixtures:
a valid result can reach approved publication, while wrong-task, missing-control, invalid-number,
missing-stratum and insufficient-evidence results cannot. Preserve their failed diagnostic records.
Every mandatory gate needs exercised positive and negative cases; omitted evidence is unverified.

A `heldout` container/path check is not an independent hidden-test service. Document which access,
execution and publication controls are implemented and which remain planned. Obtain maintainer
review for the publication-state/schema changes. Do not change the chosen metric, its direction,
clinical threshold, existing R6 tolerance or registry completion status as part of this repair.

**Done when:** exact commit + runnable fixtures + current integration results demonstrate valid
publication and rejection of each invalid case, and claim/evidence identity and required coverage
are checked. This closes an engineering defect; the metric still needs task validation.

## 3d. Correct framework claims — framework author and statistician lead

**Added 14 September.** The [current WS-2 manuscript](WS-2_framework/paper_draft/manuscript.tex)
says its per-patient condition implies aggregate equivalence. That implication is false as written.
Let the patient performance difference be 0 for 95% of patients and −1 for 5%. With margin 0.02,
`Pr(abs(difference) < 0.02) = 0.95`, so the stated per-patient condition holds. But the absolute
population mean difference is 0.05, outside the aggregate margin. The counterexample uses bounded
scores; no extreme unbounded tail is required.

The framework author and statistician should reconcile the definitions, proofs, estimator and
credential semantics. Heyang should map the corrected claims to the implementation and supply
adversarial cases, rather than independently choosing new scientific guarantees. Separate the
permitted patient exception fraction from the statistical error probability. Treat aggregate
performance, important patient/subgroup failures and uncertainty in their estimates as separate
claims; cohort ROC AUC is not an undefined per-patient score to average.

Also reconcile the CT physical-validation assertion in
[`predicted_vs_measured_dose.md`](WS-2_framework/theory/proofs/predicted_vs_measured_dose.md)
with the AAPM noise-insertion provenance. That reference alone cannot certify simulator-to-physical
patient-acquisition equivalence.

**Done when:** the false implication and related prose are corrected; independent statistical review
confirms the chosen estimands and assumptions; estimator/credential checks cover equivalence
boundaries, clinically relevant alternatives, patient/reader dependence, selection/multiplicity and
false-PASS behavior. Passing unit tests or recomputing a credential JSON does not by itself establish
statistical coverage or clinical validity. This review has identified the defect; it has not repaired
the framework implementation.

## 3e. Define the scientific result that would make this benchmark decisive

**Added 14 September.** Treat “domain collapse” as a goal of settling specified LDCT claims with
independent evidence. The [WS-3 plan](WS-3_reference_method/README.md) deliberately targets an
improvable top-quartile reference. A trustworthy benchmark can still find that no tested method
achieves a useful dose reduction; an operational leaderboard does not entail a breakthrough or adoption.

### First freeze one claim, with the clinical and statistical collaborators

Record the task/anatomy, population, acquisition settings, dose quantity and generation method,
reference, comparator versions, raw-projection versus image-only access, training/adaptation data,
compute limits, endpoints, margins, required strata, sampling/power plan and analysis. These choices
must precede confirmatory testing. No universal BandER multiplier, patient count or clinical margin
is adopted here.

The required outcomes are:

1. **A meaningful dose–task result against strong alternatives.** Evaluate prespecified dose levels
   against an adequate named reference and strong accessible classical/iterative, learned and
   clinically relevant configurations. Separate unequal input-access and resource tracks; disclose
   missing competitors. For a dose-reduction claim, dose must actually be lower than the reference
   in the declared quantity, with uncertainty where relevant. Require the prespecified diagnostic
   noninferiority criterion, any absolute adequacy floor and critical-error limits to pass. Keep
   fidelity and cost alongside task performance. Use two-sided equivalence only for a two-sided
   closeness claim; a superior method can fail equivalence without being worse.
2. **A protected independent final evaluation.** Freeze models and thresholds and reserve final
   patient/source-disjoint data from metric design, tuning, control selection and repeated leaderboard
   feedback. Include the required external institutions/protocols and relevant patient strata.
   Record training-data overlap and missing coverage. [Adaptive leaderboard research](https://proceedings.mlr.press/v37/blum15.html)
   explains why hidden labels alone do not prevent test adaptation. Plan selection/error control
   before choosing a winning method or dose from many candidates.
3. **Evidence about important failures.** Include small/low-contrast lesions, signal-absent cases,
   erased or fabricated structures and measurement bias. Check task-beneficial methods wrongly
   rejected as well as harmful ones admitted. Validate uncertainty for the claimed event and at a
   defined review/referral workload; pixel-error correlation is insufficient. Use blinded,
   appropriately analyzed reader studies for reader-performance claims. These studies require the
   named collaborators and appropriate authorization; they are not an instruction to acquire new
   patient scans or expose patients to repeat radiation merely for a paired dataset.
4. **Independent reproduction and demonstrated external use.** Another operator must reproduce the
   supported decision from authorized inputs. Independent teams must be able to challenge it with
   credible alternatives under stable rules. Publish unresolved comparisons, failures, costs,
   corrections and appeals. Measure actual external use; citations, registry entries, visibility
   and submission counts alone do not establish decision value or guarantee adoption.

**Report the lowest tested dose supported by the evidence**, with uncertainty and the supported
population/protocol scope. A lower-dose failure or inconclusive interval does not establish a physical
minimum, and interpolation or monotonicity requires justification. A claim of near-optimality would
additionally need a valid task-specific information bound under explicit assumptions; failure of the
currently tested algorithms supplies no such bound. Different populations can legitimately yield
different rankings; [challenge-ranking research](https://arxiv.org/abs/1806.02051) motivates checking
whether a claimed decision is stable within its stated scope.

### Completion record

For each claimed outcome return:

`claim + protocol version + input/model/code/evaluator hashes + commands/results + uncertainty + required-stratum coverage + independent check + limitations + decision/date`.

Keep **implementation complete**, **technically verified**, **scientifically supported**, and
**externally used** separate. Valid possible outcomes include a supported benefit, a supported
limitation, equivalence/noninferiority under the specified rule, or an unresolved comparison. Do not
change the criterion on the same final test until a favorable outcome appears. Completion of these
outcome tests could make the benchmark a strong reference within its scope; it cannot guarantee
that all low-dose CT research is settled.

---

## 4. The deposit exists on one machine — please make a copy

`deposit_procedure.md` said to pull the built records from `gs://low-dose-ct/pwm_ldct_v0_5`. **That
path does not exist**; the whole bucket is 96.8 KiB. None of the three visible buckets holds
`annotations/`, `sim_lowdose/lidc/`, `metadata/`, `splits/` or `deident_audit.jsonl`.

So the v0.5 dataset appears to exist **only on your workstation**. A disk failure there loses the
release and the dataset paper's substrate with it. **An off-machine copy is the cheapest insurance in
the project** — not the formal deposit, just a copy that is not on that one disk.

When convenient, also run:

```bash
python3 WS-1_dataset/physionet_listing/stage_deposit.py \
    --source <root holding annotations/ sim_lowdose/ metadata/ splits/ deident_audit.jsonl> \
    --out pwm_ldct_v0_5_deposit --dry-run
```

It copies nothing in dry-run mode and lists every expected part it cannot find, which tells us whether
the deposit is assemblable before a submission date is promised. If it finds DICOM, `LNNN_*.npy/npz`
or harmonized AAPM/Mayo HDF5 it **refuses and stages nothing** — deliberate, so a DUA breach cannot
pass silently.

---

## 4b. Where to put the copy — the OneDrive folder, 14 September

The owner has shared a OneDrive folder with you over Teams for exactly the copy section 4 asks for.
The link is in that Teams message and deliberately **not** written here, because this repository is
public and the share token would be readable by anyone.

**What should go in it.** The v0.5 substrate that currently exists only on your workstation:

    annotations/          including lidc_majority_vote/ and raw_per_reader/
    sim_lowdose/lidc/
    metadata/
    splits/
    deident_audit.jsonl

That is 364 files by the R6 manifest — 50 `.h5`, 300 json, 8 logs, 4 txt — and it is the thing a disk
failure would cost us.

**What should not go in it.** The harmonized AAPM/Mayo HDF5 under `aapm_tree_v1` — the ten
`aapm-00NN_*_fd.h5` full-dose arrays — along with any DICOM or `LNNN_*.npy/npz`. Those are the same
three classes `stage_deposit.py` refuses to stage, and the refusal is deliberate so that a DUA breach
cannot pass silently. A folder shared by link is a redistribution channel, so putting them there does
by hand what the deposit tool is written to prevent. This repository already rewrote its own history
in September to remove DUA-restricted Mayo arrays; the copy should not reintroduce the problem in a
different place.

If the owner decides the AAPM tree must travel anyway, that is his call to make explicitly, and the
share should be restricted to named people rather than anyone-with-the-link before it does.

**For BANDER-2 and BANDER-6, nothing needs to travel at all.** Both run on your machine against the
slices already there, and what the repository needs back is a table of numbers, not pixels. Upload the
results and a short note on what you found; a negative result is a full answer. That supplies the
requested real-anatomy control evidence without moving restricted arrays. It advances
[`FIELD_COLLAPSE_PROBLEMS.md`](FIELD_COLLAPSE_PROBLEMS.md) §1; full closure still needs the
independent task validation and uncertainty specified there and in §3e above.

---

## 5. Things that changed under you

- **The repository is public** as of 13 September. If you have a clone from before **5 September**,
  please **re-clone rather than pull**: eight Mayo-derived `L506_*.npy` files were removed from git
  history entirely on the 5th, and a hard reset does not delete objects a clone already holds. See
  [`HEYANG_RECLONE_2026-09-05.md`](HEYANG_RECLONE_2026-09-05.md).
- **CoreDiff is un-vendored.** Upstream carries no licence, so publishing a copy was not ours to do.
  `vendor/CoreDiff/fetch.sh` retrieves it. `corediff_wrapper.py` raises a message naming the script if
  it is missing. Every other baseline is unaffected.
- **R6’s committed log-comparison verdict is PASS** under the amended per-metric criterion
  (route (b)) — see §2. This is not a new independent input-to-prediction reproduction certificate.
- **WS-2 prose reconciliation** (#4) is still open and still needs no new experiments; the two false
  claims in it (the PET data claim, the PyPI/readthedocs URLs) were already fixed on `main`.

---

## What the earlier work establishes

The route (a) rerun reported no same-side differences (`n_diffs = 0`) under the tested deterministic
configuration. Preserve those logs and the reported compute cost alongside the original reference
mismatch. That observation narrows the reproduction investigation but does not uniquely establish
its cause or prove that bitwise agreement across environments is impossible.

The owner’s route (b) tolerance amendment followed the observed mismatch. Preserve the original
failure, the rationale and the amended criterion; the resulting log-derived PASS should be labeled
accordingly. A fresh input-to-prediction reproduction by a separate operator is an additional result.

The patient-level bootstrap’s refusal on files without a `patient_id` vector is useful: it prevents
silently substituting slice-level samples for independent patients. Recovering the map and using
appropriate clustered uncertainty remains the next evidence step.
