---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_37e03a7d9d4011f19046525400287e28
    ReservedCode1: ucxCK0i5Dw7mKz3dOKNt8XX2vUwrjbEmoumO2lM0YHRJsxve/IkkvpMKrliVl68SzkSarRTDdt0KzvmxaJgEX4OmtbDOIaf2dr9ZYX0ZcogJRHPj1ir97OIjYbWn7SomNKRo6nfcEXmMqpPwDUAxVR8WorpqeuDA76ryfPVt9PBJD1Gk7d5Mia8mU7U=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_37e03a7d9d4011f19046525400287e28
    ReservedCode2: ucxCK0i5Dw7mKz3dOKNt8XX2vUwrjbEmoumO2lM0YHRJsxve/IkkvpMKrliVl68SzkSarRTDdt0KzvmxaJgEX4OmtbDOIaf2dr9ZYX0ZcogJRHPj1ir97OIjYbWn7SomNKRo6nfcEXmMqpPwDUAxVR8WorpqeuDA76ryfPVt9PBJD1Gk7d5Mia8mU7U=
---



# WS-4 scoring service (P0 paired gate + blur trap; P1 held-out + spread; P2 observer; P3 registry)

Minimal runnable implementation of the leaderboard scoring pipeline for the
low-dose-ct.md items implemented so far:

1. **Paired scoring gate (P0)** — the service receives fidelity (PSNR/SSIM) **and**
   detectability together; a submission without detectability is not publishable
   ("both numbers or neither", §4). The detectability side **must include the
   discriminating index** `bander_roi` (frequency-domain `detectability-freq-v1` ROI
   BandER); the insertion-based observers (CNR / CHO-AUC / NPWE) are carried for
   transparency but do not satisfy the gate alone, because the permanent blur trap
   outscores real methods on CNR and saturates CHO-AUC (Rung 1; enforced 2026-09-04,
   see `../OPTIMIZATIONS_LOG.md` P0-1b). The gate is a dependency-free
   re-implementation of the paired gate WS-3 wired into its RunBundle
   (`WS-3_reference_method/runbundle/run.py` -> `evaluation.validate_paired_report`), so
   the leaderboard can referee independently without importing the WS-3 package.
2. **Permanent Gaussian blur trap (P0)** — the `seed-blur` entry (sigma=1.0 px, 5x5 kernel,
   same as WS-1/WS-3) is initialised into the board with `permanent=True`; it can never
   be removed or overwritten (`assert_trap_present` on every save/load), and every
   listing shows each entry's gap vs the blur. **Measured numbers since 2026-09-05**
   (P0-1d): AAPM held-out test, 4 patients, detectability-freq-v1, provenance and
   SHA-256 in the entry's `source` block and in `leaderboard.TRAP_SOURCE`. On that run
   the trap takes the highest SSIM (0.965), the highest PSNR (41.6) **and** the highest
   CNR (0.171) of the four methods, while ranking last on `bander_roi` by 8.9-15.6x.
   **Per-vendor traps (P0-1e, 2026-09-05)**: `seed-blur:<vendor>` for GE / Philips /
   Siemens / Toshiba (LIDC, simulated r=0.25) and AAPM-Siemens-real, from
   `aapm_lidc_cross_vendor_spread.json` (`leaderboard.VENDOR_TRAP_SOURCE`), so the Rung 5
   requirement that the trap separate in *every* vendor group is checked from the board by
   `trap_rank_by_group` (recorded under `board["trap_rank_by_vendor"]`). Traps are excluded
   from `compute_spread`: they are the control a group is judged against, not members of it.
2b. **Trap-rank gate (P0-1c, 2026-09-05)** — the trap must rank **last** on the
   discriminating index. `trap_rank_report` is recomputed on every mutation and stored
   under `board["trap_rank"]` (PASS / FAIL / INDETERMINATE), so the verdict lives in the
   artifact rather than in prose; `assert_trap_ranks_last` is the hard gate for a
   publishing path. Ranking itself now leads with `bander_roi` rather than CNR: a CNR-led
   board put the trap *first* on the measured Rung 1 numbers.
