"""Tests for the synthetic end-to-end corpus fixture generator.

Run from the fixture/ directory:

    PYTHONPATH=. pytest -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from make_synthetic_corpus import build_synthetic_corpus, write_nifti


# --------------------------------------------------------------------------- #
# NIfTI writer
# --------------------------------------------------------------------------- #
def test_write_nifti_roundtrips_with_nibabel(tmp_path: Path):
    nib = pytest.importorskip("nibabel")
    data = np.arange(8 * 8 * 2, dtype="f4").reshape(8, 8, 2)
    p = tmp_path / "vol.nii.gz"
    write_nifti(p, data)
    img = nib.load(str(p))
    assert img.shape == (8, 8, 2)
    np.testing.assert_allclose(np.asarray(img.dataobj, dtype="f4"), data, rtol=0, atol=0)


def test_write_nifti_header_is_valid(tmp_path: Path):
    nib = pytest.importorskip("nibabel")
    p = tmp_path / "v.nii.gz"
    write_nifti(p, np.zeros((4, 4, 1), dtype="f4"))
    hdr = nib.load(str(p)).header
    assert int(hdr["sizeof_hdr"]) == 348
    assert hdr.get_data_dtype() == np.dtype("<f4")


# --------------------------------------------------------------------------- #
# End-to-end build
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def built(tmp_path_factory):
    root = tmp_path_factory.mktemp("corpus")
    report = build_synthetic_corpus(root, seed=7)
    return root, report


def test_build_reports_all_green(built):
    _, report = built
    assert report["credentials_ok"] is True
    assert report["manifest_ok"] is True
    assert report["schema_errors"] == []


def test_build_has_expected_structure(built):
    root, _ = built
    # 2 vendors x 2 anatomies x 2 doses = 8 scan-record folders
    scan_dirs = [d for d in (root / "reconstructions").glob("*/*/r*") if d.is_dir()]
    assert len(scan_dirs) == 8
    # every scan folder has the 4 maps + scan_meta
    for d in scan_dirs:
        for f in ["recon_mean.nii.gz", "uncertainty_sigma.nii.gz",
                  "error_abs.nii.gz", "task_nodule_score.nii.gz", "scan_meta.json"]:
            assert (d / f).exists(), f"{d}/{f} missing"


def test_build_credentials_cover_both_estimators(built):
    root, _ = built
    creds = list((root / "credentials").rglob("*.json"))
    metrics = set()
    for c in creds:
        payload = json.loads(c.read_text())
        metrics.add(payload["credential"]["task"]["metric"])
    assert {"auc", "dice"} <= metrics  # AUC (DeLong) and Dice (percentile) both exercised


def test_build_reference_and_baseline_coexist(built):
    root, _ = built
    chest_r025 = root / "credentials" / "lung_nodule_5mm" / "r025"
    names = {p.name for p in chest_r025.glob("*.json")}
    assert any(n.startswith("pwm_ref_v1__") for n in names)
    assert any(n.startswith("red_cnn__") for n in names)


def test_index_line_count_matches_credentials(built):
    root, report = built
    index = (root / "credentials" / "all_credentials.jsonl").read_text().splitlines()
    n_cred_files = len(list((root / "credentials").rglob("*.json")))
    assert len(index) == n_cred_files == report["n_credentials"]


def test_manifest_passes_system_sha256sum(built):
    root, _ = built
    assert (root / "MANIFEST.sha256").exists()
    proc = subprocess.run(
        ["sha256sum", "-c", "MANIFEST.sha256"],
        cwd=root, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert ": FAILED" not in proc.stdout


def test_metadata_counts_filled(built):
    root, _ = built
    md = json.loads((root / "dataset_metadata.json").read_text())
    assert md["counts"]["n_scans"] == 4    # 2 vendors x 2 anatomies = 4 distinct scans
    assert md["counts"]["n_patients"] == 4   # one patient per (vendor, anatomy)
    assert md["counts"]["n_records_total"] > 0
    by_type = {rt["type"]: rt["count"] for rt in md["record_types"]}
    assert by_type["reference_reconstruction"] == 8   # 4 scans x 2 doses
    assert by_type["baseline_reconstruction"] == 2
    assert by_type["credential"] == _cred_count(root)


def _cred_count(root: Path) -> int:
    return len(list((root / "credentials").rglob("*.json")))


def test_deterministic_given_seed(tmp_path: Path):
    a = build_synthetic_corpus(tmp_path / "a", seed=123)
    b = build_synthetic_corpus(tmp_path / "b", seed=123)
    # identical recon bytes under the same seed
    ra = (tmp_path / "a" / "reconstructions" / "Siemens" / "scan_siemens_chest" / "r025" / "recon_mean.nii.gz").read_bytes()
    rb = (tmp_path / "b" / "reconstructions" / "Siemens" / "scan_siemens_chest" / "r025" / "recon_mean.nii.gz").read_bytes()
    assert ra == rb
    assert a["record_type_counts"] == b["record_type_counts"]


def test_cli_runs_and_exits_zero(tmp_path: Path):
    out = tmp_path / "cli_corpus"
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "make_synthetic_corpus.py"),
         str(out), "--seed", "5"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["manifest_ok"] and report["credentials_ok"]
