> **21 September update:** Start with [the focused paper-delivery assignment](HEYANG_NEXT_2026-09-21.md). This page remains the detailed follow-up backlog.

# Review and next steps — Heyang, 20 September 2026

**Read this first.** This is the current ordered assignment, following the format
of [the 8 September review](HEYANG_NEXT_2026-09-08.md). It supersedes execution
priorities in the 8, 13 and 15 September lists and expands today's initial
paper-first handoff. Historical evidence and unresolved scientific concerns in
those records still stand.

**Owner priority: finish `Heyang-paper/` as soon as possible.** Complete the paper
package before starting more agent/UI features or additional experiments. If an
owner-only field blocks finalization, finish all unblocked text and send the
specific blocker; do not wait silently or replace this priority with new work.

## What you finished, and what was merged

Your work through `d515825` is now in `main` via
[PR #26](https://github.com/integritynoble/low_dose_CT/pull/26): task-identity and
invalid-evidence checks, vendor-coverage states, diagnostic receipts, the
prototype verifier and web page, WS-2 prose reconciliation, and the draft
dose–task protocol. Keep those commits; do not redo the original assignments.
The merge also includes the earlier reviewed patient-bootstrap and provenance
repairs. Both GitHub CI workflows passed on the final reviewed candidate.

Local Linux checks: **347 passed / 10 skipped** for scoring plus WS-1 analysis,
and **157 passed** for WS-2. The skips need absent historical session scripts.
R6 log recomparison and paper table freshness passed. These are software checks,
not a new model run, scientific endorsement, native Windows verification, or
confirmation that source images were copied.

The companion agent is integrated through
[ldct_agent PR #1](https://github.com/integritynoble/ldct_agent/pull/1): task-aware
probes, full required-vendor coverage and refusal to call a failed probe enforced.
Its local test run had **53 passed / one conditional skip**. The injected
failed-probe regression passes separately. Both repositories stay separate and
connect through `LDCT_REPO`; the shared core stays a dependency.

## What changed underneath you

- **Skipped checks cannot certify a result.** The verifier now returns INCOMPLETE
  when S3/S4 or required rung checks do not run. A boolean cannot substitute for
  a numeric value in the live comparison. Preserve these fixes.
- **An empty board is NO_CLAIM.** The agent no longer expects a PASS from it.
  The gate audit can pass its software probes while the board has no publishable
  result. Neither state closes the scientific questions.
- **Patient bootstrap replacement is repaired.** Repeated sampled patients must
  repeat their complete blocks, and paired-dose comparisons share the draw.
  The corrected v2 artifacts remain exploratory with three patients; the legacy
  output is retained as history, not valid replacement-sampling evidence.
- **The paper still needs substantive correction.** Tables reproduce, but the
  causal interpretation, tolerance language and reference-environment details
  need task 1 below. A generated table is not a review of the surrounding prose.
- **Your pending list's A-1/A-2 are complete.** The changes described as uncommitted
  in `PENDING_DECISION_LIST_2026-09-20.md` were pushed as `d515825` and merged.
  Merging draft code does not ratify its `[CONFIRM]` defaults or remove DRAFT.

## What to do next, in order

### 0. Sync both repositories and acknowledge the assignment

In the CT checkout, preserve your local work, fetch, then merge `origin/main`
into `heyang` without a force push or history rewrite. In your agent checkout,
merge current `origin/main` into your working branch. Record both resulting
heads and the shared-core version/path. Use the existing authorized core;
its historical GitHub install URL is not a verified installation route.

**Done when:** your reply names both heads, local work not yet pushed, your paper
completion ETA, and any owner input needed. If these instructions conflict with
newer work, identify the exact commit/file rather than overwriting that work.

### 1. P0 — finish `Heyang-paper/` as soon as possible

Work in `Heyang-paper/` from current `origin/main`; merge main into your branch
without rewriting history. First return a short acknowledgement with your
expected completion date and the specific information you still need. Proceed
with all unblocked writing now; do not wait for the broader benchmark project.

1. **Close the environment/provenance gap.** Record both reference and rerun OS,
   GPU, driver, CUDA/cuDNN, Python, PyTorch, NumPy, code/checkpoint/data-manifest
   hashes and commands from original logs. Distinguish recorded facts from
   recollection; if reference details cannot be recovered, state that limitation
   in Methods and notify the owner. Do not invent an environment or claim a new
   independent reproduction from a comparison of existing logs.
2. **Correct the central interpretation throughout the abstract, Results,
   Discussion, conclusion and README.** A bit-identical same-side deterministic
   rerun establishes repeatability in that tested configuration; it does not
   uniquely identify the cause of the reference mismatch or rule out all GPU
   kernel effects. The absolute criteria tested failed; this does not prove
   that no absolute tolerance could pass. The per-metric amendment followed
   observation of the mismatch: label it retrospective, preserve the original
   failure, and do not claim independent/prospective tolerance validation.
   Use “original declared criterion” unless timestamped preregistration evidence
   is actually available. A third environment is optional follow-up, not a
   prerequisite for finishing this bounded Technical Note.
3. **Reconcile every number with the artifact.** Check the comparison count
   using all axes (methods, seeds, doses, metrics): the current TODO's written
   multiplication is inconsistent with its per-method label. Extend the table
   generator where necessary; keep the source artifact and tolerances unchanged.
   Run `python3 Heyang-paper/make_tables.py --check` and
   `python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`.
4. **Close submission metadata with the owner.** Request the author order,
   affiliations, ORCIDs, corresponding author, CRediT and declarations in one
   compact message. Prepare accurate code/data availability text: public code
   does not imply unrestricted image/checkpoint redistribution. The target
   recorded in the repository is Medical Physics, Technical Note; check the
   journal's current instructions when preparing the submission package.
5. **Deliver one consistent package.** Commit manuscript.tex, references.bib,
   generated tables, rebuilt manuscript.pdf, README and a short completion
   checklist with the exact commit, build command and remaining author decisions.
   Remove all resolvable TODOs, check citations/links and PDF layout, and report
   unresolved author-only fields explicitly. Do not submit to a journal until
   the authors approve the final package.

**Done means:** scientifically bounded text, reproducible tables, matching PDF,
complete metadata or a clearly enumerated owner-only blocker list, and a branch
ready for final author review. Software tests alone are not scientific approval.

## Tasks after the paper package is delivered

### 2. P1 — return a native Windows compatibility receipt for both repositories

Run the integrated code on your Windows checkout. Use your normal environment,
record versions, and capture stdout/stderr and exit codes. From the indicated
directories, these commands are shell-neutral:

```text
# low_dose_CT/WS-4_leaderboard
python -m pytest scoring/tests ../WS-1_dataset/analysis/tests -q -rs -p no:cacheprovider

# low_dose_CT/WS-2_framework/pwm_dose_equivalence
# Set PYTHONPATH to src in your shell before running:
python -m pytest -o addopts= tests -q -rs -p no:cacheprovider

# low_dose_CT root
python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check
python Heyang-paper/make_tables.py --check

# ldct_agent root; set LDCT_REPO and RESEARCH_CORE to the actual checkouts first
python -m unittest discover -s tests -v
python -m ldct_agent.cli board
python -m ldct_agent.cli gate-audit
python -m ldct_agent.cli tolerance audit
python -m ldct_agent.cli release-check
```

Use the shell's environment-variable syntax; do not paste a Linux assignment
into PowerShell. Include the actual verdicts, not just zero exit codes. Do not
change expected results to PASS or lower a gate to make the receipt green.

**Done when:** one receipt records exact CT/agent/core heads, OS/Python/package
versions, commands, counts, skip reasons and board/gate/tolerance/release results.
Explain differences from the Linux baseline; a source filename scan is not a
complete privacy/license audit. No available Windows machine means BLOCKED,
not tested. The [agent integration record](https://github.com/integritynoble/ldct_agent/blob/main/docs/CT_INTEGRATION_2026-09-20.md)
contains the reference setup and its limits.

### 3. P1 — make prototype publication states visible and testable

Audit `WS-4_leaderboard/web/`, `scoring/verifier.py`, the CLI and saved-board
receipts together. The UI currently reads board entries without using the
publication status, so a pending receipt can look like a public result.

Add an explicit preview/pending/unverified display for nonpublished or legacy
boards; distinguish NO_CLAIM, missing required strata, INCOMPLETE, rejected and
published states. Keep API fallback a labeled prototype. A published view must
use verified publication evidence from the referee, not a submitter-controlled
flag. Do not invent a release service or deploy the page as part of this task.

**Done when:** fixtures for missing status, pending, missing strata, failed gates,
skipped live execution and a valid publication all produce the intended UI/CLI
state; no skipped/pending case is labeled verified or published. Return commands,
fixture paths and screenshots of the states, with no patient images. Do not
change BandER direction, dose margins or the R6 tolerance to implement this.

### 4. P1 — bind provenance to the evaluated inputs, not only submitted JSON

Review `scoring/verify.py::check_claim_bound_provenance` and every add/save path.
Matching a hash of a submitted manifest or weights-description object proves
internal consistency, not that those bytes were actually evaluated. Likewise,
one patient label somewhere in JSON does not establish slice-to-patient mapping.

Document the trust boundary first. Add evaluator-owned evidence for the actual
model/input manifest, evaluator version and method/task/dose identity. Validate
patient mapping at the slice/result level for a claimed patient bootstrap.
Exercise direct save as well as CLI submission. When trusted evidence is absent,
keep the result unverified/pending instead of certifying it. Local deterministic
fixtures are enough to develop these checks; live S3 still needs its runtime and
authorized data source.

**Done when:** tests reject changed model bytes, changed manifest membership,
wrong method/task/dose binding, missing or inconsistent patient mapping, and a
direct-save bypass; a valid evaluator-produced fixture passes. Tests must show
the adverse outcome before the fix. Return the threat/coverage table and exact
code/fixture heads. Do not describe this as source-data authentication until the
trusted evaluator has actually run at that source.

### 5. P1 — deliver reproducible BANDER diagnostics and the backup receipt

First inventory the evidence already behind your
[14 September reply](HEYANG_REPLY_2026-09-14.md). Recover its driver, parameters,
checkpoint selection, per-patient numeric output and input/output hashes where
available; mark unrecoverable session-only material explicitly. Do not rerun
expensive inference merely to recreate a narrative that already has evidence.
Then complete the outstanding BANDER-2/6 diagnostic controls using the existing
constructors in `bander/control-matrix`, on the authorized image machine. Keep
cases/ROIs matched, preserve negative findings and patient-level dependence,
and report whether energy reflects structure, noise or artifacts within the
limits of the measurements. These are diagnostics, not a clinical threshold
selection or a confirmatory dose–task study; the latter needs the unresolved
protocol decisions first.

Separately, report the status of the already-authorized off-machine substrate
copy and deposit dry run from §§4–4b of
[the 13 September handoff](HEYANG_NEXT_2026-09-13.md). Return a redacted manifest,
file counts/checksums, verification result and dry-run missing/refused list.
Keep share tokens, restricted images and private filesystem identifiers out of
this public repository. Do not claim a copy completed without a checked receipt.

**Done when:** the diagnostic evidence and copy receipt are separate deliverables,
each marked COMPLETE, PARTIAL or BLOCKED with its evidence. If the authorized
machine/destination is unavailable, name the missing prerequisite. Do not mark
scientific acceptance complete from a successful copy or a unit-test pass.

## Not yours to decide alone

Author order, declarations and journal submission need author/owner decisions.
Clinical margins, protocol freeze and statistical guarantees need the named
clinical/statistical collaborators. Dataset rights, new redistribution, study
recruitment, spending and deployment are not authorized by this task list.
Leave unresolved protocol fields and draft semantics explicit; do not batch-ratify
confirmation markers, change registry status or delete tracked weights to make
a checklist look finished. Submit a concrete recommendation if a decision is
needed. Do not start a third-environment GPU study before delivering the paper.

## Where to put your answers, and what to do if you disagree

Commit **`HEYANG_REPLY_2026-09-20.md`** on your branch as the single progress index.
Link detailed logs/artifacts rather than copying them into many handoffs. Use:

| Task | Status | Commit / evidence | Remaining blocker | ETA |
|---|---|---|---|---|
| 0 — sync and acknowledgement | TODO | | | |
| 1 — paper package | TODO | | | |
| 2 — Windows CT + agent receipt | TODO | | | |
| 3 — publication-state UI/CLI | TODO | | | |
| 4 — evaluator-bound provenance | TODO | | | |
| 5a — BANDER diagnostics | TODO | | | |
| 5b — copy/deposit receipt | TODO | | | |

Update when starting, finishing or encountering a blocker. Use IN PROGRESS,
DONE or BLOCKED with evidence; silence and no new remote commit do not establish
inactivity. Ask for owner-only paper information in one compact list and keep
working on the rest. If an instruction is wrong, point to the contradicting
source and propose the correction before doing dependent work. Unlike the
historical September 8 channel instruction, this assignment uses the repository
handoff; delivery through the unconfirmed `BeiTa9` account is not assumed.

## Source checkpoint for this assignment

Checked after fresh fetch on 20 September:

| Repository / branch | Exact head |
|---|---|
| low_dose_CT main | `661943e00997e7ab589f6031d295817c2de31b65` |
| low_dose_CT heyang | `d515825f577c155f03ed91977ac364f8765dbc7c` |
| low_dose_CT bander/control-matrix | `a42ad2703594b4c3a4cd6a02396d1ae444f64dac` |
| ldct_agent main | `c2a75c5953aecd911877f8a667efd9d29a384b3d` |

Open CT PRs #20 (WS-2 prose) and #1/#2 (dependencies) were checked before editing;
this assignment does not duplicate or merge them. No later Heyang push was
visible; local workstation progress and acknowledgement remain unverified.
Read [the integration review](INTEGRATION_STATUS_2026-09-20.md) for the original
heads, repairs and limits. PR #26 subsequently merged that reviewed candidate;
this handoff records the confirmed merged status.
