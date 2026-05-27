"""pwm_ldct_baselines — reproducible reconstruction-baseline harness for PWM-LDCT v0.5.

Trains/evaluates low-dose->full-dose reconstruction models against the harmonized dataset via
``pwm_ldct_loader``, emitting per-dose-level PSNR/SSIM/LPIPS (manuscript Technical Validation).
RED-CNN is implemented; the other published baselines are pluggable (see models/).
"""
from .eval import evaluate, evaluate_to_json
from .models import available_models, get_model
from .train import train

__all__ = ["train", "evaluate", "evaluate_to_json", "get_model", "available_models"]
__version__ = "0.5.0"
