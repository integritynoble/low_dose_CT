"""LowDoseCTDataset — the loader contract (dataset_schema.md §4).

Reads the harmonized HDF5 tree produced by the preprocessing Dockerfiles and surfaces
per-slice samples under one schema across the three sources. Building HDF5 from raw DICOM
is the Dockerfiles' job and is out of the loader's scope (a ``build=`` path is reserved).
"""
from __future__ import annotations

import glob
import os
from typing import Dict, List, Optional, Sequence

import h5py
import numpy as np

from . import annotations as _ann
from ._seed import seed_everything
from .metadata import load_metadata
from .schema import (
    H5_FULL, H5_LD_REAL, H5_SINO_FULL, H5_SINO_LD_REAL, PIXEL_DTYPE, REAL_DOSE_RATIO, SOURCES,
    THIN_SLICE_MAX_MM, h5_ld_sim,
)


def _series_id_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _patient_from_path(path: str) -> str:
    return os.path.basename(os.path.dirname(path))


def _source_from_path(path: str) -> str:
    return os.path.basename(os.path.dirname(os.path.dirname(path)))


def _to_backend(arr: Optional[np.ndarray], backend: str):
    if arr is None:
        return None
    if backend == "torch":
        import torch
        return torch.from_numpy(np.ascontiguousarray(arr))
    return arr


def _resample_inplane(img: np.ndarray, src_spacing: Sequence[float], dst_mm: float) -> np.ndarray:
    """Separable bilinear resample of a 2-D slice from src (row, col) mm to an isotropic dst mm."""
    sr, sc = float(src_spacing[0]), float(src_spacing[1])
    h, w = img.shape
    new_h = max(1, int(round(h * sr / dst_mm)))
    new_w = max(1, int(round(w * sc / dst_mm)))
    ys = np.linspace(0, h - 1, new_h)
    xs = np.linspace(0, w - 1, new_w)
    y0 = np.floor(ys).astype(int)
    y1 = np.minimum(y0 + 1, h - 1)
    wy = (ys - y0)[:, None]
    tmp = img[y0] * (1 - wy) + img[y1] * wy
    x0 = np.floor(xs).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    wx = (xs - x0)[None, :]
    out = tmp[:, x0] * (1 - wx) + tmp[:, x1] * wx
    return out.astype(PIXEL_DTYPE)


