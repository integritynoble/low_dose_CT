"""Tests for the corpus packaging writer (MANIFEST.sha256 + dataset_metadata.json).

Run from the deposit/ directory:

    PYTHONPATH=. pytest -q
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from package_corpus import (
    MANIFEST_NAME,
    METADATA_NAME,
    PackageError,
    fill_metadata,
    package,
    sha256_file,
    verify_manifest,
    write_manifest,
)

SEED = Path(__file__).resolve().parents[1] / "dataset_metadata.example.json"
SCHEMA = Path(__file__).resolve().parents[1] / "dataset_metadata.schema.json"


# --------------------------------------------------------------------------- #
# Build a small but structurally faithful fake corpus
# --------------------------------------------------------------------------- #
def _write(p: Path, data: bytes | str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    p.write_bytes(data)


def _fake_corpus(root: Path, *, with_patient_ids: bool = True) -> dict[str, int]:
    """Two vendors x one scan each x two doses; reference + one baseline; credentials."""
    scans = [("Siemens", "scanA", "p001"), ("GE", "scanB", "p002")]
    doses = ["r025", "r010"]
    n_recon = n_unc = n_err = n_task = n_meta = 0
    for vendor, scan, pid in scans:
        for dd in doses:
            d = root / "reconstructions" / vendor / scan / dd
            _write(d / "recon_mean.nii.gz", f"recon {vendor}{scan}{dd}".ljust(64, "x"))
            _write(d / "uncertainty_sigma.nii.gz", b"sigma" * 10)
            _write(d / "error_abs.nii.gz", b"err" * 11)
            _write(d / "task_nodule_score.nii.gz", b"score" * 7)
            meta = {"vendor": vendor, "r": float("0." + dd[1:]), "anatomy": "chest",
                    "split": "test", "source_scan_id": scan}
            if with_patient_ids:
                meta["patient_id"] = pid
            _write(d / "scan_meta.json", json.dumps(meta))
            n_recon += 1; n_unc += 1; n_err += 1; n_task += 1; n_meta += 1
    # one baseline reconstruction
    b = root / "baselines" / "red_cnn" / "Siemens" / "scanA" / "r025"
    _write(b / "recon.nii.gz", b"baserecon" * 5)
    _write(b / "error_abs.nii.gz", b"baseerr" * 5)
    _write(b / "task_nodule_score.nii.gz", b"basescore" * 3)
    # credentials (cohort-level) + index
    _write(root / "credentials" / "lung_nodule_5mm" / "r025" / "pwm_ref_v1__Siemens.json",
           json.dumps({"credential": {"verdict": "PASS"}}))
    _write(root / "credentials" / "lung_nodule_5mm" / "r010" / "pwm_ref_v1__GE.json",
           json.dumps({"credential": {"verdict": "INDETERMINATE"}}))
    _write(root / "credentials" / "all_credentials.jsonl", '{"path":"x"}\n')
    _write(root / "checksums_and_versions.json", json.dumps({"torch": "x"}))
    return {"recon": n_recon, "credentials": 2}


# --------------------------------------------------------------------------- #
# sha256 + manifest
# --------------------------------------------------------------------------- #
def test_sha256_file_matches_hashlib(tmp_path: Path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello world")
    assert sha256_file(p) == hashlib.sha256(b"hello world").hexdigest()


def test_manifest_covers_all_files_except_itself(tmp_path: Path):
    _fake_corpus(tmp_path)
    manifest = write_manifest(tmp_path)
    rels = {ln.split("  ", 1)[1] for ln in manifest.read_text().splitlines()}
    on_disk = {p.relative_to(tmp_path).as_posix()
               for p in tmp_path.rglob("*") if p.is_file()}
    assert MANIFEST_NAME not in rels
    assert rels == on_disk - {MANIFEST_NAME}


def test_manifest_is_sorted_and_sha256sum_format(tmp_path: Path):
    _fake_corpus(tmp_path)
    lines = write_manifest(tmp_path).read_text().splitlines()
    rels = [ln.split("  ", 1)[1] for ln in lines]
    assert rels == sorted(rels)
    for ln in lines:
        digest, rel = ln.split("  ", 1)
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def test_verify_manifest_clean(tmp_path: Path):
    _fake_corpus(tmp_path)
    write_manifest(tmp_path)
    rep = verify_manifest(tmp_path)
    assert rep["ok"] and rep["mismatched"] == [] and rep["missing"] == [] and rep["untracked"] == []


def test_verify_detects_mutation(tmp_path: Path):
    _fake_corpus(tmp_path)
    write_manifest(tmp_path)
    victim = tmp_path / "reconstructions" / "Siemens" / "scanA" / "r025" / "error_abs.nii.gz"
    victim.write_bytes(b"TAMPERED")
    rep = verify_manifest(tmp_path)
    assert rep["ok"] is False
    assert any("error_abs" in m for m in rep["mismatched"])


def test_verify_detects_untracked_and_missing(tmp_path: Path):
    _fake_corpus(tmp_path)
    write_manifest(tmp_path)
    # add an untracked file
    (tmp_path / "sneaky.txt").write_text("new")
    # remove a tracked file
    (tmp_path / "checksums_and_versions.json").unlink()
    rep = verify_manifest(tmp_path)
    assert rep["ok"] is False
    assert "sneaky.txt" in rep["untracked"]
    assert "checksums_and_versions.json" in rep["missing"]


def test_verify_raises_without_manifest(tmp_path: Path):
    _fake_corpus(tmp_path)
    with pytest.raises(PackageError):
        verify_manifest(tmp_path)


# --------------------------------------------------------------------------- #
# metadata fill
# --------------------------------------------------------------------------- #
def test_fill_metadata_counts_records(tmp_path: Path):
    _fake_corpus(tmp_path)
    seed = json.loads(SEED.read_text())
    md = fill_metadata(seed, tmp_path)
    by_type = {rt["type"]: rt for rt in md["record_types"]}
    assert by_type["reference_reconstruction"]["count"] == 4
    assert by_type["uncertainty_map"]["count"] == 4
    assert by_type["credential"]["count"] == 2
    assert by_type["baseline_reconstruction"]["count"] == 1
    assert by_type["index"]["count"] == 1
    # sizes are positive where files exist
    assert by_type["reference_reconstruction"]["total_bytes"] > 0


def test_fill_metadata_top_level_counts(tmp_path: Path):
    _fake_corpus(tmp_path, with_patient_ids=True)
    md = fill_metadata(json.loads(SEED.read_text()), tmp_path)
    c = md["counts"]
    assert c["n_scans"] == 2
    assert c["n_patients"] == 2
    # n_records_total excludes the jsonl index: 4+4+4+4(task)+2(cred)+1(baseline)+4(scan_meta)=23
    assert c["n_records_total"] == 23
    assert c["total_bytes"] > 0


def test_fill_metadata_patient_fallback_when_absent(tmp_path: Path):
    _fake_corpus(tmp_path, with_patient_ids=False)
    seed = json.loads(SEED.read_text())
    seed["counts"]["n_patients"] = 7  # seed value should be left untouched
    md = fill_metadata(seed, tmp_path)
    assert md["counts"]["n_patients"] == 7  # not overwritten when undable to derive


def test_fill_metadata_preserves_descriptive_fields(tmp_path: Path):
    _fake_corpus(tmp_path)
    seed = json.loads(SEED.read_text())
    md = fill_metadata(seed, tmp_path)
    assert md["title"] == seed["title"]
    assert md["creators"] == seed["creators"]
    assert md["credential"]["framework_hash"] == seed["credential"]["framework_hash"]


# --------------------------------------------------------------------------- #
# package() orchestration
# --------------------------------------------------------------------------- #
def test_package_writes_both_artifacts_and_manifest_covers_metadata(tmp_path: Path):
    _fake_corpus(tmp_path)
    report = package(tmp_path, SEED, schema_path=SCHEMA)
    assert (tmp_path / METADATA_NAME).exists()
    assert (tmp_path / MANIFEST_NAME).exists()
    # manifest written after metadata => metadata is covered
    manifest_rels = {ln.split("  ", 1)[1]
                     for ln in (tmp_path / MANIFEST_NAME).read_text().splitlines()}
    assert METADATA_NAME in manifest_rels
    # and the written corpus verifies clean
    assert verify_manifest(tmp_path)["ok"]
    assert report["record_type_counts"]["reference_reconstruction"] == 4


def test_package_metadata_is_schema_valid(tmp_path: Path):
    pytest.importorskip("jsonschema")
    _fake_corpus(tmp_path)
    report = package(tmp_path, SEED, schema_path=SCHEMA, require_schema_valid=True)
    assert report["schema_errors"] == []
