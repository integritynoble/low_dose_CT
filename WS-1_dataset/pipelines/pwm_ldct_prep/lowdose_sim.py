"""Low-dose simulation (../schema/dataset_schema.md §5.2; manuscript Eq. 1).

Production forward model. Uses ``pwm_core.contrib.modalities.ct_radon`` when importable (the
project's canonical model); otherwise uses the in-repo projection-domain implementation of
manuscript Eq. 1 — a physically-grounded Poisson photon-counting + electronic-noise insertion.

Eq. 1 (per ray ℓ, effective-monochromatic):
    N_r(ℓ) ~ Poisson(I0(ℓ)·r·e^{-s_ref(ℓ)}) + N(0, σ_e²)
    s̃_low(ℓ) = -ln( max(N_r(ℓ), 1) / (I0(ℓ)·r) )
s_ref = forward Radon of the full-dose attenuation image. We reconstruct the projection-domain
noise (s̃_low − s_ref) and insert it into the full-dose image, preserving the signal.

The projector uses scikit-image's Cython ``radon``/``iradon`` when available (fast), else the numpy
reference projector in ``recon_sanity``. The forward projection is computed once per slice and
reused across dose ratios (``simulate_multi``). Approximations (per the manuscript's stated limits):
parallel-beam, per-slice 2-D, monochromatic, uniform bowtie. I0^(0)/σ_e are nominal defaults to be
calibrated per scanner (recorded in metadata).
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

_PWM_CORE_MODEL = "pwm_core.contrib.modalities.ct_radon"
_INREPO_MODEL = "pwm_ldct_prep.lowdose_sim:projection_domain_v1"

# !!! CALIBRATION REQUIRED before production use !!!
# A spot-check on real Mayo CT showed the nominal defaults below produce NON-PHYSICAL noise
# (~hundreds-to-thousands of HU vs the realistic ~tens of HU at quarter dose) because I0/sigma_e
# are uncalibrated and the mu->HU factor (~1000/MU_WATER) amplifies projection-domain noise. I0_REF
# and SIGMA_E MUST be calibrated per scanner so that simulated 25%-dose noise matches the reference
# (AAPM/Mayo noise-inserted) low-dose noise statistics (this is the manuscript's sim-vs-reference
# validation). Treat the current output as a structural placeholder, not calibrated low-dose.
I0_REF = 1.0e5        # incident photon count I0^(0)        [CONFIRM: calibrate per scanner]
SIGMA_E = 10.0        # electronic-noise std (photons)      [CONFIRM: calibrate per scanner]
N_ANGLES = 180        # projection views
MU_WATER = 0.019      # water linear attenuation (~/mm); HU<->mu conversion
HU_FLOOR = -1024.0    # physical HU floor (clip FOV-padding values, e.g. GE -3024, before mu)


def model_name() -> str:
    try:
        import pwm_core.contrib.modalities.ct_radon  # noqa: F401
        return _PWM_CORE_MODEL
    except Exception:
        return _INREPO_MODEL


def _radon(mu: np.ndarray, theta: np.ndarray) -> np.ndarray:
    try:
        from skimage.transform import radon
        return radon(mu, theta=theta, circle=False)            # [n_det, n_angles]
    except Exception:
        from .recon_sanity import parallel_radon
        return parallel_radon(mu, theta).T                     # [n_det(=W), n_angles]


def _iradon(sino: np.ndarray, theta: np.ndarray, size: int) -> np.ndarray:
    try:
        from skimage.transform import iradon
        return iradon(sino, theta=theta, filter_name="ramp", circle=False, output_size=size)
    except Exception:
        from .recon_sanity import fbp
        return fbp(sino.T, theta, out_size=size)


def simulate_multi(volume_hu: np.ndarray, ratios: Sequence[float], seed: int) -> Dict[float, np.ndarray]:
    """Simulate low-dose at several ratios, computing the forward projection once per slice."""
    try:
        from pwm_core.contrib.modalities import ct_radon  # type: ignore
        return {r: ct_radon.simulate_low_dose(volume_hu, ratio=r, seed=seed).astype(np.float32)
                for r in ratios}
    except Exception:
        return _projection_domain_multi(volume_hu, ratios, seed)


def simulate(volume_hu: np.ndarray, ratio: float, seed: int, source: str = "") -> np.ndarray:
    """Single-ratio convenience wrapper (delegates to simulate_multi)."""
    return simulate_multi(volume_hu, [ratio], seed)[ratio]


def _projection_domain_multi(volume_hu, ratios, seed) -> Dict[float, np.ndarray]:
    theta = np.linspace(0.0, 180.0, N_ANGLES, endpoint=False)
    rngs = {r: np.random.default_rng(int(seed) + int(round(r * 1000))) for r in ratios}
    out = {r: np.empty_like(volume_hu, dtype=np.float32) for r in ratios}
    for z in range(volume_hu.shape[0]):
        hu = np.clip(volume_hu[z].astype(np.float64), HU_FLOOR, None)  # drop non-physical FOV padding
        mu = np.clip((hu / 1000.0 + 1.0) * MU_WATER, 0.0, None)
        s_ref = _radon(mu, theta)                              # once per slice
        I = I0_REF * np.exp(-s_ref)
        for r in ratios:
            rng = rngs[r]
            counts = rng.poisson(np.clip(I * r, 0.0, None)) + rng.normal(0.0, SIGMA_E, s_ref.shape)
            s_low = -np.log(np.maximum(counts, 1.0) / (I0_REF * r))
            noise_img = _iradon((s_low - s_ref), theta, mu.shape[0])
            out[r][z] = ((mu + noise_img) / MU_WATER - 1.0).astype(np.float32) * 1000.0
    return out
