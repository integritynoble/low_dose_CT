# Example credentials

Concrete published-credential JSON files that demonstrate every failure mode
the [`pwm-audit`](../README.md#v022-additions-d9--16-2026-06-05) shell command
catches. A reviewer or regulator can run `pwm-audit examples/<file>` and read
the audit's output against the expected behaviour below.

All examples are **generated** from [`regenerate.py`](regenerate.py) at fixed
seed = 42. Do not hand-edit them — re-run the script. The
`tests/test_examples.py` suite catches drift between the script's output and
the on-disk JSON.

---

## Clean credential

[`valid_ct_lung_nodule.json`](valid_ct_lung_nodule.json) — a clean **PASS**
credential for paired AUC on a synthetic lung-nodule cohort (n_test = 500,
ε = 0.05, α = 0.05, estimator = DeLong). The candidate adds small per-case
noise to the reference scores; the paired AUC delta lands comfortably inside
(−ε, +ε).

```bash
$ pwm-audit examples/valid_ct_lung_nodule.json
pwm-audit: OK

Hard checks:
  schema_valid             = True
  verdict_self_consistent  = True
Soft signals:
  framework_hash_known     = True
  sample_size_check_ok     = True

Issues: none

Warnings: none
$ echo $?
0
```

---

## Failure examples

Each file in [`failures/`](failures/) is a deliberate perturbation of the
clean credential illustrating one audit signal. Hard issues block `ok` and
exit 1; soft signals (warnings) do *not* flip `ok` but are surfaced for the
reviewer's attention.

| File | Perturbation | Audit signal | Hard / Soft | Expected exit |
|---|---|---|---|---|
| `failures/tampered_verdict.json` | Flipped `verdict` (PASS → FAIL) on an otherwise valid CI | Issue: `$.credential.verdict: stored 'FAIL' but (lo, hi) vs epsilon implies 'PASS'` | **Hard** — `verdict_self_consistent = False` | `1` |
| `failures/inverted_ci.json` | Swapped `delta_ci_low` and `delta_ci_high` | Issue: `$.credential: delta_ci_low > delta_ci_high (empty CI is impossible)` | **Hard** — caught by CI-sanity check | `1` |
| `failures/missing_field.json` | Removed the required `verdict` field | Issue: `$.credential: missing required field 'verdict'` | **Hard** — schema validation fails | `1` |
| `failures/unknown_framework_hash.json` | Replaced `framework_hash` with `sha256:0000…0000` | Warning: framework_hash mismatch; `framework_hash_known = False` | **Soft** — credential may be from an older framework version | `0` |
| `failures/undersized_pass.json` | `sample_size_check.ok = False` on a `PASS` verdict | Warning: PASS verdict on cohort below the formula prescription | **Soft** — verdict may be a fluke | `0` |
| `failures/bca_headline.json` | `estimator` set to `bca` | Warning: BCa is opt-in only; confirm a percentile companion exists | **Soft** — per `theory/proofs/estimator.md` §4 | `0` |

### Try them yourself

```bash
# Hard issue — exits 1
$ pwm-audit examples/failures/tampered_verdict.json
pwm-audit: FAIL
...
Issues (1):
  - $.credential.verdict: stored 'FAIL' but (-0.0133..., -0.00022...) vs epsilon=0.05 implies 'PASS'

# Soft signal — exits 0 with a warning surfaced
$ pwm-audit examples/failures/undersized_pass.json
pwm-audit: OK
...
Warnings (1):
  - $.credential: PASS verdict issued on a cohort below the formula prescription...
```

### Machine-readable mode

```bash
$ pwm-audit examples/failures/tampered_verdict.json --json | jq '.ok, .issues[0]'
false
"$.credential.verdict: stored 'FAIL' but ..."
```

---

## Cross-references

* [`../README.md`](../README.md) — library overview and the v0.2.1 / v0.2.2
  changelog entries that describe `audit_credential` and the `pwm-audit` CLI.
* [`../../paper_draft/credential_reading_guide.md`](../../paper_draft/credential_reading_guide.md) §7a
  — the non-coder reading guide whose red-flag checklist these examples
  exercise.
* [`../credential_schema.json`](../credential_schema.json) — the
  machine-readable JSON Schema the clean credential conforms to (added at
  D9 + 19; published alongside the examples directory).
