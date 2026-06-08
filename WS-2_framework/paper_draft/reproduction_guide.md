# Reproduction guide

**For reviewers of the v0.3 manuscript.** This document tells a reviewer how to verify, end-to-end, every numerical claim in the *Signal-equivalence: testable dose-reduction claims for medical imaging* manuscript using the released artifacts. Every concrete number in the manuscript has an anchor in the repository — this guide names that anchor and the command that re-derives the number.

The manuscript is `paper_draft/manuscript.tex` v0.3 (24 pp incl. Supplementary S1). All artifacts referenced here live in [`WS-2_framework/`](.) and are seed-reproducible.

---

## 0. Install

```bash
git clone git@github.com:integritynoble/low_dose_CT.git
cd low_dose_CT/WS-2_framework/pwm_dose_equivalence
pip install -e ".[test]"
pytest                               # expect: 81 passed, 100% coverage
```

Requires Python 3.10+, NumPy ≥ 1.24, SciPy ≥ 1.10.

---

## 1. Reproduce the cross-modality consistency table (Results §, Table 2)

The manuscript's Results section advertises a 6-row table showing the same paired-bootstrap code path producing 3 PASS + 3 FAIL verdicts across CT, MRI, and PET on synthetic data at seed = 42.

```bash
cd ../experiments/cross_modality_consistency
python3 cross_modality_consistency.py
```

The script writes `results.json`. Read it back:

```python
import json
print(json.load(open("results.json"))["credentials"])
```

**Expected output (verbatim from `paper_draft/manuscript.tex` Table 2):**

```
Modality  Candidate       delta_mean   CI low     CI high    Verdict
CT        equivalent      -0.0067     -0.0156    0.0022     PASS
CT        biased           0.1011      0.0924    0.1096     FAIL
MRI       equivalent       0.0010     -0.0023    0.0044     PASS
MRI       biased           0.0986      0.0954    0.1018     FAIL
PET       equivalent      -0.0031     -0.0135    0.0076     PASS
PET       biased           0.0915      0.0816    0.1013     FAIL
```

A bit-mismatch here indicates either a NumPy version difference (the binomial RNG implementation changed between major NumPy versions) or a different `seed`. The Apache-2.0 LICENSE bundle pins the expected NumPy major version.

---

## 2. Reproduce the estimator coverage simulation (Methods §, `proofs/estimator.md` §2)

The 27-cell AUC coverage table in `proofs/estimator.md` §2 verifies that the percentile / BCa / DeLong CI variants attain nominal 95 % coverage under the truly-equivalent null. Wall time ≈ 35 min.

```bash
cd ../estimator_coverage
python3 coverage_sim.py              # writes results.json
```

Expected results (verbatim from `proofs/estimator.md` §2):

| Target AUC | n | percentile | BCa | DeLong |
|---:|---:|---:|---:|---:|
| 0.85 | 500 | 0.945 | 0.950 | 0.960 |
| 0.92 | 500 | 0.925 | 0.930 | 0.940 |
| 0.97 | 500 | 0.975 | 0.935 | 0.975 |

(Full 27-row table in `proofs/estimator.md` §2.)

---

## 3. Reproduce the non-null power simulation (Methods §, `proofs/estimator.md` §4a)

The 24-cell power table verifies the framework's power to FAIL at $\Delta_{\text{true}} = 2\varepsilon$ and conservative INDETERMINATE behaviour at the boundary. Wall time ≈ 25 min.

```bash
python3 power_sim.py                 # writes power_results.json
```

Expected: at AUC = 0.92, $n = 500$, $\Delta_{\text{true}} = 0.10$: P(`FAIL`) = 1.000 for both percentile and DeLong (verbatim from `proofs/estimator.md` §4a).

---

## 4. Reproduce the Dice + CR sims (Methods §, `proofs/estimator.md` §§4b / 4c)

Closes the AUC-only caveat the v0.1 of that document had carried. Wall time ≈ 2.5 + 3 min.

```bash
python3 dice_sim.py                  # 18 cells; writes dice_results.json
python3 cr_sim.py                    # 24 cells; writes cr_results.json
```

**Headline checks** (from `proofs/estimator.md` §§4b / 4c):

* `dice_results.json[Δ=0.00, σ_Δ=0.05, n=200]["p_pass"] == 1.000` — compare to the AUC = 0.92 / n = 200 case where P(`PASS`) = 0.40 (V3-9 finding).
* `cr_results.json[Δ=0.00, σ_Δ=0.02, n=6]["coverage"] ∈ [0.82, 0.88]` — small-n anti-conservativeness (V3-11 finding); n ≥ 30 returns to nominal.

