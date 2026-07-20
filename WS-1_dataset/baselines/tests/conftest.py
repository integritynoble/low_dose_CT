"""Tiny synthetic PWM-LDCT v0.5 tree for harness tests (32x32 so RED-CNN's valid convs fit)."""
import hashlib
import json

import h5py
import numpy as np
import pytest

from pwm_ldct_loader.schema import H5_FULL, H5_LD_REAL, SCHEMA_VERSION, h5_ld_sim

Z, H, W = 2, 32, 32


def _meta(series_id, patient_id, source):
    return {
        "scan_uid": hashlib.sha256((series_id + SCHEMA_VERSION).encode()).hexdigest()[:16],
        "patient_id": patient_id, "series_id": series_id, "source": source,
        "anatomy": "chest", "schema_version": SCHEMA_VERSION,
        "acquisition": {"manufacturer": "GE", "model": "x", "kvp": 120,
                        "slice_thickness_mm": 1.0, "pixel_spacing_mm": [0.7, 0.7],
                        "recon_kernel": "STD", "image_orientation_patient": [1, 0, 0, 0, 1, 0],
                        "patient_position": "FFS"},
        "calibration": {"hu_offset": 0.0, "bowtie_profile": "measured"},
        "lowdose_sim": {"model": "fallback", "ratios": [0.10, 0.25, 0.50], "seed": 42},
        "demographics": {"age_years": None, "sex": None},
        "provenance": {"source_sop_class_uid": "1.2.840.10008.5.1.4.1.1.2", "n_slices": Z},
    }


@pytest.fixture(scope="session")
def dataset_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("pwm_ldct_v0_5")
    rng = np.random.default_rng(0)

    def write(split, source, pid, with_real):
        series = f"{pid}_chest_fd"
        d = root / "hdf5" / split / source / pid
        d.mkdir(parents=True, exist_ok=True)
        with h5py.File(d / f"{series}.h5", "w") as f:
            full = rng.random((Z, H, W), dtype=np.float32) * 1000 - 500  # HU-ish
            f[H5_FULL] = full
            for r in (0.10, 0.25, 0.50):
                f[h5_ld_sim(r)] = (full + rng.standard_normal((Z, H, W)).astype("float32") * 30)
            if with_real:
                f[H5_LD_REAL] = (full + rng.standard_normal((Z, H, W)).astype("float32") * 25)
            m = _meta(series, pid, source)
            for k in ("scan_uid", "series_id", "patient_id", "source", "anatomy", "schema_version"):
                f.attrs[k] = m[k]
        (root / "metadata").mkdir(exist_ok=True)
        (root / "metadata" / f"{series}.json").write_text(json.dumps(m))
        return pid

    train = [write("train", "lidc", "lidc-0001", False),
             write("train", "lidc", "lidc-0002", False)]
    test = [write("test", "mayo", "mayo-0001", True)]   # has real low-dose -> exercises 'real' branch
    sp = root / "splits"
    sp.mkdir(exist_ok=True)
    (sp / "train.txt").write_text("\n".join(train) + "\n")
    (sp / "val.txt").write_text("")
    (sp / "test.txt").write_text("\n".join(test) + "\n")
    return str(root)
