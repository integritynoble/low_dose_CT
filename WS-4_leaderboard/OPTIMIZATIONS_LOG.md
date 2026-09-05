---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_39e51efc9d4011f1b930525400e6dd8f
    ReservedCode1: J9JA8WMA0YU2a/xiICB7SR6Oid8sFxFgpmJ96nE7eSSM2mU5A1LFA82t47gEHBN6e0wo7z0rQ+o7YmZTeSXG6SRZIFnqgYNsEYojyNWcgfbDSY32h1KevIttSFbh/7gKcQkagShvEEZl+nFT6H+99T9tY0xDNGAsgLmY9aZsPRvoo0Hn8AQ0KXneeuo=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_39e51efc9d4011f1b930525400e6dd8f
    ReservedCode2: J9JA8WMA0YU2a/xiICB7SR6Oid8sFxFgpmJ96nE7eSSM2mU5A1LFA82t47gEHBN6e0wo7z0rQ+o7YmZTeSXG6SRZIFnqgYNsEYojyNWcgfbDSY32h1KevIttSFbh/7gKcQkagShvEEZl+nFT6H+99T9tY0xDNGAsgLmY9aZsPRvoo0Hn8AQ0KXneeuo=
---

# WS-4 Optimizations Log (low-dose-ct.md alignment)

> Workspace: `WS-4_leaderboard` — Permanent Leaderboard + Annual Review.
> All changes are additive; the P0 prototype (paired §4 gate + permanent blur seed) is
> preserved and extended. Tests: **55 passed / 10 skipped** (`python -m pytest scoring/tests -q`).

---

## P0-1b. Paired gate requires the discriminating index (`bander_roi`)

**Status**: implemented + tested. **Changes what the gate admits — read before submitting.**

**Defect.** `task_spec.DETECTABILITY_FIELDS` was `("cnr_mean", "cho_auc_mean", "npwe_mean")`
and `verify.check_paired_submission` required *at least one* of them. `bander_roi` was
absent, so the gate never required the only index that separates the permanent blur trap.
This contradicted Rung 1, which already declares BandER discriminative and the
insertion-based indices "non-discriminative on real anatomy ... reported as transparency".

The consequence was not theoretical. On the simulated arm the trap's CNR **exceeds**
RED-CNN by 1.11–1.19×, CoreDiff by 1.08–1.13× and CTformer by 1.90–2.23× at every dose
level; on real anatomy CHO-AUC saturates at 1.000 for every method. A submission could
therefore clear the gate on a metric the trap wins, while the index that catches it
(ROI BandER: blur 0.432 vs models 3.854–6.735, blur last 4/4 in every vendor group) was
optional.

**Second defect, same root.** Because `bander_roi` was not in `DETECTABILITY_FIELDS`, it
was silently dropped by `verify.extract_paired_methods`. That made
`leaderboard.py::add_submission`'s `("bander_roi", "bander_full", "roi_tm_auc")`
carry-through **unreachable**, and `compute_spread`'s `bander_roi_span` could never be
populated from a submission — the Rung 5 dual-metric spread block was silently
fidelity+CNR only.

**Change.**

- `task_spec.py` — split the fields by role:
  - `DISCRIMINATING_FIELDS = ("bander_roi",)` — **required**.
  - `TRANSPARENCY_FIELDS = ("cnr_mean", "cho_auc_mean", "npwe_mean")` — reported, never
    sufficient alone.
  - `DETECTABILITY_FIELDS = DISCRIMINATING_FIELDS + TRANSPARENCY_FIELDS` (recognised and
    carried through).
  - `FREQ_SUPPLEMENTARY_FIELDS = ("bander_full", "roi_tm_auc")` — carried, not gate criteria.
- `verify.py` — `extract_paired_methods` now carries the frequency-domain fields in all
  three input layouts; `check_paired_submission` adds a fourth violation when
  detectability is present but the discriminating index is missing.

**Migration.** A submission reporting only CNR/CHO-AUC/NPWE is now rejected with:

> `detectability reports only insertion-based indices (cnr_mean/cho_auc_mean/npwe_mean);
> the discriminating frequency-domain index bander_roi (detectability-freq-v1 ROI BandER)
> is required`

Add `detectability.bander_roi` (protocol `detectability-freq-v1`, 1-px Gaussian high-pass
band-energy retention over the tissue noise ROI). Existing seed entries on the board are
unaffected: the gate runs on incoming submissions, not on stored entries.

**Tests** (`tests/test_scoring.py`, `tests/test_optimizations.py`):

