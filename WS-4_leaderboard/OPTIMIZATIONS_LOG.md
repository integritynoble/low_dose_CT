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
> preserved and extended. Tests: **34 passed** (`python -m pytest scoring/tests -q`).

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