3. **Held-out set independent of W_name, no write path (P1-3)** — `scoring/heldout.py`
   freezes the held-out set under the referee's OWN principal; a submission is a
   `SubmissionEnvelope(method_name, result)` with no write surface (recursive scan) and
   must not reference referee-owned files (`leaderboard.json` / `heldout.json`). The CLI
   `submit` rejects any envelope that could write back to the ranking or held-out data.
4. **Spread reporting by vendor / dose (P1-4, R5/R6)** — every entry carries
   `vendor` / `dose` tags; `leaderboard.spread` and the `spread` CLI group by
   vendor/dose and report the fidelity (PSNR) + detectability (BandER, or CNR
   fallback) + transparency (CNR) span/std instead of averaging across groups
   (Rung 5/6). **R5 method adjustment (2026-08-22):** the original R5 design
   required external multi-vendor submissions on the board; none exist, so the
   project's own held-out AAPM/LIDC multi-vendor + multi-dose results are
   treated as the on-board submission set (own-data proxy for external
   submissions). Constraints unchanged: per-vendor/per-dose grouping, never
   average across groups, blur trap must separate in every group. Empirical
   run: `WS-1_dataset/output/aapm_per_dose_spread.json` + `_summary.md`
   (per-vendor PASS + per-dose PASS).
5. **Published observer channels + sensitivity report (P2-5)** — `observer_sensitivity.py`
   publishes the observer channels (CNR + CHO(DOG-4) + NPWE, and a second observer
   CHO(DOG-6) + NPWE(beta)) with their internal-noise parameters, and provides a
   `report_observer_sensitivity` entrypoint that reports the rank-shift when switching
   to the second observer (synthetic perturbation today; wired for real data).
6. **Rung 1-6 status registry (P3-6)** — `rung_registry.py` + `data/rung_registry.json`
   keep the Rung 1-6 state (supported data / status done-partial-blocked + reason / gate),
   rendered to `RUNG_REGISTRY.md`. Rung state is changed by `update_status` after
   validation only ("rung closed by registry, not by agent").

**Comparability across WS.** The task specification is shared with WS-1's observers and
WS-3's method suite (`task_spec.py`: SKE Gaussian 2 px / 20 HU / location-known / tissue
ROI [10,120] HU / DOG-4 CHO / NPWE `rho*exp(-rho/0.2)` / Rose CNR >= 3). Submissions
whose detectability was measured on a different task are rejected.

## Layout