- `test_paired_gate_rejects_transparency_only_detectability` — the defect; asserts the
  violation is the missing index, *not* a both-or-neither error.
- `test_paired_gate_opens_when_bander_roi_present` — proves the gate still **opens**
  (guards against a gate that refuses everything).
- `test_paired_gate_accepts_bander_roi_without_transparency_indices` — BandER alone suffices.
- `test_blur_trap_is_rejected_on_cnr_but_caught_by_bander` — the trap's measured AAPM
  numbers: admissible, beats the model on CNR, separated by BandER.
- `test_spread_by_vendor_and_dose` — now asserts `bander_roi_span`/`_std` reach the spread
  block, covering the previously-unreachable carry-through.

---

## P1-3. Held-out set independent of W_name, no write path

**Status**: implemented + tested (unit + CLI gate).

- `scoring/heldout.py`
  - `HeldOutSet` — frozen dataclass (`@dataclass(frozen=True)`), read-only records,
    owned by the referee principal `OWN_PRINCIPAL = "own"`; no write method.
  - `SubmissionEnvelope(method_name, result)` — the only shape a submission may take.
  - `assert_no_write_path(obj)` — reports callable write/save/append/... attributes on
    non-container objects (dict/list primitives are not filesystem-write capable).
  - `_find_nested_write_surface` — **recursive** scan: a write handle hidden anywhere in
    the result dict/list tree is caught.
  - `assert_no_referee_paths(result)` — flags any reference to referee-owned files
    (`leaderboard.json`, `heldout.json`).
  - `check_submission_cannot_write_back(submission)` — full gate: empty list = pass.
  - `authorize_write(principal)` — only OWN may append to the held-out set.
  - `referee_append(heldout, records, authorized_by)` — OWN-only append; returns a new
    set, original untouched.
- `scoring/cli.py::cmd_submit` now runs the write-back gate **before** any score:
  a smuggled write surface or referee-path reference ⇒ REJECT, RC 1.
- Tests: `tests/test_optimizations.py::test_*` (frozen set, no write surface, OWN-only
  append, envelope pass/reject, referee-path reject, CLI end-to-end rejection).

## P1-4. Spread ranking by vendor / dose

**Status**: implemented + tested.

- `scoring/leaderboard.py`
  - Entries now carry optional `vendor` / `dose` tags (seeds remain untagged).
  - `compute_spread(entries, by="vendor"|"dose")` — groups entries and reports, per
    group, `n_entries`, `psnr_db_span` / `psnr_db_std`, `cnr_mean_span` /
    `cnr_mean_std` (fidelity **and** detectability spread; never averaged across
    vendor/dose — Rung 6).
  - `new_leaderboard()` initialises a `"spread": {}` block; `add_submission` refreshes
    it after every accepted submission.
  - `leaderboard.json` structure gained `vendor` / `dose` per entry and a `spread`
    block; backward-compatible with the P0 board.
- `scoring/cli.py::cmd_spread` — `python -m scoring.cli spread --leaderboard <board>
  --by vendor|dose` renders the group table.
- Tests: `test_spread_by_vendor_and_dose`, `test_seed_entries_have_no_vendor_dose`,
  `test_submission_updates_board_spread_block`; CLI end-to-end verified with
  Siemens/GE/0.25/0.50 submissions.

## P2-5. Observer channel publication + sensitivity report

**Status**: implemented (synthetic perturbation; real data wiring point documented).

- `scoring/observer_sensitivity.py`
  - `publish_observer_channels()` — public, machine-readable observer spec: observer A
    = CNR(Rose≥3) + CHO(DOG-4, 6 channels) + NPWE(`rho*exp(-rho/0.2)`); observer B =
    CNR + CHO(DOG-6) + NPWE(beta); both publish `internal_noise` (sigma) parameters.
  - `rank_shift_report(entries, seed)` — applies a monotone noise perturbation to the
    second observer and reports per-entry `rank_shift` + `trap_flip`, plus the
    Spearman rho between the two rankings; marked `synthetic=True`.
  - `report_observer_sensitivity(entries, seed, markdown=False)` — entrypoint /
    renderer.
- `scoring/cli.py::cmd_observer_sensitivity` — `python -m scoring.cli
  observer-sensitivity --seed 7` (default seed entries: shows blur trap staying in
  place).
- Tests: `test_observer_channels_published`, `test_rank_shift_report_structure`,
  `test_observer_sensitivity_markdown`.

## P3-6. Rung 1-6 status registry

**Status**: implemented + tested + rendered.

