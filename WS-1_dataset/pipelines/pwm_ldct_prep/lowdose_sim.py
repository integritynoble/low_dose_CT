"""Low-dose simulation (../schema/dataset_schema.md §5.2; manuscript Eq. 1).

Production forward model. Uses ``pwm_core.contrib.modalities.ct_radon`` when importable (the
project's canonical model); otherwise uses the faithful in-repo projection-domain implementation
of manuscript Eq. 1 below — a physically-grounded Poisson photon-counting + electronic-noise
insertion, not an image-domain approximation.

Eq. 1 (per ray ℓ, effective-monochromatic):
    N_r(ℓ) ~ Poisson(I0(ℓ)·r·e^{-s_ref(ℓ)}) + N(0, σ_e²)
    s̃_low(ℓ) = -ln( max(N_r(ℓ), 1) / (I0(ℓ)·r) )
where s_ref = forward Radon of the full-dose attenuation image, I0 = I0^(0)·b(ℓ) (bowtie b≡1
fallback), σ_e the electronic-noise std, r the dose ratio. We insert the *reconstructed projection-
domain noise* (s̃_low − s_ref) into the full-dose image, so the signal is preserved and only the
dose-dependent noise is added.

Known approximations (consistent with the manuscript's stated limitations): parallel-beam, per-slice
2-D, monochromatic, uniform bowtie. I0^(0)/σ_e are nominal defaults and should be calibrated per
scanner for production fidelity (recorded in metadata). For large volumes this CPU reference model
is slow; pwm_core (GPU) is preferred when available.
"""
from __future__ import annotations

import numpy as np

_PWM_CORE_MODEL = "pwm_core.contrib.modalities.ct_radon"
_INREPO_MODEL = "pwm_ldct_prep.lowdose_sim:projection_domain_v1"

# Nominal calibration (per-scanner [CONFIRM] for production; recorded in metadata).
I0_REF = 1.0e5        # incident photon count I0^(0)
SIGMA_E = 10.0        # electronic-noise std (photons)
N_ANGLES = 180        # projection views for the parallel-beam forward/back projector
MU_WATER = 0.019      # linear attenuation of water (~/mm at effective energy); HU<->mu conversion


def model_name() -> str:
    try:
        import pwm_core.contrib.modalities.ct_radon  # noqa: F401
        return _PWM_CORE_MODEL
    except Exception:
        return _INREPO_MODEL


def simulate(volume_hu: np.ndarray, ratio: float, seed: int, source: str = "") -> np.ndarray:
    """Return a simulated low-dose volume at dose ratio ``ratio`` (same shape, HU)."""
    try:
        from pwm_core.contrib.modalities import ct_radon  # type: ignore
        return ct_radon.simulate_low_dose(volume_hu, ratio=ratio, seed=seed).astype(np.float32)
    except Exception:
        return _projection_domain(volume_hu, ratio, seed)


def _projection_domain(volume_hu: np.ndarray, ratio: float, seed: int) -> np.ndarray:
    """In-repo Eq. 1 projection-domain noise insertion, per 2-D slice (parallel-beam)."""
    from .recon_sanity import fbp, parallel_radon

    rng = np.random.default_rng(int(seed) + int(round(ratio * 1000)))
    angles = np.linspace(0.0, 180.0, N_ANGLES, endpoint=False)
    out = np.empty_like(volume_hu, dtype=np.float32)
    for z in range(volume_hu.shape[0]):
        mu = np.clip((volume_hu[z].astype(np.float64) / 1000.0 + 1.0) * MU_WATER, 0.0, None)
        s_ref = parallel_radon(mu, angles)                      # full-dose line integrals
        I = I0_REF * np.exp(-s_ref)                             # noiseless photon flux
        counts = rng.poisson(np.clip(I * ratio, 0.0, None)) + rng.normal(0.0, SIGMA_E, s_ref.shape)
        s_low = -np.log(np.maximum(counts, 1.0) / (I0_REF * ratio))
        noise_img = fbp((s_low - s_ref), angles, out_size=mu.shape[0])  # reconstruct the noise only
        mu_low = mu + noise_img
        out[z] = ((mu_low / MU_WATER - 1.0) * 1000.0).astype(np.float32)  # back to HU
    return out
