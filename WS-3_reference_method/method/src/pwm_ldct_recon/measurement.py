"""Measurement model: form the unrolled net's data term from *measured* projections.

The unrolled reconstruction's data term needs a measurement ``y`` and a forward operator whose
adjoint is consistent with it. Two sources, with explicit provenance (the ``low_dose_origin``
field in ``scan_meta.json``; manuscript M5):

- ``simulated``  -- ``y = op.forward(low_dose_image)``. The bootstrap path: no measured
  projections are required, but the measurement is our own forward projection of the
  already-reconstructed low-dose image, not an independent acquisition.
- ``real_paired`` -- the measured low-dose projections from WS-1
  (``LowDoseCTDataset.get_series_projections``). These are native DICOM-CT-PD **fan-beam**
  sinograms ``[V, C, R]``; we map them onto the parallel-beam operator's geometry by standard
  **fan-to-parallel rebinning** (Kak & Slaney), so the existing parallel-beam ``RadonTransform``
  stays the matching forward model and the data term's adjoint remains exact.

Scope. Two real geometries are supported: **axial** (single-rotation) fan-beam, where detector
row ``R`` selects the slice (:func:`extract_slice_fan_sinogram`), and **helical** (Mayo LDCT-PD,
``scan_type == "HELICAL"`` / pitch > 0), handled by 360-degree-LI single-slice rebinning
(:func:`helical_rebin_slice`) into an axial fan sinogram before the shared fan->parallel step.
Only geometry that is genuinely insufficient falls back to ``simulated``, so provenance is
recorded honestly rather than reconstructing from a mismatched forward model.

Geometry fields. Confirmed against the WS-1 prep pipeline
(``pwm_ldct_prep.adapters.base.extract_ct_pd_geometry``; ``pipelines/tests/test_projections``):
the consumed keys are ``scan_type``, ``pitch`` (DICOM ``SpiralPitchFactor``), ``n_det_rows``,
``n_det_channels``, ``views_per_rotation``, ``detector_channel_positions``, ``detector_shape``,
``source_to_isocenter_mm``, ``source_to_detector_mm``, ``data_collection_diameter_mm``. WS-1 flags
the exact source/detector-distance and channel-angle semantics as needing the DICOM-CT-PD data
dictionary (``geometry.calibration_status``), so the SID and fan-angle handling here is
best-effort; the SSR step itself needs only ``pitch`` x ``n_det_rows`` (a unit-free z ratio) plus
``views_per_rotation``. The latter (DICOM-CT-PD private tag ``(7033,1013)``) was **verified
present in real Mayo LDCT-PD projection data** across both vendors (GE: 984; Siemens: 1152/2304
views/rotation) and decoded to an int by the WS-1 pipeline, so the helical path fires on real
data; the ``simulated`` fallback remains only for series genuinely missing the tag (e.g. an image,
not a projection, series).
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import torch

from .data import normalize

REAL_PAIRED = "real_paired"
SIMULATED = "simulated"


class HelicalRebinningRequired(NotImplementedError):
    """Raised when projections are helical and need rebinning before per-slice fan extraction."""


class GeometryUnavailable(ValueError):
    """Raised when the geometry dict lacks the fields needed to rebin fan -> parallel."""


# --------------------------------------------------------------------------- #
# Fan-to-parallel rebinning (equiangular detector; Kak & Slaney eq. 4.40-4.41)
# --------------------------------------------------------------------------- #
def rebin_fan_to_parallel(fan_sino: np.ndarray, *, fan_angles: np.ndarray,
                          view_angles: np.ndarray, sid: float, n_dets: int) -> np.ndarray:
    """Rebin an equiangular fan sinogram ``[V, C]`` to a parallel sinogram ``[n_views, n_dets]``.

    A fan ray ``(beta, gamma)`` maps to a parallel ray ``(theta, s)`` via
    ``theta = beta + gamma`` and ``s = sid * sin(gamma)``. We invert this on a regular parallel
    grid (``theta`` over ``[0, pi)``, ``s`` over ``[-s_max, s_max]``) and bilinearly sample the
    fan data on its ``(view_angles, fan_angles)`` grid.

    Args:
        fan_sino:    ``[V, C]`` line integrals (one detector row / axial slice).
        fan_angles:  ``[C]`` per-channel fan angle ``gamma`` in radians (monotonic).
        view_angles: ``[V]`` per-view source angle ``beta`` in radians (monotonic).
        sid:         source-to-isocenter distance (same length unit as ``s``; only its scale matters).
        n_dets:      number of parallel detector bins.
    """
    fan_sino = np.asarray(fan_sino, dtype=np.float64)
    if fan_sino.ndim != 2:
        raise ValueError(f"fan_sino must be [V, C]; got {fan_sino.shape}")
    fan_angles = np.asarray(fan_angles, dtype=np.float64)
    view_angles = np.asarray(view_angles, dtype=np.float64)
    if fan_sino.shape != (view_angles.size, fan_angles.size):
        raise ValueError("fan_sino shape must match (view_angles, fan_angles).")

    n_views = view_angles.size
    s_max = float(sid * np.sin(np.abs(fan_angles).max()))
    theta = np.linspace(0.0, np.pi, n_views, endpoint=False)
    s = np.linspace(-s_max, s_max, n_dets)
    gamma_q = np.arcsin(np.clip(s / sid, -1.0, 1.0))           # [n_dets]
    out = np.empty((n_views, n_dets), dtype=np.float64)
    for i, th in enumerate(theta):
        beta_q = th - gamma_q                                   # [n_dets]
        out[i] = _bilinear_on_grid(fan_sino, view_angles, fan_angles, beta_q, gamma_q)
    return out.astype(np.float32)


def _bilinear_on_grid(F: np.ndarray, vx: np.ndarray, vy: np.ndarray,
                      qx: np.ndarray, qy: np.ndarray) -> np.ndarray:
    """Bilinearly sample ``F`` (defined on monotonic grids ``vx``, ``vy``) at points ``(qx, qy)``.

    ``beta`` (``vx``) is treated as periodic (mod 2*pi) so a query just past the last view wraps
    to the first. Out-of-range fan angles clamp to the detector edge.
    """
    two_pi = 2.0 * np.pi
    vx0 = vx[0]
    span = vx[-1] - vx[0] + (vx[1] - vx[0] if vx.size > 1 else two_pi)  # full periodic span
    qx_w = vx0 + np.mod(qx - vx0, span if span > 0 else two_pi)
    ix = np.clip(np.searchsorted(vx, qx_w) - 1, 0, vx.size - 2)
    iy = np.clip(np.searchsorted(vy, qy) - 1, 0, vy.size - 2)
    x0, x1 = vx[ix], vx[ix + 1]
    y0, y1 = vy[iy], vy[iy + 1]
    tx = np.where(x1 > x0, (qx_w - x0) / (x1 - x0 + 1e-12), 0.0).clip(0, 1)
    ty = np.where(y1 > y0, (qy - y0) / (y1 - y0 + 1e-12), 0.0).clip(0, 1)
    f00 = F[ix, iy]; f01 = F[ix, iy + 1]; f10 = F[ix + 1, iy]; f11 = F[ix + 1, iy + 1]
    return (f00 * (1 - tx) * (1 - ty) + f10 * tx * (1 - ty)
            + f01 * (1 - tx) * ty + f11 * tx * ty)


# --------------------------------------------------------------------------- #
# Geometry parsing + per-slice fan extraction
# --------------------------------------------------------------------------- #
def _is_helical(geometry: dict) -> bool:
    if str(geometry.get("scan_type", "")).strip().upper().startswith("HELICAL"):
        return True
    pitch = geometry.get("pitch")
    return pitch is not None and float(pitch) > 0.0


def _fan_angles_from_geometry(geometry: dict, n_channels: int) -> np.ndarray:
    """Per-channel fan angle (radians) from the WS-1 geometry dict.

    Uses the fields the WS-1 prep pipeline actually emits (confirmed against
    ``pwm_ldct_prep.adapters.base.extract_ct_pd_geometry`` / ``pipelines/tests/test_projections``):
    ``detector_channel_positions`` (preferred), else ``data_collection_diameter_mm`` +
    ``source_to_isocenter_mm``. Channel-position *semantics* are flagged uncertain by WS-1's own
    ``geometry.calibration_status`` (DICOM-CT-PD data dictionary needed), so this is best-effort:
    radian-valued positions are used directly; mm positions are converted with the detector shape
    (``CYLINDRICAL`` -> arc-length/SDD, else flat-panel ``arctan``).
    """
    pos = geometry.get("detector_channel_positions")
    if pos is not None:
        pos = np.asarray(pos, dtype=np.float64)
        if pos.size == n_channels and np.isfinite(pos).all():
            if np.max(np.abs(pos)) < np.pi:                 # already radians
                return pos
            sdd = geometry.get("source_to_detector_mm")
            if sdd:                                          # mm positions on the detector
                if str(geometry.get("detector_shape", "")).upper().startswith("CYL"):
                    return pos / float(sdd)                 # curved (equiangular) arc length
                return np.arctan(pos / float(sdd))          # flat panel
    dcd = geometry.get("data_collection_diameter_mm")
    sid = geometry.get("source_to_isocenter_mm")
    if dcd and sid:
        half = float(np.arcsin(np.clip((float(dcd) / 2.0) / float(sid), -1.0, 1.0)))
        return np.linspace(-half, half, n_channels)
    raise GeometryUnavailable(
        "cannot derive per-channel fan angles: need detector_channel_positions, or "
        "data_collection_diameter_mm + source_to_isocenter_mm.")


def _feed_per_rotation_rows(geometry: dict) -> float:
    """Table feed per rotation in **detector-row-collimation units** (``pitch * n_det_rows``).

    WS-1's geometry provides ``pitch`` (DICOM ``SpiralPitchFactor`` = feed / total collimation)
    and ``n_det_rows`` but not an absolute row spacing. SSR only needs the feed *relative* to the
    row collimation (the rebinning interpolates values vs. ``z`` and is invariant to the absolute
    ``z`` scale), so we work in units where one detector row = 1: feed/rotation = pitch x n_det_rows.
    """
    pitch = geometry.get("pitch")
    rows = geometry.get("n_det_rows")
    if pitch and rows:
        return float(pitch) * int(rows)
    raise GeometryUnavailable(
        "helical rebinning needs pitch (SpiralPitchFactor) + n_det_rows.")


def helical_rebin_slice(projections: np.ndarray, geometry: dict, slice_index: int, n_slices: int
                        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Single-slice rebinning of helical ``[V, C, R]`` into one axial fan sinogram ``[Vpr, C]``.

    In a helical acquisition the source advances in ``z`` as it rotates, so each
    (view ``v``, detector row ``r``) samples azimuth ``beta_v = 2*pi*(v mod Vpr)/Vpr`` at axial
    position ``z(v, r) = feed_per_view*v + row_z(r)``. To synthesize the axial sinogram at a
    target plane ``z0``, for each azimuth bin we gather every (rotation, row) sample at that
    azimuth and **linearly interpolate** in ``z`` to ``z0`` (the classic 360-degree-LI SSR,
    generalised to multi-row by including each row's ``z`` offset). The result is an axial fan
    sinogram handed to :func:`rebin_fan_to_parallel` exactly like the axial case.

    ``z0`` is placed by ``slice_index`` over the helically-covered ``z`` extent; ``np.interp``'s
    edge-clamping bounds slices near the ends (where helical coverage is one-sided).
    """
    proj = np.asarray(projections, dtype=np.float64)
    if proj.ndim != 3:
        raise ValueError(f"projections must be [V, C, R]; got {proj.shape}")
    v_n, c_n, r_n = proj.shape
    vpr = geometry.get("views_per_rotation")
    if not vpr:
        raise GeometryUnavailable("helical rebinning needs views_per_rotation.")
    vpr = int(vpr)
    sid = geometry.get("source_to_isocenter_mm")
    if not sid:
        raise GeometryUnavailable("geometry lacks source_to_isocenter_mm (SID).")
    feed_view = _feed_per_rotation_rows(geometry) / vpr          # row-collimation units
    row_z = np.arange(r_n) - (r_n - 1) / 2.0                     # one row = 1 unit
    s_v = feed_view * np.arange(v_n)                              # source z per view

    all_z = s_v[:, None] + row_z[None, :]                        # [V, R]
    z_min, z_max = float(all_z.min()), float(all_z.max())
    z0 = z_min + (slice_index + 0.5) / max(1, n_slices) * (z_max - z_min)

    a_v = np.arange(v_n) % vpr
    fan = np.empty((vpr, c_n), dtype=np.float64)
    for a in range(vpr):
        vs = np.nonzero(a_v == a)[0]                              # views at this azimuth
        zs = (s_v[vs][:, None] + row_z[None, :]).reshape(-1)      # [len(vs)*R]
        vals = proj[vs].transpose(0, 2, 1).reshape(-1, c_n)      # [len(vs)*R, C]
        order = np.argsort(zs)
        zs_s, vals_s = zs[order], vals[order]
        j = int(np.clip(np.searchsorted(zs_s, z0), 1, len(zs_s) - 1))
        z_lo, z_hi = zs_s[j - 1], zs_s[j]
        t = 0.0 if z_hi <= z_lo else float(np.clip((z0 - z_lo) / (z_hi - z_lo), 0.0, 1.0))
        fan[a] = vals_s[j - 1] * (1.0 - t) + vals_s[j] * t
    view_angles = np.linspace(0.0, 2.0 * np.pi, vpr, endpoint=False)
    fan_angles = _fan_angles_from_geometry(geometry, c_n)
    return fan, view_angles, fan_angles, float(sid)


