# pwm_dose_equivalence

Reference implementation of the **signal-equivalence framework** for medical-imaging dose-reduction claims (CT / MRI / PET). A reconstruction method `M` is *signal-equivalent* to a reference method `M_ref` at level `(r, T, ε, α)` over subpopulation `Π` iff its expected task performance on reduced-signal scans is within `ε` of the reference's performance on full-signal scans, with confidence `≥ 1 − α`.

This package implements that test through a single modality-agnostic API call and packages the verdict with a content-addressed framework hash so a third party can verify the credential by recomputing the bootstrap.

---

## Install (development)

```bash
cd WS-2_framework/pwm_dose_equivalence
pip install -e ".[test]"
```

Requires Python ≥ 3.10, `numpy`, `scipy`.

Status: **v0.2.2 — alpha**, scaffolded 2026-06-02 (v0.1.0) → extended 2026-06-04 (v0.2.0 adds BCa estimator + small-$n$ anti-conservativeness warning + `bound_M` argument for unbounded metrics) → extended 2026-06-05 (v0.2.1 adds `audit_credential()` + machine-readable `CREDENTIAL_JSON_SCHEMA` for non-coder auditing; v0.2.2 adds the `pwm-audit` console entry point so the audit runs from the shell with no Python call required). TestPyPI ship at D9 + 365; v1.0.0 alongside paper acceptance.

---

## Use

### Non-AUC metric (Dice, MAE, contrast-recovery)

```python
from pwm_dose_equivalence import signal_equivalence_credential, Task

cred = signal_equivalence_credential(
    paired_a=candidate_scores,        # ndarray, per-patient
    paired_b=reference_scores,        # ndarray, per-patient
    signal_ratio=0.25,
    modality="CT",
    task=Task("liver_dice", metric="dice"),
    subpopulation="adult_abdomen_pwm_l3_test_v1",
    epsilon=0.05, alpha=0.05,
    n_bootstrap=10_000, seed=42,
    sigma_delta_hint=0.07,           # optional: pre-flight sample-size check
)
print(cred.credential.verdict)        # PASS / FAIL / INDETERMINATE
print(cred.to_json())                 # serialise for publication
```

The estimator defaults to **percentile bootstrap** (Efron 1979) and emits a warning if `n_test` is below the formula prescription at the requested `(ε, α, σ_Δ_hint)`.

### Paired AUC (lung-nodule detection, lesion classification)

```python
cred = signal_equivalence_credential(
    a_pos=candidate_pos_scores,       # candidate scores on positive cases
    a_neg=candidate_neg_scores,       # candidate scores on negative cases
    b_pos=reference_pos_scores,       # reference scores on the same positive cases
    b_neg=reference_neg_scores,
    signal_ratio=0.25,
    modality="CT",
    task=Task("lung_nodule_5mm", metric="auc",
              ground_truth_protocol="pwm-ldct/annotation-qa/v0.5#sha256:..."),
    subpopulation="adult_chest_pwm_l3_test_v1",
    epsilon=0.05, alpha=0.05, seed=42,
    placement_sd_hint=0.15,
)
```

The estimator auto-selects **closed-form DeLong** (DeLong, DeLong & Clarke-Pearson 1988) when `task.metric == "auc"` and the AUC-style arguments are supplied — ~300× faster than the bootstrap with mild conservativeness (per [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md)).

### Signal-reduction operators

For users who want to construct paired scores by *running* the candidate method on a synthetic reduced-signal acquisition:

```python
from pwm_dose_equivalence import Tr_ct, Tr_mri, Tr_pet
import numpy as np

rng = np.random.default_rng(42)
s_red_ct  = Tr_ct(s_ref_counts, r=0.25, rng=rng)
s_red_mri = Tr_mri(k_space, r=0.25, rng=rng, central_fraction=0.25)
s_red_pet = Tr_pet(s_listmode, r=0.25, rng=rng)
```

CT and PET use Poisson-thinning (lambda-scaling). MRI uses a variable-density Cartesian mask; per [`../theory/proofs/mri_mask.md`](../theory/proofs/mri_mask.md), the mask family rides inside `Π` so the 5-tuple shape is preserved across modalities.

