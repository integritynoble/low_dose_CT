# heyang — next steps, updated 15 September 2026

Supersedes the execution portions of HEYANG_NEXT_2026-09-13.md for the tasks
below. This handoff is written against heyang @ 29955a9. The current main is
37b7dec; check both heads before merging. The local verification record is
LOCAL_TASK_PROGRESS_2026-09-15.md.

These are execution assignments, not permission to change a score, tolerance,
clinical protocol, dataset rights, or owner decision. A negative or unresolved
result is a valid result.

## Priority and responsibility

| Priority | Work | Lead and review | What comes back |
|---|---|---|---|
| P0 | Reconcile heyang with current main | Heyang; independent Linux check | Exact merge/rebase commit, preserved R6 history, test results on Windows and LF/Linux |
| P0 | Exercise invalid-evidence and publication gates | Heyang/benchmark engineer; maintainer review | Positive/negative fixtures, receipt-vs-publication behavior, exact logs |
| P1 | Complete BANDER-2 and BANDER-6 | Heyang on the machine holding authorized images; independent evaluator | Per-patient control measurements, uncertainty, hashes, commands, honest negative findings |
| P1 | Reproduce the ldct_agent compatibility audit | Heyang; maintainer review | Agent commit, 49-test baseline or changed result, gate/release audit and drift list |
| P1 | Draft one frozen dose–task protocol | Physicist, radiologists, statistician and Heyang | Versioned protocol skeleton with unresolved owner fields marked explicitly |

## 1. Reconcile before adding new measurements

Fetch origin/main and origin/heyang, then merge or rebase onto the current
main. Preserve the accepted main R6 per-metric comparison and its route-A
evidence; retain the historical absolute-tolerance result as superseded.
Before reporting success, verify the generated comparison and its generator
agree, and report:

    git rev-list --left-right --count origin/main...HEAD
    python3 -m pytest WS-4_leaderboard/scoring/tests

The repository's current Linux machine lacks pytest, so state that limitation
if it remains true. Do not turn a missing test dependency into a pass.

## 2. Repair and exercise invalid-evidence acceptance

Complete the checks named in HEYANG_NEXT_2026-09-13.md section 3c. The gate must
refuse wrong task identity, non-finite values, empty required coverage, and
evidence that does not support the claim attached to it. Keep a submission
receipt separate from publication approval.

Add one valid fixture and one invalid fixture for each case. Show that the
valid fixture is accepted and every invalid fixture is rejected before a board
write. Include the exact commit and fixture logs.

## 3. BANDER-2 and BANDER-6: data-dependent measurements

Use the frozen protocol and existing checkpoints on the same real slices and
tissue ROIs as the committed R3 artifact, then repeat the control comparison
for the four LIDC vendor groups. Use ctformer.pt where the frequency artifact
requires it. Emit per-patient values, patient-level uncertainty,
source/checkpoint hashes, and exact commands.

Do not select a new threshold from these measurements. Do not call BandER
clinical benefit. If the controls fail to separate methods, record that
negative result and preserve the outputs.

## 4. Reproduce and extend the ldct_agent audit

Run the independent agent against the current merged checkout. Confirm that it
still imports the low_dose_CT WS-4 scoring package rather than copying it. Run
the agent's unittest suite, gate-audit, board, and release-check.

The 15 September workstation baseline was 49 tests passed and 1 skipped,
scoring probes accepted valid fixtures and refused invalid fixtures, and the
release scan found zero restricted derivatives. Recheck these claims after
merging; report any changed count, skipped dependency, vacuous board group, or
repository drift rather than smoothing it away.

## 5. Prepare a dose–task protocol, without choosing owner decisions

Draft a versioned protocol for one claim: intended task and population, dose
quantity and generation, adequate reference, strong comparators, primary
endpoint and direction, required strata, protected final data, adaptation
rules, and resource constraints.

Clinical and statistical margins, adequacy floors, and final-test ownership are
unresolved until the named collaborators decide them. Mark those fields
unresolved; do not invent values or claim dose reduction.

## Reporting contract

For every section return claim + protocol version + input/model/code hashes +
commands/results + uncertainty + required-stratum coverage + independent check +
limitations + decision/date. Keep implementation complete, technically
verified, scientifically supported, externally used, and owner accepted as
separate statuses.
