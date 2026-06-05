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

Status: **v0.2.0 — alpha**, scaffolded 2026-06-02 (v0.1.0) → extended 2026-06-04 (v0.2.0 adds BCa estimator + small-$n$ anti-conservativeness warning + `bound_M` argument for unbounded metrics). TestPyPI ship at D9 + 365; v1.0.0 alongside paper acceptance.

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

Three pedagogical tutorials in [`notebooks/`](notebooks/), one per validated modality:

* [`01_ct_lung_nodule_auc.py`](notebooks/01_ct_lung_nodule_auc.py) — CT lung-nodule detection at 25 % dose (AUC; DeLong auto-selected; ε = 0.05)
* [`02_mri_meniscus_dice.py`](notebooks/02_mri_meniscus_dice.py) — MRI knee-meniscus segmentation at 4× acceleration (Dice; percentile bootstrap; ε = 0.02)
* [`03_pet_phantom_cr.py`](notebooks/03_pet_phantom_cr.py) — NEMA NU-2 IQ phantom contrast-recovery at 25 % activity (CR; percentile; demonstrates the small-n warning at n = 6)

Each file is a `.py` script with `#%%` cell markers — it runs as a normal Python script *and* as a Jupyter notebook (open in JupyterLab / VS Code / Spyder). The reviewer-facing companion is [`../paper_draft/reproduction_guide.md`](../paper_draft/reproduction_guide.md), which verifies the manuscript's numerical claims.

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

**Current v0.2.0:** 81/81 tests pass at **100 % line coverage** (265/265 statements). The 90 % target from the manuscript's §software-rigor paragraph is the published floor; the library continues to ship well above it. The 81 tests now include 10 end-to-end integration tests in `tests/test_integration.py` covering full credential-issuance pipelines across CT / MRI / PET, cross-modality consistency via the public API, JSON round-trip + framework-hash verification, seeded reproducibility, T_r operator integration, and verdict-distribution transitions (boundary INDETERMINATE; FAIL at $\Delta_{\text{true}} > \varepsilon$ + $n = 500$).

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

---

## Versioning policy

Semantic versioning:

* `MAJOR` — break the credential JSON schema (bumps `FRAMEWORK_SPEC`)
* `MINOR` — add a modality, estimator, or task type; non-breaking
* `PATCH` — bug fix; preserves credential reproducibility

The current version is `0.2.0` (alpha). v0.2.0 added BCa + small-$n$ warning + `bound_M` + integration tests; remaining items on the path to `1.0.0` include macOS / Windows CI runners (currently Linux only) and the manuscript-acceptance fixes the journal review surfaces. `1.0.0` ships alongside the *Nature Methods* paper acceptance with five-year support commitment.

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

## License

Apache 2.0.
