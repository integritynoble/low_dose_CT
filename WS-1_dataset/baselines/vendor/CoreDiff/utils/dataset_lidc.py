"""LIDC v0.5 dataset bridge for CoreDiff (official code integration).

The official CoreDiff CTDataset only ships MAYO 2016/2020, piglet and phantom
npy layouts. This module exposes our LIDC-only simulated low-dose v0.5 tree
(D:\\ZHY\\LIDC3DDataSet\\output_all) in the exact CTDataset contract:

  * context=True  -> input (3, 512, 512): (prev, cur, next) neighbouring slices
                     of the same low-dose volume; target (1, 512, 512) full-dose.
  * context=False -> input (1, 512, 512).
  * Normalisation matches the harness convention: HU clipped to [-1024, 3072]
    then scaled to [0, 1] ((x + 1024) / 4096).

File tree consumed:
  {root}/hdf5/{split}/lidc/{pid}/{pid}_chest_fd.h5
    recon/full_dose        (S, 512, 512) float32 HU
    recon/low_dose_sim/r025 (S, 512, 512) float32 HU   (dose_ratio selected by dose)

dose values used by CoreDiff CLI are percentages (--dose 25 -> r025).
"""
from __future__ import annotations

import os
import glob
import json

import numpy as np
import h5py
from torch.utils.data import Dataset


class LIDCV05Dataset(Dataset):
    def __init__(self, root: str = r"D:\ZHY\LIDC3DDataSet\output_gpu",
                 mode: str = "train", dose: int = 25, context: bool = True,
                 seed: int = 42, test_id=None, thin_only: bool = False,
                 include_edges: bool = False):
        # test_id accepted for CLI compatibility with the official CTDataset; unused here.
        self.root = root
        self.mode = mode
        self.context = context
        self.dose_key = f"r{dose:03d}"  # 10->r010, 25->r025, 50->r050
        self.thin_only = thin_only
        self.include_edges = include_edges
        THIN_SLICE_MAX_MM = 1.5  # matches harness pwm_ldct_loader selection

        split_file = os.path.join(root, "splits", f"{mode}.txt")
        if not os.path.exists(split_file):
            raise FileNotFoundError(split_file)
        with open(split_file) as f:
            patient_ids = [ln.strip() for ln in f if ln.strip()]

        # patient-level index: (patient_id, h5_path, n_slices)
        self.patients = []
        for pid in patient_ids:
            h5 = os.path.join(root, "hdf5", mode, "lidc", pid, f"{pid}_chest_fd.h5")
            if not os.path.exists(h5):
                continue
            if thin_only:
                meta_path = os.path.join(root, "metadata", f"{pid}_chest_fd.json")
                if os.path.exists(meta_path):
                    with open(meta_path) as mf:
                        meta = json.load(mf)
                    st_mm = meta.get("acquisition", {}).get("slice_thickness_mm", 0.0)
                    if st_mm and st_mm > THIN_SLICE_MAX_MM:
                        continue
            with h5py.File(h5, "r") as fh:
                n = fh["recon/full_dose"].shape[0]
            self.patients.append((pid, h5, n))

        # slice-level index: (patient_pos, slice_idx) usable with context
        self.index = []
        for ppos, (pid, h5, n) in enumerate(self.patients):
            if self.context and not self.include_edges:
                lo, hi = (1, n - 1)
            else:
                lo, hi = (0, n)
            for s in range(lo, hi):
                self.index.append((ppos, s))

    def __len__(self):
        return len(self.index)

    def __getitem__(self, idx):
        ppos, s = self.index[idx]
        pid, h5_path, n = self.patients[ppos]
        with h5py.File(h5_path, "r") as fh:
            if self.context:
                i0, i1, i2 = max(s - 1, 0), s, min(s + 1, n - 1)
                g = fh[f"recon/low_dose_sim/{self.dose_key}"]
                ld = np.concatenate([g[i0][None], g[i1][None], g[i2][None]], axis=0)  # (3,512,512)
            else:
                ld = fh[f"recon/low_dose_sim/{self.dose_key}"][s][None]      # (1,512,512)
            fd = fh["recon/full_dose"][s][None]                              # (1,512,512)
        ld = self._normalize(ld.astype(np.float32))
        fd = self._normalize(fd.astype(np.float32))
        return ld, fd

    @staticmethod
    def _normalize(img, MIN_B=-1024, MAX_B=3072):
        np.clip(img, MIN_B, MAX_B, out=img)
        return (img - MIN_B) / (MAX_B - MIN_B)