---

## Estimator defaults (per the 2026-06-02 coverage simulation)

| Metric | Default estimator | Justification |
|---|---|---|
| `auc` | `delong` | ~300× faster than bootstrap with mild conservativeness |
| `dice`, `mae`, `contrast_recovery` | `percentile` | Close-to-nominal coverage across all tested cells |
| any | `bca` | Opt-in only (deferred to v0.2.0 — does not robustly outperform percentile under the null) |

Override with `estimator="percentile"` or `estimator="delong"` to force a specific variant.

Full justification: [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md). Coverage simulation: [`../experiments/estimator_coverage/`](../experiments/estimator_coverage/).

---

## Sample-size pre-flight

The library refuses to issue a `PASS` quietly when `n_test` is below the closed-form requirement (Formulas (S1), (S3) from [`../theory/proofs/sample_size.md`](../theory/proofs/sample_size.md)). Pass `sigma_delta_hint` (general) or `placement_sd_hint` (AUC) and the library will emit a `UserWarning` if `n_test` is short. The warning text points the user at the sample-size proofs document.

---

## Tutorial notebooks

Four pedagogical tutorials in [`notebooks/`](notebooks/), one per validated modality plus a user-implementable extension example:

* [`01_ct_lung_nodule_auc.py`](notebooks/01_ct_lung_nodule_auc.py) — CT lung-nodule detection at 25 % dose (AUC; DeLong auto-selected; ε = 0.05)
* [`02_mri_meniscus_dice.py`](notebooks/02_mri_meniscus_dice.py) — MRI knee-meniscus segmentation at 4× acceleration (Dice; percentile bootstrap; ε = 0.02)
* [`03_pet_phantom_cr.py`](notebooks/03_pet_phantom_cr.py) — NEMA NU-2 IQ phantom contrast-recovery at 25 % activity (CR; percentile; demonstrates the small-n warning at n = 6)
* [`04_optical_extending.py`](notebooks/04_optical_extending.py) — Optical / fluorescence imaging at 25 % exposure (closes the manuscript "user-implementable" claim by showing how to define `Tr_optical` and pass it through the unchanged `signal_equivalence_credential` API)

Each file is a `.py` script with `#%%` cell markers — it runs as a normal Python script *and* as a Jupyter notebook (open in JupyterLab / VS Code / Spyder). Two reviewer-facing companions live alongside the notebooks:

* [`../paper_draft/reproduction_guide.md`](../paper_draft/reproduction_guide.md) — verifies the manuscript's numerical claims (audience: code-savvy reviewers).
* [`../paper_draft/credential_reading_guide.md`](../paper_draft/credential_reading_guide.md) — walks the credential JSON field-by-field for reviewers, regulators, and clinicians who need to *interpret* a credential without re-running the bootstrap themselves. Covers verdict semantics, CI vs $\varepsilon$ reading, framework-hash guarantees, the `sample_size_check` field, and a red-flag checklist.

---

## Tests

```bash
pip install -e ".[test]"
pytest
```

The v0.2.0 test suite covers:

* **Estimator** (`test_estimator.py`) — coverage under the null for both percentile and DeLong; verdict logic; edge cases (empty data, perfect classifier).
* **Sample size** (`test_sample_size.py`) — formula (S1) / (S3) / (S4) values against the numerical table in `theory/proofs/sample_size.md`; scaling laws.
* **Operators** (`test_operators.py`) — expected-count ratios for Poisson-thinning; central-region invariant for the MRI mask; NaN sentinel.
* **Credential** (`test_credential.py`) — JSON round-trip including all v0.2 fields; enum serialisation.
* **Framework hash** (`test_framework_hash.py`) — SHA-256 prefix; hash-mutates-on-spec-mutate.
* **API end-to-end** (`test_api.py`) — equivalent and biased candidates produce expected verdicts; auto-estimator-selection; sample-size warning.

