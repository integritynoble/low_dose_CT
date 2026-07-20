"""Prove the NEMA metric math on hand-verified inputs, before any phantom scan exists.

Run:  python -m pytest test_nema_metrics.py -q     (from this directory)
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_phantom import compute_all, decayed_vs_thinned
from nema_metrics import (across_realization_stats, background_variability,
                          bland_altman, contrast_to_noise, percent_contrast_cold,
                          percent_contrast_hot)

HERE = os.path.dirname(os.path.abspath(__file__))


def test_percent_contrast_hot_full_and_partial_recovery():
    assert math.isclose(percent_contrast_hot(4.0, 1.0, 4.0), 100.0)      # perfect recovery
    assert math.isclose(percent_contrast_hot(3.4, 1.0, 4.0), 80.0)       # (2.4/3)*100
    with_ratio8 = percent_contrast_hot(8.0, 1.0, 8.0)
    assert math.isclose(with_ratio8, 100.0)


def test_percent_contrast_cold():
    assert math.isclose(percent_contrast_cold(0.2, 1.0), 80.0)


def test_background_variability_and_cnr():
    bg = [1.0, 1.1, 0.9, 1.0]
    assert math.isclose(background_variability(bg), 8.16496580927726, rel_tol=1e-9)
    assert math.isclose(contrast_to_noise(4.0, 1.0, bg), 3.0 / 0.0816496580927726, rel_tol=1e-9)


def test_bland_altman_bias_and_loa():
    ba = bland_altman([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])   # diffs [0,1,2]
    assert math.isclose(ba["bias"], 1.0)
    assert math.isclose(ba["sd"], 1.0)
    assert math.isclose(ba["loa_low"], 1.0 - 1.96)
    assert math.isclose(ba["loa_high"], 1.0 + 1.96)


def test_across_realization_stats():
    s = across_realization_stats([80.0, 82.0, 78.0])
    assert math.isclose(s["mean"], 80.0)
    assert math.isclose(s["variance"], 8.0 / 3.0)        # pstdev^2
    assert s["n_realizations"] == 3


def test_analyze_phantom_end_to_end_and_decayed_vs_thinned():
    with open(os.path.join(HERE, "fixtures", "roi_means.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    res = compute_all(doc)
    ref = res["per_level"]["reference"]
    assert math.isclose(ref["10"]["crc_percent"], 80.0)
    assert math.isclose(ref["13"]["crc_percent"], 100.0)
    # the central validation: decayed vs thinned CRC agreement (bias ~ 0 by construction)
    ba = decayed_vs_thinned(res["per_level"], "decayed_0p25", "thinned_0p25_r0")
    assert ba["sphere_mm"] == ["10", "13"]
    assert math.isclose(ba["crc_bland_altman"]["bias"], 0.0, abs_tol=1e-9)
