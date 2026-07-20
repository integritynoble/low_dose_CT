"""Minimal NIfTI-1 writer (float32) -- the corpus record format.

Self-contained so the installable package needs no sibling-script import just to write a
record. Byte-for-byte the same minimal header the WS-3 ``fixture/`` writer emits and the
``deposit/package_corpus`` verifier reads: float32, little-endian, sform = scaled identity
(orientation-normalised; DICOM position/origin intentionally not propagated -- manuscript D2).
"""
from __future__ import annotations

import gzip
import struct
from pathlib import Path
from typing import Tuple

import numpy as np


def write_nifti(path: Path | str, data: np.ndarray,
                voxel: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> None:
    """Write ``data`` as a minimal valid NIfTI-1 (.nii or .nii.gz), float32, sform=scaled identity."""
    path = Path(path)
    data = np.ascontiguousarray(np.asarray(data, dtype="<f4"))
    ndim = data.ndim
    dim = [0] * 8
    dim[0] = ndim
    for i in range(ndim):
        dim[i + 1] = data.shape[i]
    for i in range(ndim + 1, 8):
        dim[i] = 1
    pixdim = [1.0] + [float(voxel[i]) if i < len(voxel) else 1.0 for i in range(7)]

    hdr = bytearray(348)
    struct.pack_into("<i", hdr, 0, 348)
    struct.pack_into("<8h", hdr, 40, *dim)
    struct.pack_into("<h", hdr, 70, 16)            # datatype = FLOAT32
    struct.pack_into("<h", hdr, 72, 32)            # bitpix
    struct.pack_into("<8f", hdr, 76, *pixdim)
    struct.pack_into("<f", hdr, 108, 352.0)        # vox_offset
    struct.pack_into("<f", hdr, 112, 1.0)          # scl_slope
    struct.pack_into("<f", hdr, 116, 0.0)          # scl_inter
    struct.pack_into("<B", hdr, 123, 2)            # xyzt_units = MM
    struct.pack_into("<h", hdr, 252, 0)            # qform_code
    struct.pack_into("<h", hdr, 254, 1)            # sform_code = SCANNER
    struct.pack_into("<4f", hdr, 280, pixdim[1], 0.0, 0.0, 0.0)
    struct.pack_into("<4f", hdr, 296, 0.0, pixdim[2], 0.0, 0.0)
    struct.pack_into("<4f", hdr, 312, 0.0, 0.0, pixdim[3], 0.0)
    hdr[344:348] = b"n+1\x00"

    payload = bytes(hdr) + struct.pack("<4B", 0, 0, 0, 0) + data.tobytes(order="F")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
    else:
        path.write_bytes(payload)
