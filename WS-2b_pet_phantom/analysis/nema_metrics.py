"""NEMA NU 2-2018 image-quality metrics for the PWM-PET-IQ dataset.

Pure functions over ROI-mean inputs -- no I/O, no image loading -- so they are fully
unit-testable now, before any phantom scan exists. The image-dependent step (placing the
hot-sphere VOIs and the 12x5 background ROIs on the reconstructed volume) lives in
``extract_roi_means.py``; everything numeric in Technical Validation flows through here.

References: NEMA Standards Publication NU 2-2018, "Image quality, accuracy of attenuation
and scatter corrections" (percent contrast Q, background variability N).
"""
from __future__ import annotations

from statistics import mean, pstdev, stdev
from typing import Dict, List, Sequence


def percent_contrast_hot(c_hot: float, c_bg: float, true_activity_ratio: float) -> float:
    """Percent contrast recovery for a *hot* sphere (NEMA NU 2-2018 Eq. for Q_H,j).

        Q_H = [ (C_hot / C_bg) - 1 ] / [ (a_hot / a_bg) - 1 ] * 100

    ``true_activity_ratio`` = a_hot / a_bg is the *known* sphere:background fill ratio, so
    Q is measured against physical truth (100 % = full recovery).
    """
    if c_bg == 0 or true_activity_ratio == 1:
        raise ValueError("c_bg must be nonzero and true_activity_ratio != 1")
    return ((c_hot / c_bg) - 1.0) / (true_activity_ratio - 1.0) * 100.0


def percent_contrast_cold(c_cold: float, c_bg: float) -> float:
    """Percent contrast for a *cold* sphere: Q_C = (1 - C_cold / C_bg) * 100."""
    if c_bg == 0:
        raise ValueError("c_bg must be nonzero")
    return (1.0 - (c_cold / c_bg)) * 100.0


def background_variability(bg_roi_means: Sequence[float]) -> float:
    """Background variability N_j = SD(bg ROI means) / mean(bg ROI means) * 100 (%).

    Uses the sample standard deviation over the background ROIs (NEMA draws 12 per slice
    across 5 slices = 60 ROIs per sphere size).
    """
    if len(bg_roi_means) < 2:
        raise ValueError("need >= 2 background ROIs")
    m = mean(bg_roi_means)
    if m == 0:
        raise ValueError("background mean is zero")
    return stdev(bg_roi_means) / m * 100.0


def contrast_to_noise(c_hot: float, c_bg: float, bg_roi_means: Sequence[float]) -> float:
    """CNR = (C_hot - C_bg) / SD(background ROI means)."""
    sd = stdev(bg_roi_means)
    if sd == 0:
        raise ValueError("background SD is zero")
    return (c_hot - c_bg) / sd


def bland_altman(x: Sequence[float], y: Sequence[float]) -> Dict[str, float]:
    """Bland-Altman agreement of paired measurements ``x`` (e.g. decayed) vs ``y`` (thinned).

    Returns bias (mean difference), SD of differences, and the 95 % limits of agreement.
    This backs the central ``fig:decayed_vs_thinned`` validation.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x and y must be equal length >= 2")
    diffs = [a - b for a, b in zip(x, y)]
    bias = mean(diffs)
    sd = stdev(diffs)
    return {"bias": bias, "sd": sd,
            "loa_low": bias - 1.96 * sd, "loa_high": bias + 1.96 * sd, "n": len(diffs)}


def across_realization_stats(values_per_realization: Sequence[float]) -> Dict[str, float]:
    """Mean and (population) variance of a metric across seeded thinned realizations.

    Population variance because the released realizations *are* the full set (not a sample
    of a larger population): this quantifies the noise-replicate budget the dataset offers.
    """
    if len(values_per_realization) < 2:
        raise ValueError("need >= 2 realizations")
    return {"mean": mean(values_per_realization),
            "variance": pstdev(values_per_realization) ** 2,
            "n_realizations": len(values_per_realization)}
