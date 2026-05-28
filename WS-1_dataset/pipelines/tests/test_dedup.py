"""Cross-source handling in write_splits.

A physical patient appearing in two sources (same canonical key) must be CO-LOCATED in one split
(no train/test leakage). splits.txt mirrors the loadable tree, so both records are listed; the
de-dup is a *counting* notion (distinct canonical keys), and write_splits is folder-authoritative
when HDF5 are present, falling back to assign_split when they were pruned.
"""
import json
import os

import h5py
import numpy as np

from pwm_ldct_loader.splits import assign_split
from pwm_ldct_prep.writers import folder_splits, write_splits


def _meta(out, pid, ckey, seed=42, anatomy="abdomen"):
    os.makedirs(os.path.join(out, "metadata"), exist_ok=True)
    series = f"{pid}_{anatomy}_fd"
    json.dump(
        {"patient_id": pid, "series_id": series, "lowdose_sim": {"seed": seed},
         "provenance": {"canonical_patient_key": ckey}},
        open(os.path.join(out, "metadata", f"{series}.json"), "w"),
    )
    return series


def _h5(out, split, source, pid, series):
    d = os.path.join(out, "hdf5", split, source, pid)
    os.makedirs(d, exist_ok=True)
    with h5py.File(os.path.join(d, f"{series}.h5"), "w") as f:
        f.create_dataset("recon/full_dose", data=np.zeros((1, 4, 4), dtype=np.float32))


def test_pruned_build_recomputes_and_colocates(tmp_path):
    """No HDF5 (streaming build pruned them): split = assign_split(canonical_key); shared-key
    patients land in the SAME split (no leakage); every record is listed."""
    out = str(tmp_path / "tree")
    _meta(out, "mayo-0001", "SHAREDKEYAAAA")
    _meta(out, "aapm-0001", "SHAREDKEYAAAA")
    _meta(out, "mayo-0002", "OTHERKEYBBBBB")
    write_splits(out)

    splits = {s: open(os.path.join(out, "splits", f"{s}.txt")).read().split()
              for s in ("train", "val", "test")}
    where = {p: s for s, ps in splits.items() for p in ps}
    # both shared-key records present and CO-LOCATED (no leakage)
    assert where["mayo-0001"] == where["aapm-0001"] == assign_split("SHAREDKEYAAAA")
    assert where["mayo-0002"] == assign_split("OTHERKEYBBBBB")
    # every record listed exactly once across splits (3 records, 2 unique patients)
    listed = [p for ps in splits.values() for p in ps]
    assert sorted(listed) == ["aapm-0001", "mayo-0001", "mayo-0002"]
    assert len(listed) == len(set(listed)) == 3


def test_folder_layout_is_authoritative(tmp_path):
    """When HDF5 exist, splits.txt mirrors the folder placement even if it differs from
    assign_split (e.g. a tree built before canonical keys) — matching what the loader globs."""
    out = str(tmp_path / "tree")
    s1 = _meta(out, "mayo-0144", "SHAREDKEYL143")
    s2 = _meta(out, "aapm-0004", "SHAREDKEYL143")
    _h5(out, "train", "mayo", "mayo-0144", s1)   # both co-located in train (as deposited)
    _h5(out, "train", "aapm", "aapm-0004", s2)

    assert folder_splits(out) == {"mayo-0144": "train", "aapm-0004": "train"}
    write_splits(out)
    splits = {s: open(os.path.join(out, "splits", f"{s}.txt")).read().split()
              for s in ("train", "val", "test")}
    # both listed, in TRAIN (folder-authoritative), regardless of assign_split's bucket
    assert sorted(splits["train"]) == ["aapm-0004", "mayo-0144"]
    assert splits["val"] == [] and splits["test"] == []
