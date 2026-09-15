# Heyang — execution handoff, 15 September 2026

This handoff is written against origin/heyang at 29955a9. The current
repository main is at fb919e1; it has moved independently since this branch
was last reconciled. These are bounded engineering and measurement assignments.
They do not authorize changing a score, tolerance, clinical protocol, dataset
rights, or owner decision.

## P0 — reconcile the branch without losing the accepted R6 record

Rebase or merge this branch onto the current main, preserving the main version
of the per-metric R6 comparison and its route-A evidence. Preserve the
historical absolute-tolerance result as a dated superseded artifact. Resolve
the four R6 files deliberately, then report:

- exact source heads and the chosen merge/rebase commit;
- git rev-list --left-right --count origin/main...HEAD;
- the full relevant test result, including any collection skips or missing
  dependencies;
- whether the same commit passes on your Windows checkout and an LF/Linux
  checkout.

Do not report the branch as integrated until the generated comparison and its
generator agree with the accepted PASS artifact.

## P0 — close the evidence-integrity gap in WS-4

Implement the invalid-evidence and publication checks described in
HEYANG_NEXT_2026-09-13.md section 3c. Add positive and negative fixtures for
wrong task identity, non-finite values, empty required coverage, and evidence
that does not support the claim it is attached to. Keep submission receipt
separate from publication approval. The result must include the exact commit,
commands, and fixture logs. A green test suite alone is insufficient if the
invalid fixtures are never shown to fail.

## P1 — complete BANDER-2 and BANDER-6 on the authorized machine

Using the frozen protocol and the existing checkpoints, measure the controls on
the same real slices and tissue ROIs as the committed R3 artifact, then repeat
the control comparison for the four LIDC vendor groups. Use ctformer.pt where
the frequency artifact requires it. Emit per-patient values, patient-level
uncertainty, source/checkpoint hashes, and the exact command line. If the
controls do not separate the methods, record that negative result. Do not
reinterpret BandER as clinical benefit or choose a new threshold from these
measurements.

## P1 — audit the ldct_agent repository against the benchmark contract

Review integritynoble/ldct_agent at its current default-branch head against the
schemas and gates in this repository. Map each CLI/record/bench check to the
corresponding low_dose_CT policy, identify drift or checks that can accept
invalid evidence, and add focused tests or a documented gap list. Keep the
repositories separate unless a maintainer explicitly approves a dependency or
synchronization change. Return exact commits, test commands, and any remaining
incompatibilities.

## P1 — prepare, do not invent, the dose–task decision protocol

Draft a versioned protocol skeleton for one dose–task claim: intended task and
population, dose units and generation, adequate reference, strong comparators,
primary endpoint and direction, noninferiority or adequacy margins supplied by
the named clinical/statistical owners, required strata, protected final data,
and resource constraints. Mark owner decisions and missing collaborators as
unresolved; do not select clinical margins or claim dose reduction.

## Reporting contract

For every assignment return claim + protocol version + input/model/code hashes +
commands/results + uncertainty + required-stratum coverage + independent check +
limitations + decision/date. Keep implementation complete, technically
verified, scientifically supported, externally used, and owner accepted as
separate statuses.
