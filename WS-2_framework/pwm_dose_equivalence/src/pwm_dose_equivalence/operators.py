"""Modality-specific signal-reduction operators :math:`T_r`.

Each operator maps a full-signal acquisition ``s_ref`` to a reduced-signal
acquisition at ratio ``r``. The operators are pure functions of the inputs
and the RNG; their statistical properties match the modality's physics:

* CT — Poisson-thinning at rate r (Beer-Lambert linearity in expected count)
* PET — Poisson-thinning at rate r (activity reduction; see
  ``theory/proofs/pet_reduction.md`` for the activity-vs-scan-time decision)
* MRI — variable-density Cartesian k-space mask retaining fraction r; the
  unsampled entries are NaN-marked so downstream estimators can ignore them
  without coupling the mask to a value-comparison heuristic (see
  ``theory/proofs/mri_mask.md`` for the mask-family-in-Pi decision)
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt


def Tr_ct(s_ref: npt.NDArray[Any], r: float, rng: np.random.Generator) -> npt.NDArray[Any]:
    """Poisson-thinning of CT photon counts at rate ``r``."""
    if not 0 < r <= 1:
        raise ValueError("r must be in (0, 1]")
    return rng.binomial(s_ref.astype(np.int64), r)


def Tr_pet(s_ref: npt.NDArray[Any], r: float, rng: np.random.Generator) -> npt.NDArray[Any]:
    """Poisson-thinning of PET list-mode counts at rate ``r`` (activity reduction)."""
    if not 0 < r <= 1:
        raise ValueError("r must be in (0, 1]")
    return rng.binomial(s_ref.astype(np.int64), r)


def Tr_mri(
    s_ref: npt.NDArray[Any], r: float, rng: np.random.Generator,
    *, central_fraction: float = 0.25,
) -> npt.NDArray[Any]:
    """Variable-density Cartesian k-space mask at acceleration ``1 / r``.

    A fraction ``central_fraction`` of the kept lines is placed at the
    k-space centre (a fully-sampled auto-calibration region); the remainder
    is drawn uniformly at random from the periphery. Unsampled positions are
    NaN-marked.
    """
    if not 0 < r <= 1:
        raise ValueError("r must be in (0, 1]")
    if not 0 < central_fraction <= 1:
        raise ValueError("central_fraction must be in (0, 1]")
    n = s_ref.shape[-1]
    n_keep = max(1, int(np.ceil(r * n)))
    mask = np.zeros(n, dtype=bool)
    n_center = max(1, int(n_keep * central_fraction))
    c0 = n // 2 - n_center // 2
    mask[c0 : c0 + n_center] = True
    n_extra = n_keep - n_center
    if n_extra > 0:
        edges = np.flatnonzero(~mask)
        extra = rng.choice(edges, size=n_extra, replace=False)
        mask[extra] = True
    out = np.full_like(s_ref, np.nan, dtype=np.float64)
    out[mask] = s_ref[mask]
    return out
