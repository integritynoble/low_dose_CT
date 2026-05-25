"""Low-dose simulation (../schema/dataset_schema.md §5.2; manuscript Eq. 1).

The production forward model is the single source of truth
``pwm_core.contrib.modalities.ct_radon`` (do not reimplement). This module is a thin adapter:
it uses ``pwm_core`` when importable, and otherwise falls back to a clearly-flagged,
non-production image-domain noise approximation so the scaffold runs standalone.
"""
from __future__ import annotations

import numpy as np

_PWM_CORE_MODEL = "pwm_core.contrib.modalities.ct_radon"
_FALLBACK_MODEL = "image_domain_fallback"


def model_name() -> str:
    try:
        import pwm_core.contrib.modalities.ct_radon  # noqa: F401
        return _PWM_CORE_MODEL
    except Exception:
        return _FALLBACK_MODEL


def simulate(volume_hu: np.ndarray, ratio: float, seed: int, source: str = "") -> np.ndarray:
    """Return a simulated low-dose volume at dose ratio ``ratio`` (same shape, HU)."""
    try:
        from pwm_core.contrib.modalities import ct_radon  # type: ignore
        return ct_radon.simulate_low_dose(volume_hu, ratio=ratio, seed=seed).astype(np.float32)
    except Exception:
        return _fallback(volume_hu, ratio, seed)


def _fallback(volume_hu: np.ndarray, ratio: float, seed: int) -> np.ndarray:
    """NON-PRODUCTION image-domain approximation (scaffold/test only).

    Noise standard deviation grows as 1/sqrt(dose); this is a placeholder so the pipeline is
    runnable without pwm_core. It does NOT model projection-domain Poisson statistics, beam
    hardening, or bowtie weighting. Production runs use pwm_core (see model_name()).
    """
    rng = np.random.default_rng(int(seed) + int(round(ratio * 1000)))
    base_sigma = 15.0  # HU, nominal full-dose noise level (placeholder)
    sigma = base_sigma * max(0.0, (1.0 / np.sqrt(max(ratio, 1e-3))) - 1.0)
    return (volume_hu + rng.normal(0.0, sigma, size=volume_hu.shape)).astype(np.float32)
