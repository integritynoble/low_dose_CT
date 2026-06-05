# %% [markdown]
# # Tutorial 4 — Extending the framework to a new modality (Optical)
#
# Tutorials 1–3 covered the three validated modalities (CT / MRI / PET).
# This tutorial demonstrates the framework's design promise: the API is
# **modality-general by construction**, and a user can extend it to any
# modality with a measurable signal-reduction operator $T_r$ — without
# modifying the library.
#
# We work through *Optical / fluorescence* imaging as a worked example.
# The manuscript's Methods Table 1 specifies the operator as:
#
# > **Optical:** Reduced exposure time. If $s_{\text{ref}} \sim
# > \text{Poisson}(\phi(x) \cdot t_{\text{ref}})$, then
# > $s_{\text{red}} \sim \text{Poisson}(\phi(x) \cdot r \cdot t_{\text{ref}})$
#
# The manuscript flags this modality as "not validated; user-implementable"
# (Methods Table 7). This tutorial closes that claim with a concrete
# end-to-end implementation.
#
# **What you will learn:**
# 1. How to write a custom `T_r` operator for a new modality
# 2. How to plug it into the existing `signal_equivalence_credential`
#    API without modifying the library
# 3. Why optical's `T_r` is mathematically identical to CT's (both are
#    Poisson-thinning) — and how the modality-general design exploits
#    this without conflating the two scientifically
# 4. What `subpopulation` field metadata Optical-specific credentials
#    should carry

# %% [markdown]
# ## 1. Setup

# %%
import numpy as np

from pwm_dose_equivalence import (
    Task, Tr_ct, signal_equivalence_credential,
)

rng = np.random.default_rng(seed=42)

# %% [markdown]
# ## 2. Implement `Tr_optical` (your modality-specific operator)
#
# Per the Methods Table 1, optical signal reduction is Poisson-thinning of
# the photon-count distribution at rate $r$. This is **mathematically the
# same operator** as `Tr_ct` (and `Tr_pet`) — but it is *scientifically* a
# different modality because the underlying $\Pi$ (subpopulation +
# acquisition-protocol metadata) is different: optical imaging records
# fluorescence intensity from a labelled specimen, with reduced exposure
# time as the signal-reduction mechanism, rather than X-ray attenuation
# with reduced tube current.
#
# Three implementation options for `Tr_optical`:
#
# 1. **Re-use `Tr_ct` directly.** Cleanest. Trade-off: a casual reader of
#    your code might wonder why a CT operator is being used on optical
#    data; the credential's `subpopulation` field is what disambiguates.
# 2. **Define a thin wrapper.** Type-safer; documents intent.
# 3. **Implement from scratch.** Most flexible if you ever need to add
#    optical-specific physics (e.g.\ wavelength-dependent quantum
#    efficiency).
#
# We use option 2 here.

# %%
def Tr_optical(
    s_ref: np.ndarray, r: float, rng: np.random.Generator,
) -> np.ndarray:
    """Poisson-thinning of optical photon counts at exposure-time ratio r.

    Identical kernel to ``Tr_ct``; the semantic distinction lives in the
    ``Π`` metadata of the credential, not in the operator.
    """
    if not 0 < r <= 1:
        raise ValueError("r must be in (0, 1]")
    return Tr_ct(s_ref, r, rng)


# Sanity check: Tr_optical at r=1 is the identity (no thinning)
s_full = np.full(64, 100, dtype=np.int64)
assert (Tr_optical(s_full, r=1.0, rng=np.random.default_rng(0))
        == s_full).all()
print("Tr_optical(., r=1.0) == identity: OK")

# %% [markdown]
# ## 3. Simulate paired per-specimen scores at 25 % exposure
#
# In a real experiment, you would:
# 1. Acquire reference fluorescence images at full exposure time `t_ref`
# 2. Acquire reduced-exposure images at `r * t_ref` on the same specimen
# 3. Run both reconstruction methods on the reduced and reference signals
# 4. Compute a per-specimen task score (e.g., region-of-interest
#    fluorescence intensity, signal-to-noise ratio, or feature-detection
#    accuracy)
#
# Here we simulate paired per-specimen Dice-like scores with σ_Δ = 0.05
# (typical for reconstruction-method comparison on optical phantoms or
# tissue cultures).

# %%
n_specimens = 80          # typical optical-imaging cohort
sigma_delta = 0.05

# Both methods are truly equivalent; per-specimen difference noise only
b = rng.normal(0.78, 0.04, size=n_specimens)
deltas = rng.normal(0.0, sigma_delta, size=n_specimens)
a = b + deltas

