import numpy as np
import pytest
import torch

from pwm_ldct_recon.measurement import (GeometryUnavailable, HelicalRebinningRequired,
                                        REAL_PAIRED, SIMULATED, extract_slice_fan_sinogram,
                                        helical_rebin_slice, measurement_for,
                                        rebin_fan_to_parallel)
from pwm_ldct_recon.physics import RadonTransform


def _axial_geometry():
    return {"source_to_isocenter_mm": 500.0, "views_per_rotation": 36,
            "fan_angle_total_rad": 0.8}


def _helical_geometry():
    return {"source_to_isocenter_mm": 500.0, "views_per_rotation": 36,
            "fan_angle_total_rad": 0.8, "pitch": 1.0, "n_det_rows": 8,
            "detector_row_spacing_mm": 1.0}


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


def test_helical_ssr_recovers_target_z_plane():
    # Build helical projections whose value at (v, c, r) is exactly the axial position z(v, r).
    # Single-slice rebinning at z0 must then return ~z0 everywhere (it interpolates in z).
    geo = _helical_geometry()
    V, C, R = 72, 40, geo["n_det_rows"]            # 2 rotations of 36 views
    feed_view = (geo["pitch"] * R * geo["detector_row_spacing_mm"]) / geo["views_per_rotation"]
    row_z = (np.arange(R) - (R - 1) / 2.0) * geo["detector_row_spacing_mm"]
    z_of = feed_view * np.arange(V)[:, None, None] + row_z[None, None, :]   # [V,1,R]
    proj = np.broadcast_to(z_of, (V, C, R)).astype("f4")
    n_slices, idx = 8, 4
    fan, betas, gammas, sid = helical_rebin_slice(proj, geo, slice_index=idx, n_slices=n_slices)
    all_z = feed_view * np.arange(V)[:, None] + row_z[None, :]
    z0 = all_z.min() + (idx + 0.5) / n_slices * (all_z.max() - all_z.min())
    assert fan.shape == (geo["views_per_rotation"], C)
    assert np.allclose(fan, z0, atol=1e-3), (fan.mean(), z0)


def test_measurement_for_helical_is_real_paired():
    op = RadonTransform(n_views=36, n_dets=64, img_size=16)
    low = np.zeros((8, 16, 16), dtype="f4")
    proj = np.random.default_rng(4).normal(size=(72, 40, 8)).astype("f4")
    y, origin = measurement_for(op, low, projections=proj, geometry=_helical_geometry(),
                                slice_index=3, n_slices=8)
    assert origin == REAL_PAIRED        # helical now reconstructed via SSR, not faked
    assert y.shape == (1, 1, 36, 64) and torch.isfinite(y).all()


def test_measurement_for_helical_insufficient_geometry_falls_back():
    op = RadonTransform(n_views=36, n_dets=64, img_size=16)
    low = np.zeros((8, 16, 16), dtype="f4")
    proj = np.zeros((72, 40, 8), dtype="f4")
    # pitch>0 (helical) but no table-feed info (no feed field, no n_det_rows/row spacing).
    geo = {"source_to_isocenter_mm": 500.0, "views_per_rotation": 36,
           "fan_angle_total_rad": 0.8, "pitch": 1.0}
    _, origin = measurement_for(op, low, projections=proj, geometry=geo, slice_index=0, n_slices=8)
    assert origin == SIMULATED
