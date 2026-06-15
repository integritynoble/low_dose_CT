"""pwm_ldct_recon — WS-3 reference low-dose CT reconstruction method.

The *improvable* reference of the WS-3 plan (see ``WS-3_reference_method/README.md``):
an unrolled iterative reconstruction (physical Radon prior + a shared-weight learned
denoiser per iteration), with deep-ensemble uncertainty quantification, that emits the
Phase-3 derived-data corpus the *Scientific Data* Data Descriptor describes.

Pipeline (what each module owns)::

    physics.py    parallel-beam Radon forward/adjoint (differentiable) -- the data term
    models/       U-Net denoiser + the unrolled reconstruction loop
    data.py       (low, full, sinogram) pairs over the WS-1 pwm_ldct_loader
    train.py      train one seeded model -> checkpoint
    ensemble.py   K seeded models -> recon_mean + per-pixel uncertainty (ensemble std)
    detector.py   pluggable FROZEN downstream-task detector (nnDetection/LUNA16)
    emit_corpus.py  ensemble inference over a split x dose set -> the deposit corpus

``emit_corpus.run`` is the **Phase-3 corpus run** entry point: it produces exactly the
record layout the synthetic ``fixture/`` stands in for, but from real ensemble inference,
then drives the existing ``corpus_emit`` / ``deposit`` tools (credentials + manifest).
"""
from __future__ import annotations

from .config import EnsembleConfig, ReconConfig
from .physics import RadonTransform
from .models import UNetDenoiser, UnrolledRecon

__all__ = [
    "ReconConfig",
    "EnsembleConfig",
    "RadonTransform",
    "UNetDenoiser",
    "UnrolledRecon",
]
__version__ = "0.1.0"