| Module | Role |
|---|---|
| `task_spec.py` | Shared task + blur constants (mirrors WS-1 `observers.py` / WS-3 `evaluation.py`). |
| `verify.py` | `check_paired_submission` / `check_submission_result` — the §4 both-or-neither gate **plus the Rung 1 discriminating-index rule** (`bander_roi` required); accepts the WS-3 RunBundle `results.json` layout (`validation.paired_methods`) or a flat metrics dict. |
| `leaderboard.py` | Board model: seed entries, detectability-first sort (CNR -> CHO-AUC -> PSNR), permanent-trap protection, vendor/dose tags, `compute_spread` (by vendor / by dose), add/load/save. |
| `heldout.py` | P1-3: frozen `HeldOutSet` under OWN principal, `SubmissionEnvelope` with recursive no-write-surface gate, referee-path guard, `authorize_write` / `referee_append`. |
| `observer_sensitivity.py` | P2-5: published observer channels (+ internal noise), `rank_shift_report` / `report_observer_sensitivity` (synthetic today), markdown renderer. |
| `rung_registry.py` | P3-6: load/validate/update/render Rung 1-6 registry; writes `data/rung_registry.json` + `RUNG_REGISTRY.md`. |
| `gates.py` | P3-6b (2026-09-05): executable gates for Rungs 2, 3 and 4 (`check_pairing_validation`, `check_roi_protocol`, `check_dose_curve`), each reading the artifact its rung cites and asserting the claim the rung's reason makes; each ships its own accept/reject probes in `PROBES` so an auditor can exercise it both ways (`exercise(name)`). |
| `cli.py` | `init` / `validate` / `submit` / `list` / `spread` / `observer-sensitivity` / `rung-status` entrypoints. |
| `data/leaderboard.json` | Initialised leaderboard (seeds: WS-3 reference + permanent blur). |
| `data/rung_registry.json` | Rung 1-6 state (status / reason / gate / supported data). |
| `../RUNG_REGISTRY.md` | Rendered registry at the WS-4 root (regenerated by `python -m scoring.cli rung-status`). |
| `tests/` | 106 tests, 96 passed / 10 skipped (34 baseline + 27 BandER / R4-R6 edge-case regression, 2026-08-22): gate semantics, WS-3-format acceptance, trap permanence, held-out write-back rejection (unit + CLI), spread, observer sensitivity, registry, CLI end-to-end; BandER adaptive-epsilon regularisation (near-zero denominators finite & bounded, zero perturbation vs old fixed floor, rank 4/4 preservation, run-script source contract), R4 dose-curve knee (`linear_cross`) edge cases, spread single-vendor / single-dose / k=1 edge cases; and the 2026-09-04 discriminating-index gate (rejects transparency-only detectability, proves the gate still opens with `bander_roi`, and asserts `bander_roi` reaches the spread block); and the 2026-09-05 trap-rank gate (13 tests, `tests/test_trap_rank.py`: healthy board passes, an entry at or below the trap fails and is named, a trap with no `bander_roi` reads INDETERMINATE rather than PASS, min-ratio separation is separate from rank, and a non-vacuity guard showing the old CNR-led key ranked the trap first on the same numbers); and the 2026-09-05 trap refresh (4 tests, `tests/test_trap_numbers.py`: the source file's SHA-256 and every metric re-read from WS-1 so a re-run cannot silently move the trap, and the fidelity-wins/detectability-loses claim asserted against the data); and the per-vendor traps (7 gate tests in `test_trap_rank.py`, 3 provenance tests in `test_trap_numbers.py`: all five groups separate at >= 3x, the board recomputes the source file's own separation ratios to 1e-9, a global check is shown to wrongly fail a legitimate GE entry that the per-group check passes, a group with no trap reads INDETERMINATE, traps stay out of the spread). See `tests/test_bander_regularization.py`. |

## Usage

```bash
python -m scoring.cli init --out scoring/data/leaderboard.json     # fresh board with seeds
python -m scoring.cli validate --result submission.json            # gate check only (RC 0/1)
python -m scoring.cli submit --result submission.json --method "MyNet" [--vendor GE --dose 0.25] --out scoring/data/leaderboard.json
python -m scoring.cli list --leaderboard scoring/data/leaderboard.json   # table incl. vs-blur
python -m scoring.cli spread --leaderboard scoring/data/leaderboard.json --by vendor   # P1-4 spread by vendor/dose
python -m scoring.cli observer-sensitivity --seed 7                # P2-5 rank-shift report (synthetic)
python -m scoring.cli rung-status                                  # P3-6 render Rung 1-6 registry
```

`submit` accepts either a WS-3 RunBundle `results.json` (it takes every
`validation.paired_methods.<name>` block) or a flat metrics dict. A method block with
fidelity but no detectability raises and is refused; `list` always shows the
permanent blur trap and the per-entry `vs_blur` deltas. `submit` runs the P1-3
write-back gate first: an envelope exposing any callable write/save/append attribute
anywhere in the result, or referencing referee-owned files (`leaderboard.json` /
`heldout.json`), is rejected with RC 1 before any score is computed.

## Status vs the WS-4 plan

- Task 1.1 (scoring service spec) — partially done: runnable local prototype; the
  sandboxed container execution and live-web publication remain for Phase 1.
- Task 1.2 (S1–S4 verification) — not started; the paired gate is the S0 metric gate.
- Task 2.1 (seed entries) — done as seed data (`seed-blur` permanent + `seed-ws3-reference`);
  both are placeholder numbers from the WS-3 self-test structure and must be refreshed
  from the pinned WS-3 RunBundle before launch.
- `web/`, `submission_contract/` — still pending Phase 1.
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
