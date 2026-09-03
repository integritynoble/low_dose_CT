"""CTformer baseline (registered wrapper around the official implementation).

CTformer: Convolution-free Token2Token Dilated Vision Transformer for
Low-dose CT Denoising (D. Wang, F. Fan, Z. Wu, R. Liu, F. Wang, H. Yu,
Phys. Med. Biol. 68(6), 2023).

Official code: github.com/wdayang/ctformer (vendored under baselines/vendor/ctformer).
The CTformer module already maps [B,1,H,W] -> [B,1,H,W]; we only adapt imports
and expose paper-default construction. Pretrained weights shipped with the
vendor repo are loaded when ``pretrained=True``.
"""
from __future__ import annotations

import os
import sys

import torch.nn as nn

_VENDOR_CTFORMER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "vendor", "ctformer"
)
if _VENDOR_CTFORMER not in sys.path:
    sys.path.insert(0, _VENDOR_CTFORMER)

from CTformer import CTformer as _CTformer  # noqa: E402


class CTformerWrapper(nn.Module):
    """Thin wrapper: official CTformer with paper-default hyper-parameters."""

    def __init__(self, img_size: int = 512, pretrained: bool = False,
                 ckpt: str | None = None, variant: str = "legacy"):
        super().__init__()
        if variant == "compact":
            # Compact 512-adaptation of the official paper config (embed_dim=64/depth=1
            # for img_size=64), scaled up for whole-slice 512x512 inputs. Used for the
            # simulated-domain retrain (fixes the convergence failure of the legacy
            # over-provisioned 768/12-layer build that plateaued at PSNR 42-43).
            cfg = dict(
                img_size=img_size, tokens_type="convolution", in_chans=1,
                embed_dim=192, depth=6, num_heads=8, kernel=32, stride=32,
                mlp_ratio=2.0, token_dim=256,
            )
        else:
            # legacy: original harness construction (over-provisioned, converged poorly)
            cfg = dict(
                img_size=img_size, tokens_type="convolution", in_chans=1,
                embed_dim=768, depth=12, num_heads=12, kernel=32, stride=32,
                mlp_ratio=4.0, token_dim=1024,
            )
        self.model = _CTformer(**cfg)
        if pretrained:
            if ckpt is None:
                ckpt = os.path.join(_VENDOR_CTFORMER, "model_pretrained", "T2T_vit_530000iter.ckpt")
            if os.path.exists(ckpt):
                import torch
                sd = torch.load(ckpt, map_location="cpu", weights_only=False)
                if isinstance(sd, dict) and "state_dict" in sd:
                    sd = sd["state_dict"]
                missing, unexpected = self.model.load_state_dict(sd, strict=False)
                print(f"[ctformer] pretrained loaded: missing={len(missing)} unexpected={len(unexpected)}")
            else:
                print(f"[ctformer] pretrained ckpt not found: {ckpt} (training from scratch)")

    def forward(self, x):
        return self.model(x)


def ctformer() -> CTformerWrapper:
    return CTformerWrapper(img_size=512, pretrained=False, variant="legacy")


def ctformer_small() -> CTformerWrapper:
    """Compact 512-adaptation of the official CTformer paper config (retrain target)."""
    return CTformerWrapper(img_size=512, pretrained=False, variant="compact")
