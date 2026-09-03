"""Model registry for the v0.5 baseline reproductions.

RED-CNN is implemented faithfully. CTformer (Wang et al., PMB 2023) is wrapped from its
official release (vendored under baselines/vendor/ctformer). LEARN (Chen et al., IEEE TMI
2018) is a PyTorch re-implementation of the official MATLAB unrolled-iterative network.
CoreDiff (Gao et al., arXiv:2304.01814) is bridged via its vendored official
diffusion train/eval adapter (baselines/vendor/CoreDiff).
"""
from __future__ import annotations

import torch.nn as nn

from .red_cnn import REDCNN
from .learn import LEARN
from .ctformer_wrapper import CTformerWrapper, ctformer_small
from .corediff_wrapper import CoreDiffWrapper
from .gaussian_blur import GaussianBlur

_REGISTRY = {
    "red_cnn": REDCNN,
    "ctformer": CTformerWrapper,
    "ctformer_small": ctformer_small,
    "learn": LEARN,
    "corediff": CoreDiffWrapper,
    # Standing trap (Rung 1.3 / §4): higher PSNR, fails Rose criterion.
    "blur": GaussianBlur,
}

PENDING = ()


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
