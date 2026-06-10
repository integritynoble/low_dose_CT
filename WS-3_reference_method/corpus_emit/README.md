# `WS-3_reference_method/corpus_emit/` — credential-emission step

Turns per-cohort task scores into the `credential.json` records the
*Scientific Data* corpus releases, in exactly the wire format that
`pwm-audit` and [`../deposit/dataset_metadata.schema.json`](../deposit/dataset_metadata.schema.json)
expect. Builds on the WS-2 library (`pwm_dose_equivalence`) — no credential
logic is re-implemented here; this module only orchestrates issuance, auditing,
on-disk layout, and indexing.

## Why credentials are cohort-level (not per-scan)

A signal-equivalence credential summarises a **whole test cohort** (`n_test`
patients) for one `(task, signal_ratio, subpopulation, method)` stratum. So
credentials live under `credentials/<task>/r<dd>/<method>__<vendor>.json`, **not**
inside the per-scan record folders (which hold the reconstruction / uncertainty
/ error / task-score maps). This matches the manuscript Data Records layout.

## API

| Symbol | Purpose |
|---|---|
| `StratumSpec` | Identifies one credential stratum + its credential parameters (task, metric, `r`, subpopulation, ε, α, method, vendor…). |
| `AucScores` / `PairedScores` | Score containers: AUC tasks use `a_pos/a_neg/b_pos/b_neg` (DeLong); other metrics use `paired_a/paired_b` (percentile bootstrap). |
| `build_credential(spec, scores)` | Computes a `SignalEquivalenceCredential` via WS-2; dispatches on `spec.metric`. |
| `emit_stratum_credential(root, spec, scores)` | Builds → **audits** → writes one credential to the corpus. Raises `CredentialEmitError` on a failed hard audit so broken records never land. |
| `rebuild_index(root)` | (Re)writes `credentials/all_credentials.jsonl` — one queryable line per credential, sorted by path. |
| `verify_corpus_credentials(root)` | Audits every credential on disk; returns `{n_credentials, ok, failures, warnings}` (backs deposit checklist §4). |

## Usage (Phase 3)

```python
from emit_credentials import StratumSpec, AucScores, emit_stratum_credential, rebuild_index

spec = StratumSpec(
    task_name="lung_nodule_5mm", metric="auc",
    signal_ratio=0.25, subpopulation="adult_chest_pwm_l3_test_v1",
    epsilon=0.05, method="pwm_ref_v1", reference_method="full_dose_fbp",
    vendor="Siemens", anatomy="chest",
)
# scores come from the frozen nodule detector over the cohort:
emit_stratum_credential(corpus_root, spec, AucScores(a_pos, a_neg, b_pos, b_neg))
# ... repeat for every (task x dose x method x vendor) stratum ...
rebuild_index(corpus_root)
```

The score arrays are the only Phase-3 input this module needs; everything else
(verdict, CI, framework hash, audit) is handled here.

## Tests

```
python -m venv .venv && .venv/bin/pip install -e ../../WS-2_framework/pwm_dose_equivalence pytest jsonschema
cd corpus_emit && PYTHONPATH=. ../../.venv/bin/python -m pytest -q   # 18 passed
```

Tests cover: dose-tag canonicalisation, schema conformance of built credentials,
estimator dispatch (DeLong for AUC / percentile otherwise), audit-blocks-on-tamper,
on-disk layout, index shape + self-exclusion + stable sort, and corpus-wide
verification (all-ok + tamper detection).

## Status

Wired and tested against synthetic scores. The **real** score arrays arrive with
WS-3 Phase 3 (frozen detector / segmentation outputs, D9+270); plug them into
`AucScores` / `PairedScores` and the same calls produce the deposit-ready
credential records. See [`../deposit/DEPOSIT_CHECKLIST.md`](../deposit/DEPOSIT_CHECKLIST.md) §1, §4.
