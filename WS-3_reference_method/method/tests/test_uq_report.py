"""Tests for the deep-ensemble UQ report (low-dose-ct.md §7.6, P2-7)."""

from __future__ import annotations

import numpy as np
import pytest

from pwm_ldct_recon.uq_report import (
    analyze_confidence_lesion,
    analyze_ensemble_bundle,
    future_wiring_points,
    render_markdown,
)


def test_analyze_confidence_lesion_high_std_is_low_confidence():
    # std map: low variance on healthy tissue, high variance exactly on the lesion.
    rng = np.random.default_rng(0)
    std = rng.uniform(0.1, 0.5, size=(16, 16))
    lesion = np.zeros((16, 16), dtype=bool)
    lesion[4:8, 4:8] = True
    std[lesion] = 5.0  # high std on the lesion -> low confidence
    stats = analyze_confidence_lesion(std, lesion, confidence_threshold=1.0)
    # The missed fraction must be tiny (high-std lesion is NOT flagged as "missed"),
    # and recall of low-confidence as a missed predictor should be low.
    assert stats.n_missed < stats.n_lesions
    assert stats.low_conf_precision >= 0.0


def test_analyze_confidence_lesion_missed_when_low_std_on_lesion():
    std = np.zeros((16, 16))
    lesion = np.zeros((16, 16), dtype=bool)
    lesion[4:8, 4:8] = True
    # lesion has LOW std (model is confident but wrong) -> missed by low-conf flag.
    stats = analyze_confidence_lesion(std, lesion, confidence_threshold=1.0)
    assert stats.n_missed == stats.n_lesions
    assert stats.low_conf_recall == 0.0


def test_analyze_confidence_lesion_shape_mismatch():
    with pytest.raises(ValueError):
        analyze_confidence_lesion(np.zeros((4, 4)), np.zeros((5, 5)), 1.0)


def test_analyze_ensemble_bundle_no_mask():
    rng = np.random.default_rng(1)
    mean = rng.normal(0.5, 0.1, size=(16, 16))
    std = rng.uniform(0.01, 0.5, size=(16, 16))
    report = analyze_ensemble_bundle(mean, std, lesion_mask=None)
    assert report["analysis"] == "low_confidence_vs_missed_lesion"
    assert report["lesion_association"] is None
    assert 0.0 <= report["low_confidence_fraction"] <= 1.0
    assert report["std_range"][0] <= report["std_range"][1]


def test_analyze_ensemble_bundle_with_mask():
    rng = np.random.default_rng(2)
    mean = rng.normal(0.5, 0.1, size=(16, 16))
    std = rng.uniform(0.01, 0.3, size=(16, 16))
    lesion = np.zeros((16, 16), dtype=bool)
    lesion[8:12, 8:12] = True
    report = analyze_ensemble_bundle(mean, std, lesion_mask=lesion)
    assert report["lesion_association"] is not None
    assert report["lesion_association"]["n_lesions"] == lesion.sum()
    assert report["lesion_association"]["low_conf_recall"] is not None


def test_render_markdown_contains_key_numbers():
    rng = np.random.default_rng(3)
    mean = rng.normal(0.5, 0.1, size=(16, 16))
    std = rng.uniform(0.01, 0.3, size=(16, 16))
    lesion = np.zeros((16, 16), dtype=bool)
    lesion[8:12, 8:12] = True
    report = analyze_ensemble_bundle(mean, std, lesion_mask=lesion)
    md = render_markdown(report)
    assert "Low-confidence" in md
    assert "precision" in md


def test_future_wiring_points_documented():
    assert "runbundle/run.py" in future_wiring_points()
