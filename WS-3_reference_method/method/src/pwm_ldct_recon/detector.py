"""Frozen downstream-task detector (manuscript sec:detector).

The credentialed task is lung-nodule detection (v1 is lung-nodule-only; manuscript M3).
The detector is **frozen**: nnDetection (self-configuring 3D Retina U-Net) trained once on
LUNA16, never fine-tuned on PWM-LDCT, with its operating point fixed on the LUNA16
validation FROC *before* scoring any reconstruction. Released task maps are raw pre-threshold
scores. This module is the plug point: a real run registers the pinned nnDetection model;
the deterministic stub below exists only so the pipeline and tests run without the weights.

Contract: a detector maps a reconstruction volume ``[Z,H,W]`` (or ``[1,Z,H,W]``) to a
same-shaped per-voxel score map in [0,1]. It must be deterministic and stateless across calls.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np


class FrozenDetector(Protocol):
    """A frozen, deterministic task scorer. ``name``/``version`` go into the corpus metadata."""

    name: str
    version: str

    def score_map(self, volume: np.ndarray) -> np.ndarray:
        """Per-voxel task score in [0,1], same spatial shape as ``volume``."""
        ...


class NNDetectionDetector:
    """Adapter for the pinned LUNA16-trained nnDetection model (manuscript sec:detector).

    Not runnable until the weights/config are deposited (Phase-3 ``\\todo`` pin).
    Constructing it is fine. **Importing it is not free in a bare environment**: this module
    is normally reached through the package ``__init__``, which imports ``.physics`` and so
    ``torch``, and ``from pwm_ldct_recon.detector import NNDetectionDetector`` therefore
    raises ``ModuleNotFoundError`` where that optional heavy dependency is absent.

    Both entry points raise ``RuntimeError``, not ``NotImplementedError``: ``load()``
    because ``nndet`` is not installed, and ``score_map()`` because ``_model`` is never
    assigned. The ``NotImplementedError`` in ``score_map`` marks the unwritten inference
    path; it is unreachable until ``load()`` is implemented to set ``_model``, and is not a
    live error path today.
    """

    name = "nndetection"

    def __init__(self, version: str = "TODO-pin", weights_path: str | None = None):
        self.version = version
        self.weights_path = weights_path
        self._model = None

    def load(self) -> "NNDetectionDetector":
        try:
            import nndet  # noqa: F401
        except Exception as e:  # pragma: no cover - depends on optional heavy dep
            raise RuntimeError(
                "nnDetection not installed; `pip install pwm_ldct_recon[detector]` and "
                "deposit the pinned LUNA16 weights (manuscript sec:detector)."
            ) from e
        raise NotImplementedError(
            "Wire the pinned LUNA16 nnDetection inference here at Phase-3 freeze time."
        )

    def score_map(self, volume: np.ndarray) -> np.ndarray:  # pragma: no cover - needs weights
        if self._model is None:
            raise RuntimeError("call load() with the pinned weights before scoring.")
        raise NotImplementedError


class DeterministicStubDetector:
    """A frozen, deterministic blob-response stub. NOT the real detector -- pipeline/tests only.

    Produces a smooth local-contrast response so score maps are inspectable and reproducible,
    standing in for nnDetection scores until the real model is wired.
    """

    name = "stub_local_contrast"
    version = "stub-0"

    def score_map(self, volume: np.ndarray) -> np.ndarray:
        v = np.asarray(volume, dtype=np.float32)
        squeezed = v[0] if v.ndim == 4 and v.shape[0] == 1 else v
        # local mean via a small box filter (cumulative-sum trick, axis-last 2D per slice)
        out = np.empty_like(squeezed)
        flat = squeezed.reshape(-1, *squeezed.shape[-2:]) if squeezed.ndim == 3 else squeezed[None]
        res = np.empty_like(flat)
        for i, sl in enumerate(flat):
            local = 0.25 * (
                np.roll(sl, 1, 0) + np.roll(sl, -1, 0) + np.roll(sl, 1, 1) + np.roll(sl, -1, 1)
            )
            resp = np.abs(sl - local)
            mn, mx = float(resp.min()), float(resp.max())
            res[i] = (resp - mn) / (mx - mn + 1e-8)
        out = res.reshape(squeezed.shape)
        return out.reshape(v.shape) if v.ndim == 4 else out
