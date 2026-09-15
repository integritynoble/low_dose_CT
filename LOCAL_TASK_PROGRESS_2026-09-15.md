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

    PYTHONPATH=/home/S248103/pwm/pillcam_agent:/tmp/ldct_agent-review-2026-09-15 LDCT_REPO=/home/S248103/pwm/low_dose_CT python3 -m unittest discover -s tests -p 'test_ldct_*.py'

Result: 49 tests ran: **48 passed, 1 skipped**. The earlier report incorrectly
counted the skipped test as passed. A verbose repeat identifies the skip as
`test_rung_7_cannot_be_closed_while_its_own_audit_reports_a_concern`, skipped
because the current registry passes the audit, not because a fixture is missing.
No data or checkpoint was modified.

The agent imports the low_dose_CT WS-4 scoring package rather than copying it.
Its board, paired-comparison, tolerance, gate-audit, and release checks are
therefore connected to the repository's task specification and registry.

### low_dose_CT gate checks

The dependency-free WS-4 scoring modules compile successfully. The three
executable gate probe pairs all behaved as intended:

- pairing validation: valid fixture accepted and malformed patient row refused;
- ROI protocol: valid fixture accepted and non-separating trap refused;
- dose curve: valid fixture accepted and reached/non-lowest trap refused.

The separate agent gate audit reported rungs 1–6 as enforced and exercised
in both directions using its built-in probes. This does not establish full
adversarial coverage or independent scientific validation. Its release check
found 827 tracked files and zero matches to its restricted-path patterns at
main fb919e1. That check scans tracked paths, not Git history or data rights.

## Limitations and follow-up

The system Python used in the original check lacked pytest. On continuation,
the existing `/home/S248103/pwm/.venv-ldct-integration/bin/python` was located
and used to run the scoring suite. The original check remains limited as
reported; the follow-up below records the additional tests.

The current board audit reports zero vendor-comparable submission entries in
each vendor group. That makes the by-vendor PASS a vacuous structural result;
it is not evidence that a real submission has passed the trap-rank separation.
Populate and independently verify the intended grouped entries before using
that output as scientific evidence.

The BANDER-2/BANDER-6 measurements still require the authorized imaging assets
and remain assigned to Heyang. No clinical margin, dose-reduction claim, or
field-wide conclusion is asserted here.

## Follow-up: numeric submission validation

Source heads checked: main `73cd127`, heyang `29955a9`, control branch
`a42ad27`. No newer published Heyang commit was visible; this says nothing
about unpushed workstation work. Open PRs #1/#2 concern dependencies and #20
concerns WS-2 prose; none overlaps this scoring change. The older integration
branch `a436c6e` remains separate and is not claimed merged here.

Fixed the paired submission gate to reject NaN, either infinity, booleans,
strings, lists and objects in all eight recognized metric fields. Null optional
metrics remain absent; the existing paired-metric requirements still apply.
Every method block is validated before any entry is appended, so a later bad
block cannot leave a partial submission in an in-memory board. The CLI reports
the rejection before saving a board.

Tests cover valid submissions, invalid values across all recognized fields,
mixed valid/invalid method blocks, and CLI rejection with both new and existing
boards. Existing boards are compared byte-for-byte after rejected requests.

| Check | Result |
|---|---|
| Original main scoring suite, before change | 108 passed, 10 skipped |
| Initial new regression cases, before fix | 80 failed, 2 passed |
| Full scoring suite after fix, including an additional atomicity test | 191 passed, 10 skipped |
| Agent compatibility tests using changed scoring | 48 passed, 1 skipped (49 ran) |
| R6 amended comparison rederivation | Five model verdicts PASS; committed verdict matches |

Scoring command, from `WS-4_leaderboard`:

    /home/S248103/pwm/.venv-ldct-integration/bin/python -m pytest scoring/tests -q -rs -p no:cacheprovider

Agent source `eb0a3643695729570860c1eacba21b5af45eea05`, shared core
`7a20d4693b91f849895b780e66a679c43bbb8694`; the repeat used system Python,
the same `PYTHONPATH` above, and `LDCT_REPO` pointing to the reviewed worktree.
Ten scoring skips require unavailable historical session-local scripts.
No new GPU inference or native Windows verification was performed.

This closes the numeric-input portion of the evidence task. Wrong/missing task
identity, empty required coverage, direct board publication validation,
receipt/failure storage, and claim-to-provenance binding remain open. Finite
BandER values alone do not establish diagnostic validity.
