# `WS-3_reference_method/fixture/` — synthetic end-to-end corpus

Generates a miniature but **structurally complete** WS-3 corpus and runs the
entire deposit pipeline on it, so a reviewer or CI run can exercise the whole
machine **without waiting on Phase-3 data**.

```
image records (valid NIfTI) + scan_meta
  -> emit_stratum_credential   (credentials/, audited by pwm-audit)
  -> rebuild_index             (all_credentials.jsonl)
  -> package_corpus.package    (dataset_metadata.json + MANIFEST.sha256)
  -> verify_manifest           (integrity check)
```

It is **not** scientific data: pixels are random and score arrays are synthetic.
Its only job is to prove the pipeline is correct. The real corpus is produced by
the Phase-3 reconstruction pipeline and deposited per [`../deposit/`](../deposit/).

## Run it

```
python make_synthetic_corpus.py /tmp/demo_corpus --seed 42
```

Prints a JSON report; exits non-zero if credentials fail to audit, the manifest
doesn't verify, or the metadata isn't schema-valid. What it builds (default):

| | |
|---|---|
| Scans | 2 vendors × 1 anatomy (chest) = 2 (chest → lung-nodule AUC; v1 is lung-nodule-only) |
| Record folders | 2 scans × 2 doses (r025, r010) = 4 |
| Per folder | `recon_mean` / `uncertainty_sigma` / `error_abs` / `task_nodule_score` (valid `.nii.gz`) + `scan_meta.json` |
| Baselines | `red_cnn` chest r025 per vendor (recon / error / task) |
| Credentials | 6 cohort-level (lung-nodule AUC via DeLong; reference + baseline), all audit-clean |
| Packaged | `dataset_metadata.json` (counts filled, schema-valid) + `MANIFEST.sha256` (passes `sha256sum -c`) |

## What it proves

- **The NIfTI records are real** — they load with `nibabel` (tests assert a round-trip). The writer (`write_nifti`) is self-contained: numpy-only, gzip with `mtime=0` for deterministic bytes; no nibabel needed to *write*.
- **The AUC (DeLong) credential path runs end-to-end** — matching the v1 lung-nodule corpus. (The percentile/Dice path retains unit coverage in `corpus_emit/tests`.)
- **Reference and baseline credentials coexist** without filename collision.
- **The integrity manifest is standard-tool compatible** — `sha256sum -c MANIFEST.sha256` exits 0.
- **The whole chain is deterministic** at a fixed seed (same recon bytes, same counts).

## Uses

- **CI smoke test** of the emit → package → verify pipeline (no Phase-3 data).
- **Reviewer artifact** — a runnable example for the manuscript's reproducibility story: a reviewer can generate a corpus, `pwm-audit` a credential, and `sha256sum -c` the manifest in one command.
- **Schema regression** — if the credential wire format, metadata schema, or layout drifts, the fixture build fails loudly.

## Verified both ways, in isolation

[`DEMO_RUN_GUIDE.md`](DEMO_RUN_GUIDE.md) pins an isolated environment, runs these tests with skips reported,
and runs `demo_verify.py`: one valid package accepted, six corrupted **copies** rejected for named reasons,
one verifier failure reported as UNVERIFIED, the valid package proven untouched, and an evidence packet written.

## Tests

```
cd fixture && PYTHONPATH=. ../../.venv/bin/python -m pytest -q   # 23 passed
```

Covers the NIfTI round-trip, full-build green report, directory structure,
both-estimator coverage, reference/baseline coexistence, index↔credential count,
`sha256sum -c` compatibility, metadata count fill, determinism, and the CLI.
