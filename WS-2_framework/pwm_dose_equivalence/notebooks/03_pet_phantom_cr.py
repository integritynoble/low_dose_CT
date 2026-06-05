# %% [markdown]
# # Tutorial 3 — PET NEMA NU-2 IQ phantom contrast-recovery at 25 % activity
#
# This tutorial shows how to compute a credential for a **PET phantom
# task** — specifically, contrast-recovery (CR) on the NEMA NU-2 IQ
# phantom at 25 % injected activity. Two things make this tutorial
# different from the patient-cohort tutorials:
#
# 1. **Small per-credential n.** A single NEMA phantom acquisition gives
#    6 paired CR measurements (one per sphere). Even 5 acquisitions only
#    gives n = 30 — small enough that the percentile bootstrap can become
#    anti-conservative.
# 2. **The small-n warning fires for n < 30** per `proofs/estimator.md`
#    §4c (V3-11). The library helpfully warns you when you're in that
#    regime so you don't over-interpret a `PASS` / `FAIL` verdict.
#
# **What you will learn:**
# 1. How to compute a credential on a per-sphere contrast-recovery
#    metric (per the PET worked example in the manuscript)
# 2. Why n = 30 (≥ 5 phantom acquisitions) is the recommended cohort
# 3. How the small-n anti-conservativeness warning surfaces
# 4. How activity-reduction is canonical (`theory/proofs/pet_reduction.md`)

# %% [markdown]
# ## 1. Setup

# %%
import warnings

import numpy as np

from pwm_dose_equivalence import Task, signal_equivalence_credential

rng = np.random.default_rng(seed=42)

# %% [markdown]
# ## 2. Simulate paired per-sphere CR measurements
#
# In a real experiment, you would acquire the phantom at full activity
# and at 25 % activity, run both reconstruction methods on each
# acquisition, measure per-sphere CR, and report the paired differences.
# We simulate the same with σ_Δ = 0.02 (typical phantom statistics —
# physical measurements are tight) on n = 30 spheres total.

# %%
n_spheres = 30                # 5 acquisitions × 6 NEMA spheres each
sigma_delta = 0.02            # typical per-sphere CR-difference SD

deltas = rng.normal(0.0, sigma_delta, size=n_spheres)
b = rng.normal(0.85, 0.04, size=n_spheres)
a = b + deltas

print(f"n spheres   = {n_spheres}  (≈ 5 phantom acquisitions × 6 spheres)")
print(f"σ_Δ          = {sigma_delta:.3f}")

# %% [markdown]
# ## 3. Issue the credential
#
# The estimator auto-selects to percentile (no DeLong for CR). The
# PET T_r is **activity reduction** (Poisson-thinning of list-mode counts
# at rate r) per `theory/proofs/pet_reduction.md`; scan-time-reduction
# is a v2 distinction.

# %%
with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    cred = signal_equivalence_credential(
        paired_a=a, paired_b=b,
        signal_ratio=0.25,
        modality="PET",
        task=Task("contrast_recovery", metric="contrast_recovery"),
        subpopulation="nema_nu2_iq_phantom_18FDG_activity_reduction_v1",
        epsilon=0.02,                 # v0.3 non-AUC default
        alpha=0.05,
        n_bootstrap=10_000,
        seed=42,
        sigma_delta_hint=sigma_delta,
    )

print(f"Estimator: {cred.credential.estimator}")
print(f"Δ̄         = {cred.credential.delta_mean:.5f}")
print(f"95 % CI   = [{cred.credential.delta_ci_low:.5f}, "
      f"{cred.credential.delta_ci_high:.5f}]")
print(f"Verdict    = {cred.credential.verdict.value}")
print()
print("Warnings raised:")
for w in ws:
    print(f"  - {w.category.__name__}: {w.message}")
if not ws:
    print("  (none — n = 30 is at the recommended minimum)")

# %% [markdown]
# ## 4. What happens at n < 30? The small-n warning
#
# A single NEMA phantom acquisition gives only n = 6 CR measurements.
# The library warns you that the percentile bootstrap is anti-
# conservative in this regime (coverage 0.82–0.93 per
# `proofs/estimator.md` §4c). The verdict should be read with
# extra caution.

# %%
n_small = 6                       # one phantom acquisition
deltas_small = rng.normal(0.0, sigma_delta, size=n_small)
b_small = rng.normal(0.85, 0.04, size=n_small)
a_small = b_small + deltas_small

with warnings.catch_warnings(record=True) as ws_small:
    warnings.simplefilter("always")
    cred_small = signal_equivalence_credential(
        paired_a=a_small, paired_b=b_small,
        signal_ratio=0.25,
        modality="PET",
        task=Task("contrast_recovery", metric="contrast_recovery"),
        subpopulation="nema_nu2_iq_phantom_18FDG_activity_reduction_v1",
        epsilon=0.02, alpha=0.05,
        n_bootstrap=10_000, seed=43,
    )

print(f"Small-cohort verdict (n = {n_small}): "
      f"{cred_small.credential.verdict.value}")
print()
print("Warnings raised:")
for w in ws_small:
    print(f"  - {w.category.__name__}: {w.message}")

# %% [markdown]
# ## 5. Recommended PET phantom cohort
#
# Per `theory/proofs/estimator.md` §4c (the V3-11 finding):
#
# | n  | Coverage  | Practical interpretation              |
# |----|-----------|---------------------------------------|
# | 6  | 0.82–0.88 | **too small** — single acquisition; bootstrap anti-conservative |
# | 12 | 0.88–0.93 | borderline — 2 acquisitions; still below nominal |
# | **30** | **0.93–0.96** | **recommended** — 5 acquisitions; calibrated |
# | 60 | 0.93–0.96 | upper end — 10 acquisitions; over-engineered for ε = 0.02 |
#
# At n ≥ 30 the percentile bootstrap returns to nominal coverage. The
# library's small-n warning helps you avoid the n < 30 regime
# accidentally; the warning text points you at the §4c writeup.

# %% [markdown]
# ## 6. Credential JSON
#
# As with the other tutorials, the credential serialises to a JSON
# document that bears the framework-version hash. A reader of your
# credential can resolve the framework definition by hash and
# re-run the same library against your published method on the
# same phantom data.

# %%
print(cred.to_json(indent=2)[:1200] + " ...")
