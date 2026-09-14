# LDCT integration and collaborator status — 14 September 2026

This is a review branch, not a merged release or scientific acceptance record.
The owner asked that work continue with a fresh status/Heyang check each time;
the repository [working instructions](AGENTS.md) preserve that requirement.

## Starting source state

| Source | Checked head | Visible state |
|---|---|---|
| `main` | `e7efa20c8a98bf4e03981beba1716efd10ae57c1` | Outcome requirements plus the new contrast scope note |
| `heyang` | `929c21e72673656350ea621dc2e8df0024790635` | Last visible commit 11 September; 19 commits unique to this branch |
| `bander/control-matrix` | `a42ad2703594b4c3a4cd6a02396d1ae444f64dac` | Existing control constructors; patient measurements not posted |

At this check, `main...heyang` was 17/19. No open PR from Heyang was visible;
PR #20 overlaps WS-2 prose, and #1/#2 are dependency updates. No new Heyang reply
or completion receipt for BANDER-2/4/6 and the data backup was found. This does
not establish that no work has occurred on his workstation.

Integration branch: `codex/heyang-integration-2026-09-14`. Merge commit `0d9802d`
preserves Heyang's history and the current `main` Director decision and amended
R6 comparison. Only the comparison JSON had a Git conflict in this merge;
automatically merged prose still required review. The historical route-(a)
report is retained with a note distinguishing its causal interpretation from
what the rerun establishes. No tolerance or recorded R6 verdict was changed.

**Status refresh, 13:26 UTC:** `main` advanced to `b67024f` while this work was
being reviewed; Heyang remained at `929c21e`. The branch incorporates the new
reproduction-paper proposal (`d1f96a2`), removal of WS-1 R5/R6 inferential group
statistics (`24e2883`), and venue register (`b67024f`). The numerical/software
repairs in `ec45f62` are unchanged by that merge. GitHub metadata still reports
this repository public at this check.

The paper proposal and venue register are preserved as collaborator proposals,
not accepted scientific claims. In particular, the reproduction proposal's
private-visibility statement and its claims of uniquely established causality
and prospective tolerance justification need reconciliation with the current
metadata and the dated R6 review. Writing or launching that paper is a separate
work item; no new submission or research commitment is made here.

## Work completed on the review branch

- Restored LF trap provenance hashes, preserved JSON bytes through
  `.gitattributes`, and verified both LF/CRLF plus changed-content failures.
- Corrected patient replacement sampling: repeated patients repeat their full
  blocks; paired doses share a draw for the knee and method ratios retain
  pairing. Missing/malformed/unequal patient maps fail explicitly. Slice mode
  remains unchanged in the bounded comparison against Heyang's implementation.
- Corrected patient-mode knee reporting so observed boundary crossings do not
  force zero-width intervals. Left censoring is explicit; unreached/nonfinite
  draws leave the complete interval unavailable.
- Recomputed the patient bootstrap from committed numeric records, without
  running models or reading images. [The v2 report](WS-1_dataset/output/lidc_simulated_bootstrap_patient_v2.md)
  identifies the three-patient sample and the invalid legacy bootstrap.
- Rejected NaN, infinity and booleans in table-extraction finite-CNR checks,
  including invalid seed-level median fallbacks. Current table values and input
  fingerprints are unchanged by this validation repair.
- Corrected the [contrast scope note](FIELD_COLLAPSE_SCOPE_CONTRAST.md): AAPM's
  published enhanced portal-venous protocol is known; LIDC is not uniformly
  unenhanced; an agent-name tag does not establish phase; the injection start
  tag is `(0018,1042)`. Per-record metadata work remains open.

## Verification

Linux, Python 3.11.16; dedicated test environment with NumPy 2.4.6, SciPy 1.17.1,
pytest 8.4.2 and jsonschema 4.26.0. Commands below use that environment's Python.

| Check | Result |
|---|---|
| Merged WS-4 before the hash fix | 2 failed, 124 passed, 10 skipped; both failures were the reported hashes |
| WS-4 plus WS-1 analysis tests after repairs | 207 passed, 10 skipped (130 scoring + 21 bootstrap + 56 table-validation tests) |
| WS-2 framework suite | 157 passed, one existing small-sample warning |
| R6 `recompare_per_metric.py --check` | All five committed log-comparison verdicts rederived as PASS |
| Bootstrap v2 | 4,000 replacement draws, seed 20260831, three patients; source/generator hashes recorded |
| Removed L506 history check | Zero `test_img/L506` object paths reachable from checked `heyang` |

```bash
# From WS-4_leaderboard
python -m pytest scoring/tests ../WS-1_dataset/analysis/tests -q -rs -p no:cacheprovider
# From WS-2_framework/pwm_dose_equivalence
PYTHONPATH=src python -m pytest -o addopts= tests -q -rs -p no:cacheprovider
# From repository root
python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check
```

The ten scoring skips need absent historical session-local scripts. No native
Windows run, GPU inference, WS-3 torch suite, PDF rebuild, new image experiment,
reader study, hidden test service or data-copy operation was performed. Existing
paper PDFs remain inherited artifacts. Software tests do not resolve the WS-2
definition counterexample or validate clinical performance.

## Open work before stronger acceptance

1. **Heyang/data holder:** native Windows checks of this same branch; BANDER
   patient controls; backup/deposit dry-run receipt; confirm the patient/series
   mapping and contrast evidence at the authorized source. Do not duplicate
   completed patient-ID plumbing or the existing control constructors.
2. **Scoring engineer:** finite/task-bound publication validation, required
   vendor/dose coverage, and explicit receipt/failure-storage/publication states.
   In-memory checks of the integrated code still allow NaN and missing/omitted
   group evidence through some publishing assertions. Saving a failed board now
   raises; it does not persist failure evidence despite an inherited comment.
3. **Analyst/statistician:** three-patient limitations, corrected-bootstrap
   interpretation and framework definitions. Equal patient-label vectors do not
   independently verify slice order or the original data-to-identifier mapping.
4. **Harmonization/table provenance:** the 150 HU number was selected after the
   observed 144.8536 HU difference, so it is descriptive, not an independently
   validated acceptance threshold. Its hash covers metadata but not the HDF5
   pixels used; selected-series and voxel-weighting provenance need repair.
   The baseline/detectability hash `14bd54f...` is the CRLF encoding fingerprint;
   current LF sources yield `369ee3e946440b5144abdd067e0fa1d0af7ded407143b0d685f65d52c0dddf40`.
   Numeric table/LaTeX cells reproduce, but the encoding-dependent provenance
   needs a dated correction. No source data were available to rerun harmonization.
5. **Manuscript reconciliation:** resolve inherited physical-acquisition,
   BandER/clinical-meaning, observer-variance and population-coverage overclaims;
   identify descriptive/post-hoc thresholds, reconcile PR #20, and rebuild PDFs
   after scientific review. This integration does not endorse those claims.

Before resuming, fetch and compare the current remote heads and update this
record and [Heyang's handoff](HEYANG_NEXT_2026-09-13.md). Do not mark unavailable
workstation evidence complete or infer that a field-level question is settled.
