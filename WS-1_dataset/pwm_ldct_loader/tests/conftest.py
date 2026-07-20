"""Builds a tiny, schema-conformant PWM-LDCT v0.5 tree for tests.

Two series: a full-dose-only LIDC scan (sim low-dose, no sinogram) and an AAPM scan with
real low-dose + sinogram. Mirrors dataset_schema.md §2-§3.
"""
import hashlib
import json

import h5py
import numpy as np
import pytest

from pwm_ldct_loader.schema import H5_FULL, H5_LD_REAL, H5_SINO_FULL, SCHEMA_VERSION, h5_ld_sim

Z, H, W = 2, 8, 8
NV, NC, NR = 5, 12, 4   # projection views, detector channels, detector rows


def _meta(series_id, patient_id, source, anatomy="chest", geometry=None):
    m = {
        "scan_uid": hashlib.sha256((series_id + SCHEMA_VERSION).encode()).hexdigest()[:16],
        "patient_id": patient_id,
        "series_id": series_id,
        "source": source,
        "anatomy": anatomy,
        "schema_version": SCHEMA_VERSION,
        "acquisition": {
            "manufacturer": "SIEMENS",
            "model": "SOMATOM",
            "kvp": 120,
            "slice_thickness_mm": 1.0,
            "pixel_spacing_mm": [0.7, 0.7],
            "recon_kernel": "B30f",
            "image_orientation_patient": [1, 0, 0, 0, 1, 0],
            "patient_position": "HFS",
        },
        "calibration": {"hu_offset": 0.0, "bowtie_profile": "measured"},
        "lowdose_sim": {"model": "pwm_core.contrib.modalities.ct_radon",
                        "ratios": [0.10, 0.25, 0.50], "seed": 42},
        "demographics": {"age_years": None, "sex": None},
        "provenance": {"source_sop_class_uid": "1.2.840.10008.5.1.4.1.1.2", "n_slices": Z},
    }
    if geometry is not None:
        m["geometry"] = geometry
    return m


@pytest.fixture(scope="session")
def fixture_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("pwm_ldct_v0_5")
    rng = np.random.default_rng(0)

    def write_series(source, patient, series, with_real, with_sino):
        d = root / "hdf5" / "train" / source / patient
        d.mkdir(parents=True, exist_ok=True)
        geom = ({"vendor": "SIEMENS", "detector_shape": "CYLINDRICAL", "scan_type": "HELICAL",
                 "beam_geometry": "FANBEAM", "n_views": NV, "n_det_channels": NC, "n_det_rows": NR,
                 "calibration_status": "test fixture"} if with_sino else None)
        m = _meta(series, patient, source, geometry=geom)
        with h5py.File(d / f"{series}.h5", "w") as f:
            f[H5_FULL] = rng.standard_normal((Z, H, W)).astype("float32")
            for r in (0.10, 0.25, 0.50):
                f[h5_ld_sim(r)] = rng.standard_normal((Z, H, W)).astype("float32")
            if with_real:
                f[H5_LD_REAL] = rng.standard_normal((Z, H, W)).astype("float32")
            if with_sino:
                f[H5_SINO_FULL] = rng.standard_normal((NV, NC, NR)).astype("float32")
            f.attrs["scan_uid"] = m["scan_uid"]
            f.attrs["series_id"] = series
            f.attrs["patient_id"] = patient
            f.attrs["source"] = source
            f.attrs["anatomy"] = "chest"
            f.attrs["schema_version"] = SCHEMA_VERSION
        (root / "metadata").mkdir(exist_ok=True)
        (root / "metadata" / f"{series}.json").write_text(json.dumps(m))

    write_series("lidc", "lidc-0001", "lidc-0001_chest_fd", with_real=False, with_sino=False)
    write_series("aapm", "aapm-001", "aapm-001_chest_fd", with_real=True, with_sino=True)

    sp = root / "splits"
    sp.mkdir(exist_ok=True)
    (sp / "train.txt").write_text("lidc-0001\naapm-001\n")
    (sp / "val.txt").write_text("")
    (sp / "test.txt").write_text("")

    nd = root / "annotations" / "lidc_majority_vote"
    nd.mkdir(parents=True, exist_ok=True)
    (nd / "lidc-0001.json").write_text(json.dumps({
        "patient_id": "lidc-0001", "series_id": "lidc-0001_chest_fd", "source": "lidc",
        "nodules": [{
            "nodule_id": "n1", "slice_index": 0, "bbox_xyxy": [1, 1, 3, 3],
            "diameter_mm": 4.0, "texture": 3, "location": "RUL",
            "ground_truth": "majority_vote", "n_contributing_readers": 3,
            "calibration_window": ["cw-r1-001"],
        }],
    }))
    lk = root / "annotations" / "likert"
    lk.mkdir(parents=True, exist_ok=True)
    (lk / "aapm-001_chest_fd.json").write_text(json.dumps({
        "series_id": "aapm-001_chest_fd",
        "scores": [{"reconstruction": "fbp", "dose_ratio": 0.25,
                    "scores_per_reader": [4, 3], "consensus": 4}],
        "n_readers": 2,
    }))

    manifest_rels = [
        "metadata/lidc-0001_chest_fd.json",
        "metadata/aapm-001_chest_fd.json",
        "splits/train.txt",
        "annotations/lidc_majority_vote/lidc-0001.json",
        "annotations/likert/aapm-001_chest_fd.json",
    ]
    lines = []
    for rel in manifest_rels:
        digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    (root / "manifest.sha256").write_text("\n".join(lines) + "\n")

    return str(root)