**Current v0.2.2:** 140/140 tests pass at **100 % line coverage** (437/437 statements). The 90 % target from the manuscript's §software-rigor paragraph is the published floor; the library continues to ship well above it. The 140 tests now include 10 end-to-end integration tests (`tests/test_integration.py` — full credential-issuance pipelines across CT / MRI / PET, cross-modality consistency via the public API, JSON round-trip + framework-hash verification, seeded reproducibility, T_r operator integration, and verdict-distribution transitions) plus 35 credential-audit tests (`tests/test_credential_audit.py` — schema validation; tampered-verdict detection; framework-hash recognition; sample-size-check coherence; estimator-specific soft signals; deep-copy non-mutation invariant) plus 12 CLI tests (`tests/test_cli.py` — file / stdin / JSON / help / version / missing-argument / tampered-verdict exit-code paths) plus 12 examples + schema-artifact + snapshot tests (`tests/test_examples.py` — clean credential audits ok; each failure example produces its expected hard issue or soft warning; on-disk JSON stays bit-identical to `examples/regenerate.py` output and to `CREDENTIAL_JSON_SCHEMA`; `examples/expected_audit_output.txt` snapshot of `pwm-audit` output stays bit-identical to a fresh in-process re-run).

**v0.2.0 additions (D9 + 15, 2026-06-04):**

* **BCa estimator** (`bca_ci` + `estimator="bca"`) — opt-in only per the
  `theory/proofs/estimator.md` §4 decision (does not robustly outperform
  percentile under the null). Useful in regimes with visible bootstrap-
  distribution skew.
* **Small-$n$ anti-conservativeness warning** — fires for any non-AUC
  call with $n < 30$, citing the V3-11 finding in
  `theory/proofs/estimator.md` §4c (percentile bootstrap coverage drops to
  0.82–0.93 in that regime). Affects both `percentile` and `bca`.
* **`bound_M` argument** — exposes the Bernstein bound's bound parameter
  for unbounded metrics (MAE / MSE on raw HU; default `bound_M = 1.0`
  for bounded metrics). Larger `bound_M` strictly increases the
  Bernstein-bound sample-size requirement; the CLT bound is unaffected.

**v0.2.1 additions (D9 + 16, 2026-06-05):**

* **`audit_credential(json_dict_or_str)`** — internal-consistency audit
  for a published credential. Validates schema, recognises the
  framework hash against the currently-installed library, re-derives
  the verdict from `(delta_ci_low, delta_ci_high, epsilon)` and checks
  it matches the stored verdict, inspects the `sample_size_check`
  field for the undersized-PASS pattern, and flags BCa-as-headline
  credentials. Returns a `CredentialAudit` dataclass with `ok`,
  `schema_valid`, `framework_hash_known`, `verdict_self_consistent`,
  `sample_size_check_ok`, `issues`, and `warnings`. Does **not**
  re-run the bootstrap (that is the job of
  `paper_draft/reproduction_guide.md`).
* **`CREDENTIAL_JSON_SCHEMA`** — machine-readable JSON Schema
  (draft-07-compatible) describing the credential wire format. A
  caller can `json.dumps(CREDENTIAL_JSON_SCHEMA)` to get an on-disk
  artifact and validate credentials in any JSON-Schema-aware tool
  (no Python required).
* **Backs the manuscript §software_rigor "Credential reading guide"
  claim** with code: the reading guide
  (`paper_draft/credential_reading_guide.md`) §7a now demonstrates
  the audit call directly.

**v0.2.2 additions (D9 + 16, 2026-06-05):**

* **`pwm-audit` console entry point** — installs as a shell command
  via `[project.scripts]`. Calls the same `audit_credential` function
  but with no Python required by the caller:

  ```bash
  pwm-audit credential.json          # human-readable summary
  pwm-audit credential.json --json   # machine-readable JSON report
  cat credential.json | pwm-audit -  # read from stdin
  ```

  Exit code: `0` if `ok=True`, `1` if any hard issue, `2` on I/O or
  argument error. Drop into a CI hook or submission-checklist script
  and any internally-inconsistent credential fails the workflow.