---

## 5. Verify the cross-modality consistency demo via the **production library**

Above, §1 used a standalone script (the prototype that the cross-modality demo was written against). The released library reproduces the same demo through the public API:

```bash
cd ../../pwm_dose_equivalence
pytest tests/test_integration.py::test_cross_modality_consistency_via_public_api -v
```

**Expected:** `PASSED`. The test asserts that all three modalities issue PASS credentials with identical schema shape and identical framework hash.

---

## 6. Verify the content-addressed framework hash (Methods §)

The manuscript claims the framework is content-addressed by SHA-256 of a stable `FRAMEWORK_SPEC` string. To verify the hash matches the spec:

```python
from pwm_dose_equivalence import FRAMEWORK_SPEC, framework_hash
import hashlib
print(framework_hash())   # sha256:<digest>
print("sha256:" + hashlib.sha256(FRAMEWORK_SPEC.encode("utf-8")).hexdigest())
# Both lines must print the same value.
```

Or as a regression test:

```bash
pytest tests/test_framework_hash.py -v
```

---

## 7. Verify the sample-size formulas (Methods §, `proofs/sample_size.md`)

The manuscript's sample-size paragraph gives formulas (S1) general CLT and (S3) paired-AUC DeLong placement-variance, and Supplementary S1 derives the Bernstein (S4) bound. The library implements all three.

```python
from pwm_dose_equivalence import (
    required_n_general, required_n_auc, required_n_bernstein,
)
# proofs/sample_size.md §3.1 row (eps=0.02, sigma_Δ=0.10) → n ≥ 97
assert required_n_general(epsilon=0.02, alpha=0.05, sigma_delta=0.10) == 97
# proofs/sample_size.md §3.2 row (AUC=0.85, eps=0.02, s=0.20) → n ≥ 1540
assert 1537 <= required_n_auc(epsilon=0.02, alpha=0.05, placement_sd=0.20) <= 1540
# Supplementary S1 numerical comparison: (eps=0.05, sigma=0.10, M=1) → n ≥ 50
assert required_n_bernstein(
    epsilon=0.05, alpha=0.05, sigma_delta=0.10, bound_M=1.0,
) == 50
```

Or:

```bash
pytest tests/test_sample_size.py -v
```

---

## 8. Verify the BCa / small-n warning / bound_M v0.2.0 additions

Library v0.2.0 added BCa exposure, small-$n$ anti-conservativeness warning, and `bound_M` for unbounded metrics. The v0.3-evidence-completion CHANGELOG section documents these as L0.2-1 / L0.2-2 / L0.2-3.

```bash
pytest tests/test_v020_features.py -v
```

Expected: 11 tests pass.

---

## 9. Issue a credential on your own method (Quickstart)

For a reviewer who wants to compute a credential using their own reconstruction method:

```python
import numpy as np
from pwm_dose_equivalence import signal_equivalence_credential, Task

# Replace these with your own per-patient scores
n = 200
rng = np.random.default_rng(42)
my_method_scores      = rng.normal(0.82, 0.05, size=n)
reference_method_scores = rng.normal(0.82, 0.05, size=n)

cred = signal_equivalence_credential(
    paired_a=my_method_scores,
    paired_b=reference_method_scores,
    signal_ratio=0.25,
    modality="CT",
    task=Task("liver_dice", metric="dice"),
    subpopulation="my_test_set_v1",
    epsilon=0.05, alpha=0.05,
    n_bootstrap=10_000, seed=42,
    sigma_delta_hint=0.05,        # triggers (S1) sample-size pre-flight
)
print(cred.to_json(indent=2))
```

The credential JSON includes the framework hash (anchors the framework version), the bootstrap CI, the verdict (`PASS` / `FAIL` / `INDETERMINATE`), and the `sample_size_check` field with both CLT and Bernstein bounds.

---

## 10. Per-claim anchor table

A reviewer can locate any concrete numerical claim in the manuscript by consulting this table:

