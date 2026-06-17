import numpy as np
import pytest
import torch

from pwm_ldct_recon.measurement import (GeometryUnavailable, HelicalRebinningRequired,
                                        REAL_PAIRED, SIMULATED, extract_slice_fan_sinogram,
                                        measurement_for, rebin_fan_to_parallel)
from pwm_ldct_recon.physics import RadonTransform


def _axial_geometry():
    return {"source_to_isocenter_mm": 500.0, "views_per_rotation": 36,
            "fan_angle_total_rad": 0.8}


def test_rebin_shape_and_constant_preservation():
    V, C = 36, 40
    fan = np.full((V, C), 5.0, dtype="f4")
    betas = np.linspace(0, 2 * np.pi, V, endpoint=False)
    gammas = np.linspace(-0.4, 0.4, C)
    par = rebin_fan_to_parallel(fan, fan_angles=gammas, view_angles=betas, sid=500.0, n_dets=64)
    assert par.shape == (V, 64)
    assert np.isfinite(par).all()
    # rebinning a constant sinogram yields a constant sinogram (interpolation preserves it).
    assert np.allclose(par, 5.0, atol=1e-4)


def test_extract_axial_slice():
    proj = np.random.default_rng(0).normal(size=(36, 40, 8)).astype("f4")
    fan, betas, gammas, sid = extract_slice_fan_sinogram(proj, _axial_geometry(), slice_index=3)
    assert fan.shape == (36, 40)
    assert betas.shape == (36,) and gammas.shape == (40,)
    assert sid == 500.0


def test_extract_helical_raises():
    proj = np.zeros((36, 40, 8), dtype="f4")
    geo = {**_axial_geometry(), "pitch": 1.0}
    with pytest.raises(HelicalRebinningRequired):
        extract_slice_fan_sinogram(proj, geo, slice_index=0)


def test_extract_missing_sid_raises():
    proj = np.zeros((36, 40, 8), dtype="f4")
    with pytest.raises(GeometryUnavailable):
        extract_slice_fan_sinogram(proj, {"fan_angle_total_rad": 0.8}, slice_index=0)


def test_measurement_for_simulated_when_no_projections():
    op = RadonTransform(n_views=36, n_dets=64, img_size=16)
    low = np.random.default_rng(1).normal(size=(8, 16, 16)).astype("f4")
    y, origin = measurement_for(op, low, projections=None, slice_index=2)
    assert origin == SIMULATED
    assert y.shape == (1, 1, 36, 64)


def test_measurement_for_real_when_projections_present():
    op = RadonTransform(n_views=36, n_dets=64, img_size=16)
    low = np.zeros((8, 16, 16), dtype="f4")
    proj = np.random.default_rng(2).normal(size=(36, 40, 8)).astype("f4")
    y, origin = measurement_for(op, low, projections=proj, geometry=_axial_geometry(),
                                slice_index=2)
    assert origin == REAL_PAIRED
    assert y.shape == (1, 1, 36, 64)
    assert torch.isfinite(y).all()


def test_measurement_for_helical_falls_back_to_simulated():
    op = RadonTransform(n_views=36, n_dets=64, img_size=16)
    low = np.zeros((8, 16, 16), dtype="f4")
    proj = np.zeros((36, 40, 8), dtype="f4")
    geo = {**_axial_geometry(), "pitch": 1.0}
    _, origin = measurement_for(op, low, projections=proj, geometry=geo, slice_index=0)
    assert origin == SIMULATED   # helical -> fall back rather than mismatch the forward model
