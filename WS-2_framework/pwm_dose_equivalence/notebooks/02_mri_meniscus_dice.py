# %% [markdown]
# # Tutorial 2 — MRI knee-meniscus segmentation at 4× acceleration (Dice)
#
# This tutorial shows how to compute a signal-equivalence credential for
# an **MRI segmentation task** at the v0.3 non-AUC default ε = 0.02. The
# input here is per-patient Dice scores (one number per patient per
# method), so the estimator path is **percentile bootstrap** (no DeLong
# analog for Dice).
#
# The MRI mask family rides inside Π (per `theory/proofs/mri_mask.md`);
# the variable-density Cartesian R = 4 mask is encoded in the
# `subpopulation` slug.
#
# **What you will learn:**
# 1. How to provide paired per-patient Dice scores (the (S1) general-
#    metric setting)
# 2. How `sigma_delta_hint` triggers the sample-size pre-flight check
#    (both CLT (S1) and Bernstein (S4) bounds reported)
# 3. How the cohort-sizing implication for Dice differs from AUC
#    (P(`PASS`) under the null = 1.000 at n = 200, vs ≈ 0.40 for AUC)
# 4. How the small-n anti-conservativeness warning fires when n < 30

# %% [markdown]
# ## 1. Setup

# %%
import numpy as np

from pwm_dose_equivalence import Task, signal_equivalence_credential

rng = np.random.default_rng(seed=42)

# %% [markdown]
# ## 2. Simulate paired per-patient Dice scores
#
# In a real experiment, you would have:
# * `paired_a[k]`: your candidate method's Dice on patient k
# * `paired_b[k]`: the reference method's Dice on the **same** patient k
#
# We simulate both with the (S1) generative model
# Δ_k = a_k − b_k ∼ Normal(0, σ_Δ²), reflecting truly-equivalent methods
# with per-patient variability σ_Δ = 0.05 typical of MRI knee-meniscus
# segmentation in the literature.

# %%
n_patients = 200          # the WS-1 v0.5-comparable cohort size
sigma_delta = 0.05        # typical per-patient Dice-difference SD

# Anchor the reference around realistic clinical Dice ≈ 0.82 ± noise
b = rng.normal(0.82, 0.04, size=n_patients)
# Candidate is truly equivalent: a_k = b_k + small noise
deltas = rng.normal(0.0, sigma_delta, size=n_patients)
a = b + deltas

print(f"n patients   = {n_patients}")
print(f"mean Dice (a) ≈ {a.mean():.3f}")
print(f"mean Dice (b) ≈ {b.mean():.3f}")
print(f"σ_Δ           = {sigma_delta:.3f}")

# %% [markdown]
# ## 3. Issue the credential
#
# Three things happen:
#
# 1. The estimator auto-selects to **percentile bootstrap** because the
#    task metric is `dice` (not `auc`). No DeLong analog.
# 2. We pass `sigma_delta_hint = 0.05` so the library runs the (S1) CLT
#    and (S4) Bernstein sample-size checks and writes them into the
#    credential's `sample_size_check` field. A `UserWarning` fires if
#    n is below the formula prescription.
# 3. The MRI mask family is recorded inside the subpopulation slug — the
#    5-tuple shape holds verbatim across modalities per
#    `theory/proofs/mri_mask.md`.

# %%
import warnings

with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25,            # equivalently R = 1/0.25 = 4×
        modality="MRI",
        task=Task("meniscus_dice", metric="dice"),
        subpopulation="fastmri_knee_vd_cartesian_R4_v1",
        epsilon=0.02,                 # v0.3 non-AUC default per V3-1
        alpha=0.05,
        n_bootstrap=10_000,
        seed=42,
        sigma_delta_hint=sigma_delta,
    )

print(f"Estimator used: {cred.credential.estimator}")
print(f"Δ̄  (observed) = {cred.credential.delta_mean:.4f}")
print(f"95 % CI       = [{cred.credential.delta_ci_low:.4f}, "
      f"{cred.credential.delta_ci_high:.4f}]")
print(f"Verdict        = {cred.credential.verdict.value}")
print()
print("Warnings raised:")
for w in ws:
    print(f"  - {w.category.__name__}: {w.message}")
if not ws:
    print("  (none — cohort comfortably above all formula prescriptions)")

# %% [markdown]
# ## 4. Inspect the sample-size check
#
# Because we passed `sigma_delta_hint`, the credential carries an
# explicit pre-flight record showing the (S1) CLT and (S4) Bernstein
# sample-size requirements at the requested `(ε, α, σ_Δ)`.

# %%
sample_check = cred.credential.sample_size_check
print("sample_size_check fields:")
for k, v in sample_check.items():
    print(f"  {k:25s}: {v}")

# %% [markdown]
# ## 5. Cohort-sizing comparison: Dice vs AUC
#
# At n = 200 (the WS-1 v0.5-comparable cohort):
#
# | Metric    | σ_Δ-relative-to-ε | P(`PASS`) under null |
# |-----------|-------------------|----------------------|
# | AUC = 0.92 | placement-s 0.15 / ε 0.05 | ≈ 0.40 |
# | **Dice** | σ_Δ 0.05 / ε 0.02 | **= 1.000** |
#
# Dice tasks are *substantively easier* to certify at the WS-1 v0.5
# cohort size than AUC tasks, because the variance-relative-to-margin
# ratio is much narrower. A downstream researcher computing a Dice
# credential on n = 200 patients should expect `PASS` under the null,
# **not** the INDETERMINATE-dominated regime that AUC inherits.
#
# Per `theory/proofs/estimator.md` §4b (V3-10), this holds at clinical
# σ_Δ ∈ [0.05, 0.10]. At higher σ_Δ (noisier segmentation tasks), the
# Dice cohort-sizing parallels the AUC case.

# %% [markdown]
# ## 6. (Optional) Force a different estimator
#
# By default the library auto-selects percentile for non-AUC metrics.
# For visible-skew bootstrap distributions you can opt into BCa
# (Efron 1987 bias-corrected accelerated). v0.2.0 exposes this.

# %%
cred_bca = signal_equivalence_credential(
    paired_a=a, paired_b=b,
    signal_ratio=0.25,
    modality="MRI",
    task=Task("meniscus_dice", metric="dice"),
    subpopulation="fastmri_knee_vd_cartesian_R4_v1",
    epsilon=0.02, alpha=0.05,
    n_bootstrap=10_000, seed=42,
    estimator="bca",                  # opt-in for BCa
)
print(f"BCa verdict: {cred_bca.credential.verdict.value}")
print(f"BCa CI:      [{cred_bca.credential.delta_ci_low:.4f}, "
      f"{cred_bca.credential.delta_ci_high:.4f}]")
