"""WS-4 shared task specification (low-dose-ct.md Rung 1 / Rung 1.2 / Rung 1.4).

The leaderboard scores every submission on the **same declared detection task** used by
WS-1's baselines and WS-3's reference method, so numbers are comparable across WS:

  - SKE (signal-known-exactly) Gaussian lesion: sigma = 2.0 px, peak contrast = 20 HU,
    location known = True, inserted into a tissue ROI (noise ROI HU band [10, 120]).
  - Observers: CNR with Rose criterion >= 3; Channelized Hotelling Observer (CHO) with
    DOG-4 channels; NPWE with eye filter ``rho*exp(-rho/0.2)``.

These constants mirror ``WS-1_dataset/baselines/src/pwm_ldct_baselines/observers.py``
(``PAIRED_TASK``) and ``WS-3_reference_method/method/src/pwm_ldct_recon/evaluation.py``
(``task_config``) exactly. A submission whose detectability numbers were measured on a
different task is not comparable and is rejected by the paired gate.
"""
from __future__ import annotations

TASK_LABEL = "SKE-Gaussian20HU-s2px"

TASK_SPEC = {
    "label": TASK_LABEL,
    "signal": {
        "sigma_px": 2.0,
        "peak_contrast_hu": 20.0,
        "location_known": True,
    },
    "observer": {
        "cnr": {"rose_criterion": 3.0},
        "cho": {"channels": "dog", "n_channels": 4},
        "npwe": {"eye_filter": "rho*exp(-rho/0.2)"},
    },
    "noise_roi_hu_band": [10.0, 120.0],
}

# The permanent Gaussian blur trap (Rung 1.3): sigma = 1.0 px, 5x5 kernel, same as the
# WS-1 baselines and the WS-3 method suite. It never leaves the leaderboard.
BLUR_SPEC = {
    "sigma_px": 1.0,
    "kernel_size": 5,
    "module": "pwm_ldct_recon.models.GaussianBlur (WS-3)",
}

SCHEMA_VERSION = "0.1.0"

# Fidelity fields that must be paired with a detectability field (§4 both-or-neither).
FIDELITY_FIELDS = ("psnr_db", "ssim")

# Discriminating detectability fields: frequency-domain ``detectability-freq-v1``
# ROI BandER. **At least one is required for publishability.**
#
# Rung 1 of RUNG_REGISTRY.md declares BandER the discriminative index and the
# insertion-based indices below "non-discriminative on real anatomy ... reported
# as transparency". The gate did not enforce that until 2026-09-04: it accepted
# any one of CNR/CHO-AUC/NPWE alone, which meant a submission could clear the
# gate on a metric the permanent blur trap *wins*. On the simulated arm the trap's
# CNR exceeds RED-CNN by 1.11-1.19x, CoreDiff by 1.08-1.13x and CTformer by
# 1.90-2.23x at every dose level; on real anatomy CHO-AUC saturates at 1.000 for
# every method. BandER is what separates the trap (8.9-19.0x, blur last 4/4 in
# every vendor group), so it is what the gate must require.
DISCRIMINATING_FIELDS = ("bander_roi",)

# Transparency fields: insertion-based observers. Reported alongside the
# discriminating index per Rung 1, but never sufficient on their own -- a
# submission carrying only these is not publishable.
TRANSPARENCY_FIELDS = ("cnr_mean", "cho_auc_mean", "npwe_mean")

# Every detectability field the gate recognises and carries through to the
# leaderboard entry. Ordered discriminating-first.
DETECTABILITY_FIELDS = DISCRIMINATING_FIELDS + TRANSPARENCY_FIELDS

# Supplementary frequency-domain fields carried when present (not gate criteria).
FREQ_SUPPLEMENTARY_FIELDS = ("bander_full", "roi_tm_auc")