print(f"n specimens = {n_specimens}")
print(f"σ_Δ          = {sigma_delta:.3f}")

# %% [markdown]
# ## 4. Issue the credential
#
# **The key point:** we use the *same* `signal_equivalence_credential`
# API call we used for the three validated modalities. The library does
# not know that this is optical data — it doesn't need to. The
# `modality` field is a string tag for the credential JSON; the
# `subpopulation` field carries the acquisition-protocol metadata that
# distinguishes optical from CT.
#
# Note we pass `modality="Optical"` — the library accepts arbitrary
# strings; the validated modalities are CT / MRI / PET, but the type
# discipline does not lock out user-implemented modalities. The
# manuscript's Methods Table 7 flags this explicitly: *"`Optical`:
# specified; not validated; user-implementable."*

# %%
cred = signal_equivalence_credential(
    paired_a=a, paired_b=b,
    signal_ratio=0.25,                          # 25 % of reference exposure time
    modality="Optical",                         # NEW modality tag
    task=Task("roi_fluorescence_intensity", metric="dice"),
    subpopulation="zebrafish_embryo_488nm_GFP_exposure_reduction_v1",
    epsilon=0.02, alpha=0.05,
    n_bootstrap=10_000, seed=42,
    sigma_delta_hint=sigma_delta,
)

print(f"Estimator used: {cred.credential.estimator}")
print(f"Δ̄             = {cred.credential.delta_mean:.5f}")
print(f"95 % CI       = [{cred.credential.delta_ci_low:.5f}, "
      f"{cred.credential.delta_ci_high:.5f}]")
print(f"Verdict       = {cred.credential.verdict.value}")
print(f"Modality tag  = {cred.credential.modality}")

# %% [markdown]
# ## 5. The `subpopulation` field is the load-bearing metadata
#
# Per `theory/proofs/mri_mask.md` and manuscript §framework clarification
# C5: $\Pi$ carries the acquisition-protocol metadata that determines
# `T_r` for the modality. For optical imaging, this includes:
#
# * The fluorophore (e.g. GFP / mCherry / fluorescein)
# * The excitation wavelength (e.g. 488 nm / 561 nm)
# * The exposure-time-reduction protocol (the operator implementation)
# * The specimen class (e.g. zebrafish embryo, HeLa cells, tissue slice)
# * Camera + microscope model
#
# The slug `"zebrafish_embryo_488nm_GFP_exposure_reduction_v1"` we used
# above is a placeholder for a content-addressed acquisition-protocol
# document. A reader of the credential resolves this slug to the
# operational spec, runs the same library against the same protocol,
# and verifies the verdict — exactly as for the validated modalities.

# %% [markdown]
# ## 6. Cross-modality consistency the user gets for free
#
# Because the library's `signal_equivalence_credential` did not care
# what modality the operator came from, your custom `Tr_optical` plus
# the validated `Tr_ct` / `Tr_mri` / `Tr_pet` can be tested together
# under the same cross-modality consistency framework that
# `experiments/cross_modality_consistency/` demonstrates for CT/MRI/PET
# in Results Table 2. **Same code path; one more modality.**
#
# This is the operational meaning of "modality-general by construction"
# in the manuscript abstract. The validated modalities are the ones we
# ship with worked examples and `T_r` implementations; user-implemented
# modalities follow the same discipline and produce credentials of
# identical schema shape — verifiable, content-addressed, comparable.

# %% [markdown]
# ## 7. What you would do next, on real optical data
#
# To turn this synthetic demonstration into a real Scientific Data
# release for an optical-imaging method:
#
# 1. **Define the acquisition protocol.** Write up the fluorophore,
#    wavelength, exposure-time reduction rule, and camera settings;
#    deposit it under a stable URL and reference it from the
#    `subpopulation` slug.
# 2. **Acquire paired data.** Reference + 25 % exposure on the same
#    specimens, repeated for ≥ n specimens per the (S1) sample-size
#    formula at your target `(ε, α, σ_Δ)`. For Dice-type metrics at
#    σ_Δ = 0.05, ε = 0.02, n ≈ 25 per `proofs/sample_size.md` §3.1.
# 3. **Compute the credential.** Run this notebook, swapping the
#    synthetic `a` / `b` arrays for your real per-specimen scores.
# 4. **Publish the credential JSON.** The framework hash is the same;
#    any reader can resolve it to the canonical framework spec and
#    verify your verdict bit-for-bit.
#
# No library modification is required at any step. That is the
# modality-general design.