| Manuscript claim | Anchor | Re-derive |
|---|---|---|
| Cross-modality consistency: 6 verdicts | Results § Table 2 | §1 above; `experiments/cross_modality_consistency/results.json` |
| AUC coverage table (27 cells) | `proofs/estimator.md` §2 | §2 above; `experiments/estimator_coverage/results.json` |
| AUC power table (24 cells) | `proofs/estimator.md` §4a | §3 above; `experiments/estimator_coverage/power_results.json` |
| Dice coverage + power (18 cells) | `proofs/estimator.md` §4b | §4 above; `experiments/estimator_coverage/dice_results.json` |
| CR coverage + power (24 cells) | `proofs/estimator.md` §4c | §4 above; `experiments/estimator_coverage/cr_results.json` |
| n ≥ 97 at ε = 0.02, σ_Δ = 0.10 (S1 example) | `proofs/sample_size.md` §3.1 | §7 above |
| n ≥ 1540 at AUC = 0.85, ε = 0.02 (S3 example) | `proofs/sample_size.md` §3.2 | §7 above |
| Bernstein vs CLT ratio ≈ 3.2 at canonical AUC operating point | Supplementary S1; `proofs/sample_size.md` §4 | §7 above |
| `pwm-signal-equivalence/v0.2` schema_version | `framework_hash.py` `FRAMEWORK_SPEC` | §6 above |
| 60/100% library coverage (manuscript §software_rigor) | `pwm_dose_equivalence/` test suite (v0.1.0 numbers per V3-3) | `pytest --cov` |
| AUC default ε = 0.05 (vs non-AUC ε = 0.02) | `proofs/sample_size.md` §5 | §7 above shows formula-derivation |
| INDETERMINATE-dominated regime for WS-1 v0.5 cohort (n ≈ 208) at AUC = 0.92 | `proofs/estimator.md` §4a "Cohort-sizing implication" | §3 above; inspect P(`PASS`) at AUC = 0.92, n = 200 |
| CR small-n anti-conservativeness (n < 30) | `proofs/estimator.md` §4c | §4 above; inspect `cr_results.json` |
| Library version 0.1.0 / schema v0.2 (§Code availability) | `pyproject.toml` + V3-8 framing | `pip show pwm_dose_equivalence` |
| `mask_family` rides inside Π (§framework / C5) | `proofs/mri_mask.md` | textual; no number to re-derive |
| PET activity-reduction canonical (Table 1 footnote) | `proofs/pet_reduction.md` | textual |
| Composition not derivable (§Point-evaluated by design) | `proofs/composition.md` | textual |
| Conditional monotonicity conjecture (§Discussion future-work) | `proofs/monotonicity.md` | textual; empirical check gated on Phase 1 |

---

## 10a. Companion document for non-coders

This guide is the *technical* reproduction surface. Its companion is [`credential_reading_guide.md`](credential_reading_guide.md) — a field-by-field walk through a published credential JSON for reviewers, regulators, and clinicians who need to *interpret* a credential without re-running the bootstrap themselves. The reading guide covers verdict semantics (PASS / FAIL / INDETERMINATE), CI vs $\varepsilon$ reading, what the framework hash does and does not guarantee, the `sample_size_check` field, common reviewer questions, and a red-flag checklist.

The two guides are deliberately disjoint:

* `reproduction_guide.md` (this document) — "how do I re-derive the numbers?"
* `credential_reading_guide.md` — "how do I read a credential someone else published?"

A complete reviewer-facing surface needs both.

---

## 11. What this guide intentionally does *not* cover

* **Per-modality Results tables (Table 2 CT / Table 3 MRI / Table 4 PET).** These remain `\todo` placeholders in the v0.3 manuscript pending the Phase 1 pilot (CT, D9 + 90) and Phase 3 real-data integrations (MRI fastMRI / PET NEMA NU-2 IQ phantom, D9 + 270). When those land, this guide will gain a §12 anchored at the cohorts' content-addressed manifests.
* **Submission-time fields.** §Author contributions / §Competing interests / §Acknowledgments / §Data availability supplementary table all carry `\todo{}` placeholders that fill at submission. The reproduction guide cannot anchor them until they exist.
* **Literature depth-pass.** `theory/related_work.md` v0.1 seeded the four anchor cites; the depth-pass reading of fastMRI reader studies / CHO-LDCT / Wunderlich–Noo is genuinely external work the reproduction discipline cannot help with.

---

## 12. Reporting a reproduction failure

If any of §§1–8 above fails to reproduce against this guide, please file an issue at `https://github.com/integritynoble/low_dose_CT/issues` with:

* The command you ran
* The expected output (from this guide or the manuscript)
* The actual output
* Your `python --version`, `numpy.__version__`, `scipy.__version__`

The pinned NumPy major version is bundled with the `pyproject.toml` constraint. The library is unit + integration tested at 100 % line coverage; reproduction failures are taken seriously and typically reflect either an environment-pin gap or a manuscript-table typo.

---

*Reproduction guide v1.0 — 2026-06-05 (D9 + 16). Aligned with manuscript v0.3 + library v0.2.0 + `proofs/estimator.md` v0.4.*