class LowDoseCTDataset:
    """Per-slice dataset over the harmonized PWM-LDCT v0.5 tree.

    Pass either a single ``root`` (one harmonized tree) or per-source roots
    (``root_lidc`` / ``root_aapm`` / ``root_mayo``). See dataset_schema.md §4.1 for arguments.
    """

    def __init__(
        self,
        root: Optional[str] = None,
        *,
        root_lidc: Optional[str] = None,
        root_aapm: Optional[str] = None,
        root_mayo: Optional[str] = None,
        split: str = "train",
        seed: int = 42,
        dose_ratio: float = REAL_DOSE_RATIO,
        prefer_real_ld: bool = True,
        resample_spacing: Optional[float] = None,
        slice_thickness="thin",
        sources: Optional[Sequence[str]] = None,
        return_sinogram: bool = True,
        backend: Optional[str] = None,
    ):
        seed_everything(seed)
        self.split = split
        self.seed = seed
        self.dose_ratio = float(dose_ratio)
        self.prefer_real_ld = prefer_real_ld
        self.resample_spacing = resample_spacing
        self.slice_thickness = slice_thickness
        self.return_sinogram = return_sinogram
        self.sources = tuple(sources) if sources else SOURCES

        if backend is None:
            try:
                import torch  # noqa: F401
                backend = "torch"
            except ImportError:
                backend = "numpy"
        self.backend = backend

        # Resolve roots: a single harmonized tree, and/or per-source roots.
        self._roots: Dict[str, str] = {}
        if root is not None:
            for s in self.sources:
                self._roots[s] = root
        for s, r in {"lidc": root_lidc, "aapm": root_aapm, "mayo": root_mayo}.items():
            if r is not None and s in self.sources:
                self._roots[s] = r
        if not self._roots:
            raise ValueError("provide root=... or at least one of root_lidc/root_aapm/root_mayo")

        self._meta_cache: Dict = {}
        self._h5_cache: Dict[str, h5py.File] = {}
        self._index: List = []  # (series_path, root, z)
        self._series_path: Dict[str, str] = {}   # series_id -> hdf5 path
        self._series_root: Dict[str, str] = {}   # series_id -> root
        self._build_index()

    # -- index -------------------------------------------------------------------------
    def _series_files(self, root: str, source: str) -> List[str]:
        return sorted(glob.glob(os.path.join(root, "hdf5", self.split, source, "*", "*.h5")))

    def _metadata_for(self, root: str, series_id: str) -> dict:
        key = (root, series_id)
        if key not in self._meta_cache:
            p = os.path.join(root, "metadata", f"{series_id}.json")
            self._meta_cache[key] = load_metadata(p) if os.path.exists(p) else {}
        return self._meta_cache[key]

    def _build_index(self) -> None:
        for source, root in self._roots.items():
            for path in self._series_files(root, source):
                series_id = _series_id_from_path(path)
                meta = self._metadata_for(root, series_id)
                if self.slice_thickness == "thin":
                    st_mm = meta.get("acquisition", {}).get("slice_thickness_mm", 0.0)
                    if st_mm and st_mm > THIN_SLICE_MAX_MM:
                        continue
                self._series_path[series_id] = path
                self._series_root[series_id] = root
                with h5py.File(path, "r") as f:
                    n_slices = f[H5_FULL].shape[0]
                for z in range(n_slices):
                    self._index.append((path, root, z))

    # -- access ------------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._index)

    def _file(self, path: str) -> h5py.File:
        if path not in self._h5_cache:
            self._h5_cache[path] = h5py.File(path, "r")
        return self._h5_cache[path]

    def __getitem__(self, i: int) -> dict:
        path, root, z = self._index[i]
        f = self._file(path)
        series_id = f.attrs.get("series_id", _series_id_from_path(path))
        source = f.attrs.get("source", _source_from_path(path))
        patient_id = f.attrs.get("patient_id", _patient_from_path(path))
        meta = self._metadata_for(root, series_id)

        full = np.asarray(f[H5_FULL][z], dtype=PIXEL_DTYPE)

        low = None
        low_kind = None
        dr = self.dose_ratio
        if self.prefer_real_ld and H5_LD_REAL in f:
            low = np.asarray(f[H5_LD_REAL][z], dtype=PIXEL_DTYPE)
            low_kind, dr = "real", REAL_DOSE_RATIO
        else:
            sim_key = h5_ld_sim(self.dose_ratio)
            if sim_key in f:
                low = np.asarray(f[sim_key][z], dtype=PIXEL_DTYPE)
                low_kind = "sim"
            elif H5_LD_REAL in f:
                low = np.asarray(f[H5_LD_REAL][z], dtype=PIXEL_DTYPE)
                low_kind, dr = "real", REAL_DOSE_RATIO

        has_proj = H5_SINO_FULL in f  # projections are series-level (see get_series_projections)

        if self.resample_spacing is not None:
            ps = meta.get("acquisition", {}).get("pixel_spacing_mm", [1.0, 1.0])
            full = _resample_inplane(full, ps, self.resample_spacing)
            if low is not None:
                low = _resample_inplane(low, ps, self.resample_spacing)

        nodules = _ann.nodules_for_slice(_ann.load_series_nodules(root, patient_id), z)
        likert = _ann.load_series_likert(root, series_id)

        b = self.backend
        return {
            "full_dose": _to_backend(full, b),
            "low_dose": _to_backend(low, b),
            "low_dose_kind": low_kind,
            "dose_ratio": dr,
            "sinogram": None,            # projections are series-level; use get_series_projections()
            "has_projections": has_proj,
            "source": source,
            "patient_id": patient_id,
            "series_id": series_id,
            "slice_index": z,
            "annotations": {"nodules": nodules, "likert": likert},
            "metadata": meta,
        }

    def get_series_projections(self, series_id: str):
        """Native series-level projections + geometry for a series, or None if absent.

        Returns ``{"full_dose": ndarray [V, C, R], "low_dose_real": ndarray|None,
        "geometry": dict}`` (dataset_schema.md §4.2). Projections are not slice-aligned, so they
        are accessed by ``series_id`` rather than via the per-slice sample.
        """
        path = self._series_path.get(series_id)
        if path is None:
            return None
        f = self._file(path)
        if H5_SINO_FULL not in f:
            return None
        out = {"full_dose": np.asarray(f[H5_SINO_FULL], dtype=PIXEL_DTYPE)}
        out["low_dose_real"] = (np.asarray(f[H5_SINO_LD_REAL], dtype=PIXEL_DTYPE)
                                if H5_SINO_LD_REAL in f else None)
        root = self._series_root.get(series_id, "")
        out["geometry"] = self._metadata_for(root, series_id).get("geometry", {})
        return out

    def close(self) -> None:
        for f in self._h5_cache.values():
            try:
                f.close()
            except Exception:  # pragma: no cover
                pass
        self._h5_cache.clear()

    def __del__(self):  # pragma: no cover - best-effort cleanup
        self.close()
