---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_3601afdd9d4011f19155525400826444
    ReservedCode1: OubaHe6RmEW/5pn5tUAAaOVd9aZjvSXxXknAeNV2kK+v12Sx3hqyuwtRRc6Sh4o0IGdcQbI7z6IWXvGdjrxO7AMJKZfmHV/IIVChymJPzeBH1ojmkBIn5v3aYDP+o1Gt/sAAAB17PuYL9VXT2KrHgOwc/5zuRNRGLJswvXy2vEhRv17N2+yHefvKkOI=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_3601afdd9d4011f19155525400826444
    ReservedCode2: OubaHe6RmEW/5pn5tUAAaOVd9aZjvSXxXknAeNV2kK+v12Sx3hqyuwtRRc6Sh4o0IGdcQbI7z6IWXvGdjrxO7AMJKZfmHV/IIVChymJPzeBH1ojmkBIn5v3aYDP+o1Gt/sAAAB17PuYL9VXT2KrHgOwc/5zuRNRGLJswvXy2vEhRv17N2+yHefvKkOI=
---

# WS-3 Optimization Log (P0 done — P1-4 / P2-5 / P2-6 / P2-7 implemented)

> Incremental additions on top of the completed P0 work (built-in observer,
> permanent Gaussian blur trap, paired both-or-neither schema gate). Everything below
> is strictly additive — existing gates, tests and the pinned RunBundle are intact.

## P1-4 — Held-out split isolation (low-dose-ct.md §6 / §7.2)

- `method/src/pwm_ldct_recon/heldout.py` — `HeldOutSet` (frozen, read-only; no write /
  append / save surface), `assert_no_write_path`, `check_eval_train_imports` (static
  scan of `evaluation.py` + `runbundle/run.py` forbidding `data`/`train` imports),
  `check_heldout_isolation` (validation must declare `data_provenance ==
  heldout-split` in emit mode), `heldout_isolation_gate`.
- `runbundle/run.py` — new `_heldout_gate(results, mode)`; results now carry
  `heldout_isolation_ok` and `heldout_gate_mode`. Run exit code fails if the gate fails.
- `runbundle/results.schema.json` — `heldout_isolation_ok` / `heldout_gate_mode`
  fields.
- Tests: `method/tests/test_heldout.py` (10 tests).
- E2E: `python runbundle/run.py --self-test` → `heldout_isolation_ok: true`, RC=0.

## P2-5 — Reproduce-first gate (low-dose-ct.md §7.1)

- `README.md` → new **"Reproduce-first gate"** section: comparisons require a local
  pinned-container reproduction (±0.5 dB tolerance); citing paper numbers directly is
  rejected by the WS-4 submission gate; `--self-test` is explicitly non-scientific.

## P2-6 — Artefact-class sub-scores (low-dose-ct.md §7.5)

- `method/src/pwm_ldct_recon/artefacts.py` — extensible artefact registry
  (`metal` / `motion` / `truncation` / `ring_streak`), `ArtefactScore` (paired
  fidelity+detectability, Rose-criterion `ok`), `validate_artefact_report` gate,
  `register_artefact_probe` extension point. No full-dataset run required.
- `runbundle/results.schema.json` — optional `artefacts` block (`$defs/artefacts`).
- Tests: `method/tests/test_artefacts.py` (10 tests).

## P2-7 — Deep-ensemble UQ report (low-dose-ct.md §7.6 / §5)

- `method/src/pwm_ldct_recon/uq_report.py` — `analyze_confidence_lesion`,
  `analyze_ensemble_bundle` (low-confidence ⟷ missed-lesion association;
  confidence = per-pixel ensemble std), `render_markdown`, `future_wiring_points`.
- `runbundle/results.schema.json` — optional `uq_report` block (`$defs/uq_report`).
- Tests: `method/tests/test_uq_report.py` (7 tests).

## New CLI commands (pwm-recon)

```
python -m pwm_ldct_recon.cli artefact-info        # print artefact-class registry (P2-6)
python -m pwm_ldct_recon.cli uq-report            # synthetic low-conf<->missed report (P2-7)
python -m pwm_ldct_recon.cli uq-report --markdown # human-readable Markdown summary
```

## Test status

`python -m pytest method/tests -q` → **65 passed** (was 38 before this round).
