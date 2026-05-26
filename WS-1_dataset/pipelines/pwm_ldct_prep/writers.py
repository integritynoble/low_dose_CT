"""Writers for the harmonized tree: HDF5 (§3), metadata (§5), audit, splits (§7), manifest."""
from __future__ import annotations

import glob
import hashlib
import json
import os
from typing import Dict, List, Optional

import h5py
import numpy as np

from pwm_ldct_loader.schema import (H5_FULL, H5_LD_REAL, H5_SINO_FULL, H5_SINO_LD_REAL,
                                    PIXEL_DTYPE, SCHEMA_VERSION, h5_ld_sim)

from .harmonize import apply_hu_offset


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(path: str, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def write_metadata(out_root: str, meta: Dict) -> str:
    d = os.path.join(out_root, "metadata")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{meta['series_id']}.json")
    blob = json.dumps(meta, indent=2, sort_keys=True).encode()
    with open(path, "wb") as f:
        f.write(blob)
    return _sha256_bytes(blob)


def write_series_hdf5(out_root: str, fd, sims: Dict[float, np.ndarray], split: str,
                      meta_sha256: str, real_ld=None) -> str:
    d = os.path.join(out_root, "hdf5", split, fd.source, fd.patient_id)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{fd.series_id}.h5")

    def _ds(f, name, arr):
        f.create_dataset(name, data=np.ascontiguousarray(arr.astype(PIXEL_DTYPE)),
                         compression="gzip", compression_opts=4)

    with h5py.File(path, "w") as f:
        _ds(f, H5_FULL, apply_hu_offset(fd.volume_hu, fd.source))
        for r, vol in sims.items():
            _ds(f, h5_ld_sim(r), vol)
        if real_ld is not None:
            _ds(f, H5_LD_REAL, apply_hu_offset(real_ld.volume_hu, real_ld.source))
        if fd.sinogram is not None:
            _ds(f, H5_SINO_FULL, fd.sinogram)
        ld_sino = getattr(real_ld, "sinogram", None) if real_ld is not None else None
        if ld_sino is None:
            ld_sino = getattr(fd, "ld_sinogram", None)   # GE: LD projection without an LD recon
        if ld_sino is not None:
            _ds(f, H5_SINO_LD_REAL, ld_sino)
        f.attrs["scan_uid"] = _scan_uid(fd.series_id)
        f.attrs["patient_id"] = fd.patient_id
        f.attrs["series_id"] = fd.series_id
        f.attrs["source"] = fd.source
        f.attrs["anatomy"] = fd.anatomy
        f.attrs["schema_version"] = SCHEMA_VERSION
        f.attrs["metadata_sha256"] = meta_sha256
    return path


def write_annotations(out_root: str, patient_id: str, series_id: str, source: str,
                      annotations: Optional[Dict]) -> None:
    """Write majority-vote + raw-per-reader annotation files (annotation_qa_protocol.md §7)."""
    if not annotations:
        return
    base = os.path.join(out_root, "annotations")
    mv_dirname = "lidc_majority_vote" if source == "lidc" else f"topup_{source}"
    mv_dir = os.path.join(base, mv_dirname)
    os.makedirs(mv_dir, exist_ok=True)
    nodules = annotations.get("majority", [])
    for n in nodules:
        n.setdefault("ground_truth", "majority_vote")
    with open(os.path.join(mv_dir, f"{patient_id}.json"), "w") as f:
        json.dump({"patient_id": patient_id, "series_id": series_id, "source": source,
                   "nodules": nodules}, f, indent=2)
    raw_dir = os.path.join(base, "raw_per_reader", patient_id)
    os.makedirs(raw_dir, exist_ok=True)
    for rid, items in annotations.get("per_reader", {}).items():
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(rid))
        with open(os.path.join(raw_dir, f"{safe}.json"), "w") as f:
            json.dump({"patient_id": patient_id, "series_id": series_id, "reader_id": rid,
                       "nodules": items}, f, indent=2)


def append_audit(out_root: str, row: Dict) -> None:
    with open(os.path.join(out_root, "deident_audit.jsonl"), "a") as f:
        f.write(json.dumps(row) + "\n")


def write_splits(out_root: str) -> Dict[str, List[str]]:
    """Derive splits/*.txt from metadata + the deterministic split rule (dataset_schema.md §7).

    Uses each series' patient_id + recorded seed, so it works even when the (regenerable, local-only)
    HDF5 shards have been uploaded and pruned during a chunked/streaming build.
    """
    from pwm_ldct_loader.splits import assign_split
    placement: Dict[str, str] = {}
    for mp in glob.glob(os.path.join(out_root, "metadata", "*.json")):
        with open(mp) as f:
            meta = json.load(f)
        pid = meta.get("patient_id")
        if pid:
            placement[pid] = assign_split(pid, int(meta.get("lowdose_sim", {}).get("seed", 42)))
    out: Dict[str, List[str]] = {"train": [], "val": [], "test": []}
    for pid, split in placement.items():
        out.setdefault(split, []).append(pid)
    sd = os.path.join(out_root, "splits")
    os.makedirs(sd, exist_ok=True)
    for name in ("train", "val", "test"):
        with open(os.path.join(sd, f"{name}.txt"), "w") as f:
            f.write("\n".join(sorted(out.get(name, []))) + ("\n" if out.get(name) else ""))
    return out


def write_manifest(out_root: str) -> str:
    """Hash the deposited records (metadata, splits, annotations) into manifest.sha256."""
    rels: List[str] = []
    for pat in ("metadata/*.json", "splits/*.txt", "annotations/**/*.json"):
        for p in glob.glob(os.path.join(out_root, pat), recursive=True):
            rels.append(os.path.relpath(p, out_root))
    rels = sorted(set(rels))
    lines = [f"{_sha256_file(os.path.join(out_root, rel))}  {rel}" for rel in rels]
    path = os.path.join(out_root, "manifest.sha256")
    with open(path, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    return path


def _scan_uid(series_id: str) -> str:
    return hashlib.sha256((series_id + SCHEMA_VERSION).encode()).hexdigest()[:16]