- `scoring/data/rung_registry.json` — machine-readable registry:
  `{schema_version, updated_at, rungs: [{rung, title, status, supported_data, reason,
  gate}]}`; status ∈ {done, partial, blocked}.
- `scoring/rung_registry.py`
  - `validate_registry(reg)` — requires Rungs 1-6 present, valid status, reason for
    non-done, gate string.
  - `update_status(reg, rung, status, ...)` — validated update only; raises on invalid
    status ("rung closed by registry, not by agent").
  - `render_markdown(reg)` — renders `RUNG_REGISTRY.md`.
  - `save_registry` / `load_registry`.
- `scoring/cli.py::cmd_rung_status` — `python -m scoring.cli rung-status` validates the
  registry and regenerates `RUNG_REGISTRY.md`.
- `scoring/RUNG_REGISTRY.md` — rendered registry (current state: Rung 1 partial,
  Rung 2 partial — AAPM 2016 10-patient real-paired corpus staged at `E:\AAPM_staged\`,
  geometric pairing validation runs; Mayo LDCT-PD & prospective acquisition removed
  from v1.0 scope — Rung 3 partial, Rung 4 partial, Rung 5 partial, Rung 6 partial —
  LIDC four-vendor simulated LOOCV + AAPM Siemens real validation).
- Tests: `test_registry_has_rungs_1_to_6`, `test_registry_missing_rung_reported`,
  `test_registry_bad_status_reported`, `test_update_status_validated`,
  `test_registry_markdown_renders_table`.

---

## Test & verification

```
python -m pytest scoring/tests -q        # 34 passed
```

CLI end-to-end (fresh board):

```bash
python -m scoring.cli init --out board.json
python -m scoring.cli submit --result sub.json --method MyAlgo-Siemens --vendor Siemens --dose 0.25 --out board.json
python -m scoring.cli submit --result sub.json --method MyAlgo-GE --vendor GE --dose 0.25 --out board.json
python -m scoring.cli spread --leaderboard board.json --by vendor
python -m scoring.cli spread --leaderboard board.json --by dose
python -m scoring.cli observer-sensitivity --seed 7
python -m scoring.cli rung-status
```

Rejection path (P1-3 gate): a submission whose result references
`../data/leaderboard.json` or carries a write-capable object is rejected with RC 1
and a REJECT message before scoring.

## P0-1c. Trap-rank gate: the blur trap must rank last on the discriminating index

**Status**: implemented + tested. **Changes the board's ranking order — read before publishing.**

**Defect.** P0-1b made `bander_roi` required, but nothing checked where the trap actually
sat, and `sort_entries` still ranked by `cnr_mean` first. Rung 1, 3, 5 and 6 all rest on the
trap ranking last on detectability (measured 8.9–19.0× separation, blur last 4/4 in every
vendor group), yet that structural claim was enforced nowhere in code. Because the trap
*wins* on CNR (1.11–2.23× over the learned baselines on the simulated arm), a CNR-led board
displayed the deliberate cheat above real methods with every gate green.

**Fix.** `leaderboard.trap_rank_report(entries, min_ratio=None)` returns a verdict block:
PASS / FAIL / INDETERMINATE, the trap's value, the ranked comparable entries, the observed
minimum separation ratio, and a violation string per offending entry. `check_trap_rank`
returns the violations; `assert_trap_ranks_last` raises. `sort_entries` now leads with the
discriminating index, and an entry that does not report it sorts below every entry that does.

Three deliberate design choices, each of which could reasonably have gone the other way:

- **Recorded, not raised, on ordinary mutation.** `add_submission` and `save` store the
  verdict on the board instead of rejecting. A board on which the trap is not last is
  evidence — either an entry smooths beyond a plain Gaussian blur, or the index has stopped
  discriminating — and discarding it would let the leaderboard suppress a finding about
  itself. `assert_trap_ranks_last` is the hard gate for whoever publishes.
- **INDETERMINATE is distinct from FAIL.** If the trap carries no `bander_roi` while real
  entries do, the board cannot be checked and says so. Folding that into PASS would make
  "stop measuring the trap" the way to evade the gate. Note this fires on a fresh board as
  soon as a real submission lands, because `seed_blur_entry` is a placeholder: the trap must
  be refreshed from the WS-3 run before the board means anything.
- **Rank and separation ratio are separate.** Rank alone is the gate; `min_ratio` is
  optional and is the Rung 5/6 criterion (3×). A board can rank correctly and still fail a
  separation requirement, and the report carries both numbers.

**Tests**: 13 in `scoring/tests/test_trap_rank.py`, in both directions — a gate that only
ever refuses would pass a rejection-only suite and fail the project. Includes a non-vacuity
guard that reconstructs the pre-change CNR-led key and asserts it ranked the trap first on
the measured Rung 1 board, and one test (`test_real_submissions_against_a_placeholder_trap_are_indeterminate`)
written only because the suite failed first and the failure turned out to be correct
behaviour. Suite: 78 tests, 68 passed / 10 skipped, up from 65 / 55.

**Not done here**: the registry's Rung 1 status is untouched. Rung 1 has read `done` while
its named gate did not enforce its own discriminative claim; whether that warrants re-closing
with a dated note is the owner's judgement, not the gate's.

## P0-1d. Trap refreshed from the measured run

**Status**: implemented + tested.

**Why it was blocking.** P0-1c made the trap's rank a gate, and the gate reads
INDETERMINATE (not PASS) when the trap carries no `bander_roi` while real entries do.
`seed_blur_entry` still held synthetic self-test placeholders, so the first real
submission would have made every board uncheckable. The refresh moved from cosmetic to
on the critical path the moment the gate landed.

**Source**: `WS-1_dataset/output/aapm_r3_roi_detectability.json`, schema
`aapm-r3-roi-detectability/v1`, generated 2026-08-22T19:36:01, SHA-256
`9987864a…`, AAPM held-out test (aapm-0003/0005/0006/0009), detectability-freq-v1 on
`find_tissue_roi` patches, 48 ROIs per patient, per-patient mean. Recorded in
`leaderboard.TRAP_SOURCE` and in the entry's own `source` block.

**One protocol, not two.** The project holds two different band-energy measurements: the
Rung 1 whole-slice `band_energy_ratio` (blur 0.247, in `aapm_paired_baselines_v2.json`)
and the Rung 3 ROI `roi_band_energy_ratio` (blur 0.432). The leaderboard's discriminating
field is `bander_roi` and its task spec carries `noise_roi_hu_band`, so the ROI protocol
is the matching one and **every** metric on the entry comes from that single run. Taking
fidelity from the v2 file and ROI band energy from the r3 file would have produced an
entry no run ever measured.

**What the numbers say.** On this held-out test the trap takes the highest SSIM (0.9653),
the highest PSNR (41.63) *and* the highest CNR (0.1706) of the four methods, while
ranking last on `bander_roi` (0.4315) by 8.93x (LEARN), 8.98x (RED-CNN) and 15.61x
(CTformer). Three of the four indices a reader reaches for first rank the deliberate
cheat top of the board. That is the Rung 1 claim, now on real held-out data rather than
the simulated arm.

**`vendor` / `dose` stay None, and that is deliberate.** These numbers are Siemens real
quarter-dose, so the null looks like an omission. Those two fields are `compute_spread`'s
grouping keys, and the spread population is the submissions whose variability is being
characterised; the trap is the control a group is judged against, not a member of it.
Putting a deliberate cheat inside the span would change what the span measures. The
measurement context lives in `source` instead. Four existing tests
(`test_seed_entries_have_no_vendor_dose`, `test_spread_by_vendor_and_dose`,
`test_submission_updates_board_spread_block`, `test_spread_empty_board_returns_empty`)
caught an initial attempt to set them and were right to; they encode this decision.

**Known gap, named rather than hidden.** The board holds one trap entry, measured on
Siemens. Rung 5 requires the trap to separate in *every* vendor group, and that is not
checkable from the board alone until there is a per-vendor trap measurement and a
per-group form of `trap_rank_report`.

**Tests**: 4 in `scoring/tests/test_trap_numbers.py`, plus one added to
`test_trap_rank.py`. The provenance tests re-read the source file, verify its SHA-256 and
compare all eight metrics, so a WS-1 re-run fails the suite instead of silently moving the
board's trap; they skip if WS-1 is not checked out beside WS-4. `scoring/data/leaderboard.json`
regenerated. Suite: 83 tests, 73 passed / 10 skipped, up from 78 / 68.

## Future wiring points

- **P1-3**: attach real held-out DICOM records to `HeldOutSet` at launch; referee
  appends via OWN only.
- **P2-5**: replace the synthetic perturbation in `rank_shift_report` with actual
  second-observer scores from WS-3 (`observers.py` CHO(DOG-6) channel is already
  published there).
- **P3-6**: transition Rungs to `done` only when the corresponding gate evidence
  (real runs) lands; update `rung_registry.json` via `update_status`.
- **P1-4**: real vendor/dose tags come from WS-1 corpus provenance when submissions
  arrive with full RunBundle provenance.
*（内容由AI生成，仅供参考）*