def extract_slice_fan_sinogram(projections: np.ndarray, geometry: dict, slice_index: int
                               ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Extract one axial slice's fan sinogram from ``[V, C, R]``.

    Returns ``(fan_sino [V, C], view_angles [V], fan_angles [C], sid)``. Raises
    :class:`HelicalRebinningRequired` for helical acquisitions and :class:`GeometryUnavailable`
    when the geometry is insufficient.
    """
    proj = np.asarray(projections)
    if proj.ndim != 3:
        raise ValueError(f"projections must be [V, C, R]; got {proj.shape}")
    if _is_helical(geometry):
        raise HelicalRebinningRequired(
            "helical acquisition (pitch > 0): apply single-slice rebinning before fan extraction "
            "(Phase-3 step). Falling back to simulated measurement.")
    v, c, r = proj.shape
    row = int(np.clip(slice_index, 0, r - 1))
    fan_sino = proj[:, :, row]                                  # [V, C]
    sid = geometry.get("source_to_isocenter_mm")
    if not sid:
        raise GeometryUnavailable("geometry lacks source_to_isocenter_mm (SID).")
    vpr = geometry.get("views_per_rotation", v)
    n_rot = max(1, v // max(1, int(vpr)))
    view_angles = np.linspace(0.0, 2.0 * np.pi * n_rot, v, endpoint=False)
    fan_angles = _fan_angles_from_geometry(geometry, c)
    return fan_sino.astype(np.float64), view_angles, fan_angles, float(sid)


# --------------------------------------------------------------------------- #
# Measurement selection
# --------------------------------------------------------------------------- #
def simulate(op, low_image: np.ndarray, device: str = "cpu") -> torch.Tensor:
    """``y = op.forward(low_image)`` for a ``[Z,H,W]`` (or ``[H,W]``) HU image -> ``[Z,1,V,D]``."""
    arr = np.asarray(low_image, dtype="f4")
    if arr.ndim == 2:
        arr = arr[None]
    low = torch.from_numpy(normalize(arr)).unsqueeze(1).to(device)
    return op.forward(low)


def measurement_for(op, low_image: np.ndarray, *, projections: Optional[np.ndarray] = None,
                    geometry: Optional[dict] = None, slice_index: int = 0,
                    n_slices: Optional[int] = None,
                    device: str = "cpu") -> Tuple[torch.Tensor, str]:
    """Return ``(y, origin)`` for one slice: measured projections if usable, else simulated.

    ``y`` is shaped ``[1,1,n_views,n_dets]`` to match ``op``. ``origin`` is ``real_paired`` or
    ``simulated`` (records to ``low_dose_origin``). Helical scans are single-slice rebinned
    (needs ``n_slices`` to place the target plane); only geometry that is genuinely insufficient
    falls back to ``simulated`` rather than reconstruct from a mismatched forward model.
    """
    if projections is not None and geometry:
        try:
            if _is_helical(geometry):
                fan, betas, gammas, sid = helical_rebin_slice(
                    projections, geometry, slice_index, n_slices or 1)
            else:
                fan, betas, gammas, sid = extract_slice_fan_sinogram(
                    projections, geometry, slice_index)
            par = rebin_fan_to_parallel(fan, fan_angles=gammas, view_angles=betas, sid=sid,
                                        n_dets=op.n_dets)
            y = torch.from_numpy(par).to(device)[None, None]      # [1,1,V,D]
            if y.shape[2] != op.n_views:
                y = torch.nn.functional.interpolate(
                    y, size=(op.n_views, op.n_dets), mode="bilinear", align_corners=False)
            return y, REAL_PAIRED
        except (HelicalRebinningRequired, GeometryUnavailable):
            pass  # geometry insufficient -> fall back to simulated below
    arr = np.asarray(low_image, dtype="f4")
    if arr.ndim == 2:
        arr = arr[None]
    return simulate(op, arr[slice_index] if arr.shape[0] > slice_index else arr[0], device), SIMULATED