* The CLI is documented in
  [`../paper_draft/credential_reading_guide.md`](../paper_draft/credential_reading_guide.md)
  §7a alongside the Python API.

**Examples + standalone schema (D9 + 19, 2026-06-08):**

* **`examples/`** — one clean PASS credential
  ([`examples/valid_ct_lung_nodule.json`](examples/valid_ct_lung_nodule.json))
  plus six deliberately-broken variants in
  [`examples/failures/`](examples/failures/), one per audit signal:
  `tampered_verdict.json`, `inverted_ci.json`, `missing_field.json`
  (hard issues, exit 1); `unknown_framework_hash.json`,
  `undersized_pass.json`, `bca_headline.json` (soft warnings, exit 0).
  See [`examples/README.md`](examples/README.md) for the per-file
  audit-signal table and expected `pwm-audit` output. The examples are
  regenerated from `examples/regenerate.py` at seed = 42;
  `tests/test_examples.py` catches drift if any file is hand-edited.
* **`credential_schema.json`** (top-level of the library) — a
  standalone download of `CREDENTIAL_JSON_SCHEMA` for non-Python
  validators (JSON-Schema-aware editors, `ajv`, registry tooling,
  etc.). Regenerated from `scripts/dump_schema.py`; drift caught by
  `test_examples.py`.
* **`examples/expected_audit_output.txt`** — snapshot of the
  expected `pwm-audit` output on every example credential. A
  reviewer can confirm bit-identical behaviour by running
  `pwm-audit examples/<each>` themselves and diffing against this
  file. Regenerated from `examples/regenerate_expected_outputs.py`;
  drift caught by
  `tests/test_examples.py::test_expected_audit_output_matches_snapshot`.

---

## Versioning policy

Semantic versioning:

* `MAJOR` — break the credential JSON schema (bumps `FRAMEWORK_SPEC`)
* `MINOR` — add a modality, estimator, or task type; non-breaking
* `PATCH` — bug fix; preserves credential reproducibility

The current version is `0.2.2` (alpha). v0.2.0 added BCa + small-$n$ warning + `bound_M` + integration tests; v0.2.1 added `audit_credential` + machine-readable `CREDENTIAL_JSON_SCHEMA`; v0.2.2 added the `pwm-audit` console entry point; remaining items on the path to `1.0.0` include macOS / Windows CI runners (currently Linux only), a `method.code_hash` extension to the credential schema for full method-bundle provenance, and the manuscript-acceptance fixes the journal review surfaces. `1.0.0` ships alongside the *Nature Methods* paper acceptance with five-year support commitment.

---

## Cross-references

* [`../paper_draft/manuscript.tex`](../paper_draft/manuscript.tex) — the methodological framework this library implements.
* [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md) — estimator-default decision.
* [`../theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) — sample-size formulas.
* [`../theory/proofs/mri_mask.md`](../theory/proofs/mri_mask.md) — MRI mask family handling.
* [`../theory/proofs/pet_reduction.md`](../theory/proofs/pet_reduction.md) — PET activity vs scan-time decision.
* [`../theory/proofs/composition.md`](../theory/proofs/composition.md) — why composition is not derivable.
* [`../experiments/cross_modality_consistency/`](../experiments/cross_modality_consistency/) — synthetic proof of modality-general API.
* [`../experiments/estimator_coverage/`](../experiments/estimator_coverage/) — coverage simulation.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the contribution policy. The
policy defines two sign-off tiers — Tier A (two of three maintainers) for
changes to `framework_hash.py`, `credential.py`, `credential_schema.py`,
`estimator.py`, `sample_size.py`, and `operators.py`; Tier B (one
maintainer) for documentation, tests, tutorials, examples, and
API-additive changes — plus the schema-mutation discipline, testing
floor, security-disclosure window, and license intent.

## Citation

See [`CITATION.cff`](CITATION.cff) (CFF v1.2.0). The preferred citation
is the *Nature Methods* manuscript (in preparation); the CFF also
declares a software-citation entry for the library itself.

## License

Apache 2.0 ([LICENSE](LICENSE)).
