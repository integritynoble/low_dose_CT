# Cross-modality consistency experiment

Synthetic validation that the same paired-bootstrap code path produces the
expected signal-equivalence verdict when applied to three modality-specific
signal-reduction operators. Backs the WS-2 manuscript's modality-general claim
with reproducible numbers rather than rhetoric.

---

## What it does

For each of three modalities, two candidate methods are evaluated against a
reference method at signal-reduction ratio `r = 0.25`, equivalence margin
`epsilon = 0.05`, and significance level `alpha = 0.05` on `n = 200`
synthetic patients with `B = 10,000` bootstrap replicates:

| Modality | `T_r` operator                                |
|---|---|
| CT  | Poisson-thinning of full-signal photon counts |
| MRI | Variable-density Cartesian k-space subsampling (1/4 of kept lines fully sample the centre) |
| PET | Poisson-thinning of list-mode counts          |

The two candidates per modality are:

| Candidate    | Construction                                                       | Expected verdict |
|---|---|---|
| `equivalent` | unbiased ML estimator on the reduced signal (acquisition noise only) | `PASS` |
| `biased`     | same estimator + additive bias `0.10 > epsilon`                    | `FAIL` |

All six credentials are issued by the *single* `signal_equivalence_credential`
function in the script. The operator `T_r` is the only modality-specific
component; no modality-specific branching occurs in the bootstrap or in the
verdict logic.

---

## Run

```bash
python3 cross_modality_consistency.py
```

Requires `numpy`. No other dependencies. Writes `results.json` alongside the
script; full reproducibility from `seed = 42`.

---

## Result at `seed = 42`

```
Modality  Candidate       delta_mean      CI low     CI high  Verdict
---------------------------------------------------------------------
CT        equivalent         -0.0067     -0.0156      0.0022  PASS
CT        biased              0.1011      0.0924      0.1096  FAIL
MRI       equivalent          0.0010     -0.0023      0.0044  PASS
MRI       biased              0.0986      0.0954      0.1018  FAIL
PET       equivalent         -0.0031     -0.0135      0.0076  PASS
PET       biased              0.0915      0.0816      0.1013  FAIL
```

All three equivalent candidates pass; all three biased candidates fail. The
modality-general claim is therefore not rhetorical: the same code path
discriminates equivalence from non-equivalence correctly under three different
acquisition physics.

---

## What this experiment is and is not

**It is** the cross-modality consistency anchor for the WS-2 manuscript's
modality-general claim — evidence that the *software* generalises, not just
the *idea*.

**It is not** a substitute for the per-modality empirical worked examples
(Results Tables 2–4 in the manuscript), which require real patient data and
land with the WS-2 Phase 1 / Phase 3 milestones. The clinical credentials are
the load-bearing science; this script is the methods-side sanity check.

---

## Cross-references

- [`../../paper_draft/manuscript.tex`](../../paper_draft/manuscript.tex) — the
  Results subsection *"Cross-modality consistency on synthetic data"* reports
  the table above.
- [`../../theory/dose-equivalence-framework.md`](../../theory/dose-equivalence-framework.md)
  — formal definition this script implements.
- [`../../theory/open_questions.md`](../../theory/open_questions.md) §3 —
  estimator coverage simulations; this experiment is a step toward that work
  but is not a substitute for the full coverage table.
