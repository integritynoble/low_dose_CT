"""Model registry for the v0.5 baseline reproductions.

RED-CNN is implemented faithfully. The other three method classes named in the manuscript
(a transformer-, a diffusion-, and an unrolled-iterative reconstruction method) are deliberately
left as registry stubs: faithful reproduction requires each method's published implementation +
weights/config, and the specific method choices are still open (manuscript \\todo). Register them
here once selected; the train/eval harness is method-agnostic (any nn.Module mapping
low-dose [B,1,H,W] -> denoised [B,1,H,W] plugs in).
"""
from __future__ import annotations

import torch.nn as nn

from .red_cnn import REDCNN

_REGISTRY = {
    "red_cnn": REDCNN,
    # "ctformer": ...,   # TODO(select published transformer method) — manuscript Tech. Validation
    # "diffusion": ...,  # TODO(select published diffusion method)
    # "learn": ...,      # TODO(select published unrolled-iterative method, e.g. LEARN)
}

PENDING = ("transformer", "diffusion", "unrolled")


def get_model(name: str) -> nn.Module:
    if name not in _REGISTRY:
        raise NotImplementedError(
            f"model {name!r} is not implemented. Available: {sorted(_REGISTRY)}. "
            f"The manuscript's other baselines ({', '.join(PENDING)}) need their published "
            f"implementations + a method-selection decision before registration."
        )
    return _REGISTRY[name]()


def available_models():
    return sorted(_REGISTRY)
