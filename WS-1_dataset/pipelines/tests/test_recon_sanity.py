"""Reconstruction-sanity machinery tests: phantom Radon->FBP round-trip + agreement metric.

Validates the harness itself (the genuinely-passing piece). The real-helical-data check is
approximate/uncalibrated by design (see recon_sanity.py docstring) and is not asserted here.
"""
import numpy as np

from pwm_ldct_prep import recon_sanity as rs


def _disk_phantom(n=64):
    ys, xs = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2.0
    img = np.zeros((n, n), np.float64)
    img[(xs - c) ** 2 + (ys - c) ** 2 <= (n / 4) ** 2] = 1.0
    img[(xs - c) ** 2 + (ys - c) ** 2 <= (n / 8) ** 2] = 2.0   # inner higher-contrast core
    return img


def test_fbp_recovers_phantom_structure():
    img = _disk_phantom(64)
    m = rs.self_consistency(img, n_angles=180)
    # FBP scaling differs, but structure must be recovered -> high correlation
    assert m["pearson_r"] > 0.9, m


def test_agreement_identical_is_zero():
    img = _disk_phantom(32)
    m = rs.agreement(img, img.copy(), tol=1.0)
    assert m["max_abs"] == 0.0
    assert m["rmse"] == 0.0
    assert m["frac_within_tol"] == 1.0
    assert m["pearson_r"] > 0.999


def test_agreement_detects_difference():
    img = _disk_phantom(32)
    other = img + 100.0
    m = rs.agreement(img, other, tol=5.0)
    assert m["max_abs"] == 100.0
    assert m["frac_within_tol"] == 0.0
    assert m["pearson_r"] > 0.99   # constant offset -> still perfectly correlated


def test_radon_shapes():
    img = _disk_phantom(40)
    angles = np.linspace(0, 180, 90, endpoint=False)
    sino = rs.parallel_radon(img, angles)
    assert sino.shape == (90, 40)
    recon = rs.fbp(sino, angles, out_size=40)
    assert recon.shape == (40, 40)


def test_series_check_runs_and_flags_status():
    # random projections -> the check must run and return the honest "uncalibrated" status
    proj = np.random.default_rng(0).standard_normal((12, 16, 4)).astype("float32")
    recon = np.random.default_rng(1).standard_normal((3, 16, 16)).astype("float32")
    m = rs.check_series_projection_recon(proj, recon, {"vendor": "GE"})
    assert m["status"] == "approximate_uncalibrated_parallel_rebin"
    assert "pearson_r" in m and "rmse" in m
    assert rs.check_series_projection_recon(None, recon, {})["status"] == "no_projections"
