# Local LDCT task progress — 15 September 2026

This report records work performed on the RTX 5090 workstation against
low_dose_CT main at fb919e1 and ldct_agent main at eb0a364. It is an
implementation and verification record; it does not close a scientific,
clinical, data-rights, or owner decision.

## Completed on this machine

### ldct_agent compatibility and test audit

A fresh full checkout of integritynoble/ldct_agent was run with the local
pillcam_agent shared core and LDCT_REPO pointing to this low_dose_CT checkout.

Command:

    PYTHONPATH=/home/S248103/pwm/pillcam_agent:/tmp/ldct_agent-review-2026-09-15 +      LDCT_REPO=/home/S248103/pwm/low_dose_CT +      python3 -m unittest discover -s tests -p 'test_ldct_*.py'

Result: 49 tests ran, 49 passed, 1 skipped. The skipped test is conditional on
an optional repository fixture. No data or checkpoint was modified.

The agent imports the low_dose_CT WS-4 scoring package rather than copying it.
Its board, paired-comparison, tolerance, gate-audit, and release checks are
therefore connected to the repository's task specification and registry.

### low_dose_CT gate checks

The dependency-free WS-4 scoring modules compile successfully. The three
executable gate probe pairs all behaved as intended:

- pairing validation: valid fixture accepted and malformed patient row refused;
- ROI protocol: valid fixture accepted and non-separating trap refused;
- dose curve: valid fixture accepted and reached/non-lowest trap refused.

The independent agent gate audit reported rungs 1–6 as enforced and exercised
in both directions. Its release check found 827 tracked files and zero
restricted derivatives at main fb919e1.

## Limitations and follow-up

The local system does not have pytest installed, so the repository's pytest
suite was not claimed as run. Python compilation and the available unittest and
gate-probe checks are not a substitute for that suite.

The current board audit reports zero vendor-comparable submission entries in
each vendor group. That makes the by-vendor PASS a vacuous structural result;
it is not evidence that a real submission has passed the trap-rank separation.
Populate and independently verify the intended grouped entries before using
that output as scientific evidence.

The BANDER-2/BANDER-6 measurements still require the authorized imaging assets
and remain assigned to Heyang. No clinical margin, dose-reduction claim, or
field-wide conclusion is asserted here.
