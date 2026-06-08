# Credential reading guide

**For reviewers, regulators, and clinicians who need to *interpret* a published signal-equivalence credential — without writing code.**

If you can read JSON, you can read a credential. This guide tells you what each field means, what verdict words you should trust, and what red flags should prompt a follow-up question.

If you *can* write code, the companion document is [`reproduction_guide.md`](reproduction_guide.md), which tells you how to **re-derive** the credential from the published sources.

---

## 1. What a credential is

A signal-equivalence credential is a JSON document a method's authors publish alongside their reconstruction method. It is a structured assertion of the form:

> "Our method `M` produces task outputs on reduced-signal scans that are within $\varepsilon$ of a named reference method `M_ref` on full-signal scans, with confidence $1 - \alpha$, on patient subpopulation `Π`."

That assertion is *machine-verifiable* (someone else can re-run the same library on the same test set and check the verdict) and *content-addressed* (it carries a cryptographic hash of the framework version it was issued against, so the meaning of the assertion is pinned).

A credential is **not**:

* A claim that the candidate method is *better* than the reference (that's superiority, a different test).
* A claim about a different reduction ratio, different task, different cohort, or different reference than the ones listed.
* A claim about whether you should personally trust the method clinically — that is your decision based on the credential plus the surrounding evidence.

---

## 2. The credential JSON, field-by-field

A real credential looks like this:

```json
{
  "schema_version": "pwm-signal-equivalence/v0.2",
  "framework_hash": "sha256:b366f51c11a8fbdfc7b60f1f977d42a10a8bdaa55521b43de0c428afc289fb58",
  "credential": {
    "method":            "my_method",
    "reference_method":  "FBP_full_dose",
    "signal_ratio":      0.25,
    "modality":          "CT",
    "task":              {"name": "lung_nodule_5mm",
                          "metric": "auc",
                          "target": null,
                          "ground_truth_protocol":
                            "pwm-ldct/annotation-qa/v0.5#sha256:..."},
    "subpopulation":     "adult_chest_pwm_l3_test_v1",
    "epsilon":           0.05,
    "alpha":             0.05,
    "estimator":         "delong",
    "n_test":            500,
    "n_bootstrap":       0,
    "seed":              42,
    "delta_mean":        -0.012,
    "delta_ci_low":      -0.034,
    "delta_ci_high":     0.011,
    "verdict":           "PASS",
    "sample_size_check": {"rule": "S3-auc-clt",
                          "placement_sd_hint": 0.15,
                          "n_required": 246,
                          "n_actual": 500,
                          "ok": true}
  }
}
```

The exact JSON Schema this credential conforms to is exported from the library as `CREDENTIAL_JSON_SCHEMA` (in `pwm_dose_equivalence.credential_schema`). One `json.dumps(CREDENTIAL_JSON_SCHEMA)` gives you the machine-readable copy if you want to validate a credential outside Python.

> **Schema-evolution note.** The v0.2 schema carries `method` and `reference_method` as bare strings (slugs only). A future v1.0 schema will widen them to `{"name": "...", "code_hash": "sha256:..."}` for full method-bundle provenance. Until then, the `framework_hash` field anchors the *framework version* the credential commits to; method-bundle provenance is recorded separately at the publication venue (Docker image hash in the supplementary materials, pip release hash on PyPI, etc.).

Field by field:

| Field | What it means | What you check |
|---|---|---|
| `schema_version` | Which version of the credential schema the authors used | Should be the latest schema you recognise; older schemas are historical |
| `framework_hash` | SHA-256 of the framework definition the credential commits to | Resolve by hash; if it doesn't match a framework version you trust, ask for clarification. The library's `audit_credential` function checks this automatically |
| `method` | The candidate method slug | A descriptive name. v0.2 emits a bare string; v1.0 will widen to `{name, code_hash}` |
| `reference_method` | The reference method slug (FBP at full dose, vendor IR at full dose, etc.) | A *credible* reference. If it is unfamiliar, ask what it is |
| `signal_ratio` (= `r`) | The reduction ratio. `0.25` = 25 % of the reference signal | Check this matches the authors' marketing claim. A 50 %-dose-reduction claim should have `r = 0.5` |
| `modality` | `CT`, `MRI`, `PET`, or a user-defined string | Should match the modality you care about |
| `task` | The clinical task this credential asserts equivalence on | A credential at `lung_nodule_5mm` is **silent** about, e.g., ground-glass-opacity characterisation |
| `task.ground_truth_protocol` | The reader-panel adjudication protocol the labels followed | Should resolve to a documented protocol (board-certified reader panel + calibration gate + consolidation rule) |
| `subpopulation` (= `Π`) | The patient cohort the credential asserts equivalence over | An adult-chest credential is silent about pediatric / oncology-followup populations |
| `epsilon` (= `ε`) | The equivalence margin. Smaller = stricter claim | Reasonable defaults: 0.05 for AUC tasks, 0.02 for Dice / MAE / contrast-recovery. **If ε is much larger than these, ask why** |
| `alpha` (= `α`) | The significance level. `0.05` = 95 % confidence | Standard. Larger than 0.10 is suspicious |
| `estimator` | The CI computation method | `delong` for AUC; `percentile` for general metrics; `bca` is opt-in. **`bca` as the headline result is a yellow flag** (BCa does not robustly outperform percentile under the null) |
| `n_test` | The cohort size the credential was issued on | The single biggest determinant of whether the verdict is trustworthy |
| `delta_mean`, `delta_ci_low`, `delta_ci_high` | The observed performance gap + its 95 % CI | The verdict is determined by whether the CI fits inside `(-ε, ε)` — see §3 |
| `verdict` | `PASS`, `FAIL`, or `INDETERMINATE` | See §3 for what each one means |
| `sample_size_check` | The pre-flight sanity check on whether `n_test` was adequate | `"ok": false` means the cohort was too small for the chosen `(ε, α)` |

---

## 3. Reading the verdict

The verdict is one of three words. The framework refuses to issue any other word.

### `PASS`

The 95 % CI `[delta_ci_low, delta_ci_high]` is *fully inside* the equivalence band `(-ε, ε)`. The data are consistent with equivalence; under standard assumptions, the authors have shown the methods agree to within the margin they claimed.

A `PASS` does **not** mean the methods are *identical*. It means the difference is bounded by `ε` at confidence `1 − α`.

### `FAIL`

The 95 % CI is *fully outside* the equivalence band — either entirely above `+ε` or entirely below `−ε`. The data are inconsistent with equivalence. The authors have evidence *against* their own equivalence claim. If they publish this credential, they are being transparent about a negative result.

### `INDETERMINATE`

The 95 % CI *straddles* one of the equivalence band's boundaries. The data are consistent with *both* equivalence and non-equivalence at the chosen `(ε, α)`. The framework refuses to commit either way.

**`INDETERMINATE` is not a failure to issue a credential.** It is the honest answer when the data do not justify a stronger claim. The most common causes are:

1. The cohort is too small (most common; see `sample_size_check`).
2. The per-patient variance is high relative to the margin.
3. The methods *are* close to the boundary — neither demonstrably equivalent nor demonstrably non-equivalent at the chosen `ε`.

A research group publishing many `INDETERMINATE` credentials on small cohorts is honestly acknowledging cohort-size limits. That is good practice, not a red flag.

---

## 4. The sample-size sanity check

If the credential carries a `sample_size_check` field with `"ok": false`, the cohort was below the formula prescription at the chosen `(ε, α)`. A `PASS` verdict in that regime should be read with caution: the verdict is more likely to be a fluke than a reliable equivalence claim. Specifically:

* For AUC tasks at the v0.3 default `ε = 0.05`, the WS-1 PWM-LDCT v0.5 cohort of n ≈ 208 patients is *exactly* in the regime where INDETERMINATE-but-truly-equivalent is the modal outcome. P(`PASS`) under the null is approximately **0.40** at n = 200, lifting to 0.94 at n = 500. This means: **on a cohort of ≈ 208 patients, *absence* of a `PASS` verdict is not evidence of non-equivalence** — only of insufficient n.
* For Dice / MAE / contrast-recovery tasks at the v0.3 default `ε = 0.02`, the same cohort is comfortably above the formula prescription at typical variability values. A `PASS` on these tasks is more meaningful at the same n.

Numerical anchors for these claims are in [`theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) §3 and [`theory/proofs/estimator.md`](../theory/proofs/estimator.md) §§4a / 4b / 4c.

---

## 5. The framework hash — what it guarantees and what it does not

The `framework_hash` field is the SHA-256 of the framework definition the credential commits to. It guarantees:

1. **Provenance.** A reader of the credential can resolve the hash to the exact framework specification the authors used. There is no ambiguity about "which framework" they validated against.
2. **Tamper detection.** If the authors silently re-evaluate the credential against a later framework version after publication, the hash will not match the published one. A re-evaluated verdict gets a new hash; the old hash continues to point at the old, smaller-evidence specification.
3. **Independent re-derivation.** A reviewer can pull the framework spec by hash, install the library at the matching version, run the same paired-bootstrap on the same test set, and check the verdict bit-for-bit.

The hash does **not** guarantee:

* That the *test data* are correct (separate dataset-hash discipline).
* That the *method bundle* is what the authors claim (separate `method.code_hash` field).
* That the *task ground truth* is reliable (separate `ground_truth_protocol` field).

A complete audit checks all three hashes plus the framework hash.

---

## 6. Common reviewer / regulator questions

**Q. The verdict is `PASS`. Should I approve the method?**
A. Not on the credential alone. A credential is one piece of evidence that the method achieves the *equivalence* claim it asserts. It is silent about: surgical-quality reader studies, regulatory pathway, post-market surveillance, vendor support life-cycle. Read the credential as "the equivalence claim is internally consistent and statistically supported" — not as a clinical-deployment recommendation.

**Q. The verdict is `INDETERMINATE`. Is the method bad?**
A. Probably not. The most common cause is that the cohort is too small for the chosen `(ε, α)`. See §4. Ask the authors what cohort size would resolve to `PASS` or `FAIL`, and whether they plan to expand.

**Q. The cohort `n_test` is small (say, < 30 for a non-AUC metric). Should I trust the verdict?**
A. Be cautious. Below n = 30 for non-AUC metrics the percentile-bootstrap CI is *anti-conservative* — it can be too narrow, which inflates the `PASS` rate slightly above what the nominal `α` would suggest. The library issues an explicit warning in this regime. The verdict is still meaningful but should be cross-checked against a domain expert's prior.

**Q. The credential was issued at `epsilon = 0.10`. Is that lax?**
A. For AUC tasks the v0.3 manuscript's recommended default is `0.05`. A credential at `0.10` is a *weaker* claim — methods that differ by 10 percentage points of AUC are deemed equivalent. Ask the authors why they used a wider margin than the recommended default. For Dice / MAE / contrast-recovery the recommended default is `0.02`; `0.10` is very loose.

**Q. The estimator field says `bca` instead of `percentile` or `delong`. Is that a problem?**
A. BCa is a legitimate estimator, but the v0.3 manuscript's recommended default is *not* BCa: BCa does not robustly outperform percentile under the null, and is opt-in only. A credential using BCa as the headline result is not wrong, but should also be reported alongside a percentile-bootstrap version. The library writes both bounds into the credential's `sample_size_check` field; ask for the percentile-CI version.

**Q. The credential references a `subpopulation` slug I don't recognise. What is it?**
A. The slug should resolve to an operational description of the cohort: inclusion criteria, scanner / vendor / kVp / mask family / tracer (whichever apply), and the dataset spec. Ask the authors for the operational description. A credential whose subpopulation slug is opaque is one whose claim cannot be transferred to your context.

**Q. Two credentials from the same authors on the same dataset have different verdicts. Which do I trust?**
A. Likely they are at different operating points (different `r`, different task `T`, different `epsilon`). Each credential is a separately-verifiable claim. Read them both — they are not in conflict; they are answering different questions.

---

## 7. Red flags

These should prompt follow-up questions before you act on the credential:

| Red flag | Why it matters |
|---|---|
| `framework_hash` not resolvable / not on the registry | Provenance broken; you cannot verify what specification was tested |
| `audit_credential()` returns `ok=False` | The credential is internally inconsistent — verdict does not match its CI, or schema fields are missing or out of range. See §7a |
| Method bundle (Docker image / pip release) hash not published alongside the credential | The method is not pinned; the authors may be silently iterating between issuances. The v0.2 schema does not yet carry a `method.code_hash` field, so this discipline lives at the publication venue |
| `subpopulation` slug not resolvable | You cannot tell who is in the cohort; can't transfer the claim |
| `ground_truth_protocol` undocumented (or `null`) | The labels could be of unknown quality |
| `epsilon` much larger than the v0.3 default for the metric | Lax equivalence claim; may not be clinically meaningful |
| `estimator = "bca"` *without* a percentile companion | BCa as headline result not recommended; ask for the percentile version. `audit_credential()` emits this warning automatically |
| `n_test` much smaller than `sample_size_check.n_required` | The verdict may be a fluke; cohort below formula prescription. `audit_credential()` flags this when the verdict is `PASS` |
| Same-day commit hash on the credential AND on the method bundle | Possible cherry-picking; ask for a longitudinal record |
| Credentials only published when `verdict = "PASS"` (selective reporting) | Publication bias; ask for the full ledger of issued credentials |

A credential that has none of these flags is *internally consistent*. Whether it is *clinically sufficient* remains your call.

### 7a. The `audit_credential` shortcut

If you have Python installed, you can run every *internal-consistency* check above (schema validity, verdict self-consistency, framework-hash recognition, sample-size-check coherence, BCa-headline warning) in one call:

```python
from pwm_dose_equivalence import audit_credential
import json

report = audit_credential(json.load(open("their_credential.json")))
print(report.ok)                   # True iff every hard check passed
print(report.issues)               # list of failed checks (hard issues)
print(report.warnings)             # list of soft signals (non-blocking)
```

If you would rather not write any Python, the library installs a console entry point that does the same thing from the shell:

```bash
pwm-audit their_credential.json              # human-readable summary
pwm-audit their_credential.json --json       # machine-readable JSON report
cat their_credential.json | pwm-audit -      # read from stdin
```

The exit code mirrors the verdict: `0` if `ok=True`, `1` if any hard issue, `2` on I/O or argument error. Drop `pwm-audit` into a CI pipeline or a paper-submission checklist and any credential that fails internal consistency will block the workflow.

The audit (library call or CLI) does *not* re-run the bootstrap — that requires the original test-set scores and is the job of `reproduction_guide.md`. The audit *does* verify that the published verdict is what the published CI implies, that the framework hash is one this library version recognises, that the schema is intact, and that no soft signals (BCa-as-headline, undersized cohort with PASS) have been silently issued. Most of the red flags above translate to a check in `audit_credential`; the remainder (subpopulation slug resolution, method-bundle hash, selective reporting) require institutional context the credential JSON cannot carry on its own.

### 7b. Worked examples

The library ships a small `examples/` directory with one clean credential and six deliberately-broken variants — one per audit signal — so a reviewer can see what each red flag *actually looks like* in the JSON and in the `pwm-audit` output:

| File | Demonstrates | Expected exit |
|---|---|---|
| `examples/valid_ct_lung_nodule.json` | Clean PASS credential at the WS-1 v0.5 lung-nodule operating point | `0` (OK, no warnings) |
| `examples/failures/tampered_verdict.json` | `verdict` flipped to FAIL on a PASSing CI | `1` (hard issue: `verdict_self_consistent = False`) |
| `examples/failures/inverted_ci.json` | `delta_ci_low > delta_ci_high` | `1` (hard issue: empty CI) |
| `examples/failures/missing_field.json` | Required `verdict` field removed | `1` (hard issue: schema invalid) |
| `examples/failures/unknown_framework_hash.json` | `framework_hash` replaced with a different SHA-256 | `0` (soft warning: framework version not recognised) |
| `examples/failures/undersized_pass.json` | `PASS` verdict with `sample_size_check.ok = False` | `0` (soft warning: cohort below formula prescription) |
| `examples/failures/bca_headline.json` | `estimator = "bca"` as the headline result | `0` (soft warning: BCa is opt-in per `proofs/estimator.md` §4) |

The examples are regenerated from `examples/regenerate.py` (fixed seed = 42); `tests/test_examples.py` catches drift if any file is hand-edited. The on-disk `credential_schema.json` (top-level of the library) is the same `CREDENTIAL_JSON_SCHEMA` dict serialised to a stand-alone JSON Schema file for non-Python validators.

---

## 8. Cross-references

* [`manuscript.tex`](manuscript.tex) v0.3 — the framework paper itself
* [`CHANGELOG.md`](CHANGELOG.md) — what changed and when
* [`reproduction_guide.md`](reproduction_guide.md) — the *technical positive-claim* companion for reviewers who write code
* [`limitations_anchors.md`](limitations_anchors.md) — the *negative-claim* companion mapping each V3-12 manuscript limitation to its supporting proofs / simulation / roadmap milestone
* [`../theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) — formal sample-size derivation
* [`../theory/proofs/estimator.md`](../theory/proofs/estimator.md) — formal coverage + power discussion
* [`../pwm_dose_equivalence/notebooks/`](../pwm_dose_equivalence/notebooks/) — four tutorial notebooks for users learning to *issue* credentials
* `pwm_dose_equivalence.audit.audit_credential` — Python API for the internal-consistency checks described in §7a
* `pwm-audit` — shell entry point installed alongside the library (§7a)
* `pwm_dose_equivalence.credential_schema.CREDENTIAL_JSON_SCHEMA` — the machine-readable JSON Schema this guide describes
* [`../pwm_dose_equivalence/credential_schema.json`](../pwm_dose_equivalence/credential_schema.json) — standalone JSON Schema artifact for non-Python validators
* [`../pwm_dose_equivalence/examples/`](../pwm_dose_equivalence/examples/) — clean + 6 broken example credentials, one per audit signal (§7b)

---

*Reading guide v1.3 — 2026-06-08 (D9 + 19). Aligned with manuscript v0.3 + library v0.2.2 + `examples/` directory + standalone `credential_schema.json`. Pairs with `reproduction_guide.md`. v1.0 → v1.1: reconciled JSON example to match the v0.2 schema's bare-string `method` field; added §7a `audit_credential` shortcut and schema-evolution note. v1.1 → v1.2: §7a documented the `pwm-audit` CLI. v1.2 → v1.3: added §7b "Worked examples" linking to `examples/` (one clean + six broken credentials, one per audit signal) and the standalone `credential_schema.json` artifact for non-Python validators.*
