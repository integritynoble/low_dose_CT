# Heyang integration review — 20 September 2026

## Sources checked before editing

- main: `d4b941f94c147dd63206b0871292d61e1d7ebcaa`
- heyang: `d515825f577c155f03ed91977ac364f8765dbc7c`
- bander/control-matrix: `a42ad2703594b4c3a4cd6a02396d1ae444f64dac`
- prior integration: `a436c6e3eb1d7228eb3a4e9afd98899da61107f5`

Fetched all four branches. The prior integration was not an ancestor of main.
Open PRs were #20 (overlapping WS-2 prose) and dependency updates #1/#2; no
Heyang/integration PR was open. Heyang's WS-2 edits cover the unperformed-work
language addressed by #20; this integration does not close or separately merge
that PR. Read both dated handoffs, Heyang's 14 September measurement reply and
20 September pending-decision list. The reply is operator-reported evidence;
no independent rerun of its image measurements was performed here.

## Integration

Merge commit `48d053a` preserves Heyang's latest work and the earlier reviewed
patient-bootstrap, finite-table and contrast-provenance repairs. Resolved three
conflicts: equivalent JSON byte-preservation attributes, LF/CRLF regression
coverage, and historical route-(a) prose with its interpretation caveat. The
current main R6 comparison JSON is unchanged. The original failed criterion
and later retrospective amendment remain distinct.

Reviewed new submission/task/stratum gates, receipt storage and prototype
verifier/web code. Fixed two issues before merge: skipped verification must
report INCOMPLETE (and a nonzero CLI status), not ALL PASS; boolean/number
substitution must fail numeric comparison. Explicitly disabled rung checks are
also recorded as skipped. Added regression coverage. S3's prototype absolute
comparison is not endorsement of a universal reproduction tolerance or a
replacement for the amended R6 artifact.

## Verification

Environment: existing `.venv-ldct-integration`, Python 3.11 on Linux.

- From `WS-4_leaderboard`: `python -m pytest scoring/tests ../WS-1_dataset/analysis/tests -q -rs -p no:cacheprovider`: **347 passed, 10 skipped**.
  Skips require absent historical session-local scripts. An initial invocation
  from the repository root had an incorrect test/import path; rerunning from
  the documented package directory resolved collection.
- From `WS-2_framework/pwm_dose_equivalence`: `PYTHONPATH=src python -m pytest -o addopts= tests -q -rs -p no:cacheprovider`: **157 passed**, existing small-sample warning.
- `python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`: all five
  committed log-derived amended verdicts match.
- `python3 Heyang-paper/make_tables.py --check`: all tables current.
- No `test_img/L506` path found in objects reachable from checked Heyang head.
- `git diff --check` for integration edits: clean. The full inherited diff
  also contains CRLF JSON and historical whitespace warnings; artifact bytes
  were preserved rather than rewritten for formatting.
- Initial GitHub CI found one overlong line in Heyang's new WS-2 documentation
  test; split its diagnostic expression without changing its assertion.

No native Windows run, GPU inference, WS-3 torch tests, image/control experiment,
PDF rebuild, live sandbox execution, data copy or external adoption verification
was performed. Inherited PDFs are draft artifacts, not certified final papers.
The prototype UI must not be treated as a deployed publication service. Submitted
manifest hashes and patient labels still need independent source validation.
Three-patient bootstrap estimates remain exploratory. Scientific/framework and
paper interpretation issues in the 14 September review remain open unless
explicitly closed with evidence.

## Assignment and release state

The owner's new priority is recorded in `heyang/HEYANG_NEXT_2026-09-20.md`: **Heyang
finishes Heyang-paper as soon as possible**, ahead of further feature work.
The assignment requires evidence-bounded interpretation, exact environments,
artifact-derived numbers, owner metadata and a matching rebuilt PDF. The current
README/manuscript's causal and absolute-tolerance overclaims need that correction.
No acknowledgement or completion date from Heyang has yet been received.

This record describes the checked integration candidate. Remote merge status
must be confirmed from GitHub/main; local commits alone do not establish release.
