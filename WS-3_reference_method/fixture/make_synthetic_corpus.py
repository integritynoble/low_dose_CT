"""Generate a miniature but structurally complete WS-3 corpus.

Exercises the full deposit pipeline end-to-end on synthetic data:

    image records (valid NIfTI) + scan_meta
      -> emit_stratum_credential  (credentials/, audited)
      -> rebuild_index            (all_credentials.jsonl)
      -> package_corpus.package   (dataset_metadata.json + MANIFEST.sha256)
      -> verify_manifest          (integrity check)

The product is a real, inspectable corpus a reviewer or CI run can walk: the
NIfTI records load with any reader, the credentials audit clean under
``pwm-audit``, and ``sha256sum -c MANIFEST.sha256`` passes. It is NOT scientific
data — the pixel values are random and the score arrays are synthetic; its only
job is to prove the machinery is correct without waiting on Phase-3 data.

Deterministic given ``seed``. Depends only on numpy + the WS-2 library (the
NIfTI writer below is self-contained — no nibabel needed to *write*; nibabel is
used only by the tests to confirm the files load).

CLI::

    python make_synthetic_corpus.py <out_dir> [--seed 42]
"""

from __future__ import annotations

import argparse
import gzip
import json
import struct
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Make the sibling tool modules importable whether run as a script or imported.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "corpus_emit"))
sys.path.insert(0, str(_HERE.parent / "deposit"))

from emit_credentials import (  # noqa: E402
    AucScores,
    PairedScores,
    StratumSpec,
    emit_stratum_credential,
    rebuild_index,
    verify_corpus_credentials,
)
import package_corpus as pkg  # noqa: E402

SEED_METADATA = _HERE.parent / "deposit" / "dataset_metadata.example.json"
SCHEMA = _HERE.parent / "deposit" / "dataset_metadata.schema.json"

# Small image grid keeps the fixture tiny but multi-slice.
_SHAPE = (8, 8, 2)

# Anatomy -> (task_name, metric, subpopulation, epsilon)
_TASKS = {
    "chest": ("lung_nodule_5mm", "auc", "adult_chest_pwm_l3_test_v1", 0.05),
    "abdomen": ("liver_lesion", "dice", "adult_abdomen_pwm_l3_test_v1", 0.03),
}


# --------------------------------------------------------------------------- #
# Self-contained NIfTI-1 writer (single .nii, float32, little-endian)
# --------------------------------------------------------------------------- #
def write_nifti(path: Path, data: np.ndarray, voxel: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> None:
    """Write a minimal valid NIfTI-1 (.nii) volume. float32, sform = scaled identity."""
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
    struct.pack_into("<i", hdr, 0, 348)            # sizeof_hdr
    struct.pack_into("<8h", hdr, 40, *dim)         # dim[8]
    struct.pack_into("<h", hdr, 70, 16)            # datatype = NIFTI_TYPE_FLOAT32
    struct.pack_into("<h", hdr, 72, 32)            # bitpix
    struct.pack_into("<8f", hdr, 76, *pixdim)      # pixdim[8]
    struct.pack_into("<f", hdr, 108, 352.0)        # vox_offset
    struct.pack_into("<f", hdr, 112, 1.0)          # scl_slope
    struct.pack_into("<f", hdr, 116, 0.0)          # scl_inter
    struct.pack_into("<B", hdr, 123, 2)            # xyzt_units = NIFTI_UNITS_MM
    struct.pack_into("<h", hdr, 252, 0)            # qform_code
    struct.pack_into("<h", hdr, 254, 1)            # sform_code = SCANNER
    struct.pack_into("<4f", hdr, 280, pixdim[1], 0.0, 0.0, 0.0)   # srow_x
    struct.pack_into("<4f", hdr, 296, 0.0, pixdim[2], 0.0, 0.0)   # srow_y
    struct.pack_into("<4f", hdr, 312, 0.0, 0.0, pixdim[3], 0.0)   # srow_z
    hdr[344:348] = b"n+1\x00"                        # magic

    payload = bytes(hdr) + struct.pack("<4B", 0, 0, 0, 0) + data.tobytes(order="F")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        # mtime=0 keeps the gzip bytes deterministic across runs at a fixed seed.
        path.write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
    else:
        path.write_bytes(payload)


# --------------------------------------------------------------------------- #
# Per-scan image records
# --------------------------------------------------------------------------- #
def _emit_scan_records(scan_dir: Path, rng: np.random.Generator) -> None:
    """Write the four NIfTI maps with a faintly realistic uncertainty<->error link."""
    ref = rng.normal(0.0, 1.0, _SHAPE).astype("f4")
    recon = ref + rng.normal(0.0, 0.3, _SHAPE).astype("f4")
    error = np.abs(recon - ref)
    # sigma tracks error (positive correlation) plus independent noise — so the
    # fixture's uncertainty<->error relationship is inspectable, not pure noise.
    sigma = 0.8 * error + np.abs(rng.normal(0.0, 0.05, _SHAPE)).astype("f4")
    task = rng.uniform(0.0, 1.0, _SHAPE).astype("f4")

    write_nifti(scan_dir / "recon_mean.nii.gz", recon)
    write_nifti(scan_dir / "uncertainty_sigma.nii.gz", sigma)
    write_nifti(scan_dir / "error_abs.nii.gz", error)
    write_nifti(scan_dir / "task_nodule_score.nii.gz", task)


def _auc_scores(rng: np.random.Generator, n: int) -> AucScores:
    return AucScores(
        a_pos=rng.normal(0.65, 0.18, n), a_neg=rng.normal(0.35, 0.18, n),
        b_pos=rng.normal(0.65, 0.18, n), b_neg=rng.normal(0.35, 0.18, n),
    )


def _dice_scores(rng: np.random.Generator, n: int) -> PairedScores:
    base = rng.uniform(0.80, 0.92, n)
    return PairedScores(paired_a=base + rng.normal(0, 0.01, n),
                        paired_b=base + rng.normal(0, 0.01, n))


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def build_synthetic_corpus(
    out_dir: Path | str,
    *,
    vendors: tuple[str, ...] = ("Siemens", "GE"),
    anatomies: tuple[str, ...] = ("chest", "abdomen"),
    doses: tuple[float, ...] = (0.25, 0.10),
    n_cohort: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    """Generate the corpus and run the full deposit pipeline; return a report.

    One scan per (vendor, anatomy); image records at every dose; cohort-level
    credentials per (task, dose, vendor) for the reference method plus one
    baseline (``red_cnn``) chest stratum per vendor at r025.
    """
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    patient = 0
    for vendor in vendors:
        for anatomy in anatomies:
            patient += 1
            scan_id = f"scan_{vendor.lower()}_{anatomy}"
            pid = f"p{patient:03d}"
            task_name, metric, subpop, eps = _TASKS[anatomy]
            for r in doses:
                dd = f"r{int(round(r * 100)):03d}"
                scan_dir = root / "reconstructions" / vendor / scan_id / dd
                _emit_scan_records(scan_dir, rng)
                (scan_dir / "scan_meta.json").write_text(json.dumps({
                    "vendor": vendor, "r": r, "anatomy": anatomy, "split": "test",
                    "source_scan_id": scan_id, "patient_id": pid,
                }, indent=2) + "\n", encoding="utf-8")

                spec = StratumSpec(
                    task_name=task_name, metric=metric, signal_ratio=r,
                    subpopulation=subpop, epsilon=eps,
                    method="pwm_ref_v1", reference_method="full_dose_fbp",
                    vendor=vendor, anatomy=anatomy,
                )
                scores = (_auc_scores(rng, n_cohort) if metric == "auc"
                          else _dice_scores(rng, n_cohort))
                emit_stratum_credential(root, spec, scores)

    # one baseline reconstruction stratum (chest, r025) per vendor, with records.
    # Baseline layout differs from the reference: recon.nii.gz (not recon_mean),
    # and no uncertainty map.
    for vendor in vendors:
        scan_id = f"scan_{vendor.lower()}_chest"
        bdir = root / "baselines" / "red_cnn" / vendor / scan_id / "r025"
        write_nifti(bdir / "recon.nii.gz", rng.normal(0.0, 1.0, _SHAPE).astype("f4"))
        write_nifti(bdir / "error_abs.nii.gz", np.abs(rng.normal(0.0, 0.3, _SHAPE)).astype("f4"))
        write_nifti(bdir / "task_nodule_score.nii.gz", rng.uniform(0.0, 1.0, _SHAPE).astype("f4"))
        emit_stratum_credential(
            root,
            StratumSpec(
                task_name="lung_nodule_5mm", metric="auc", signal_ratio=0.25,
                subpopulation="adult_chest_pwm_l3_test_v1", epsilon=0.05,
                method="red_cnn", reference_method="full_dose_fbp",
                vendor=vendor, anatomy="chest",
            ),
            _auc_scores(rng, n_cohort),
        )

    (root / "checksums_and_versions.json").write_text(
        json.dumps({"note": "synthetic fixture; not real library pins"}, indent=2) + "\n",
        encoding="utf-8",
    )

    rebuild_index(root)
    cred_report = verify_corpus_credentials(root)
    pkg_report = pkg.package(root, SEED_METADATA, schema_path=SCHEMA, require_schema_valid=True)
    manifest_report = pkg.verify_manifest(root)

    return {
        "root": str(root),
        "credentials_ok": cred_report["ok"],
        "n_credentials": cred_report["n_credentials"],
        "manifest_ok": manifest_report["ok"],
        "n_files": manifest_report["n_checked"],
        "counts": pkg_report["counts"],
        "record_type_counts": pkg_report["record_type_counts"],
        "schema_errors": pkg_report["schema_errors"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a synthetic WS-3 corpus end-to-end.")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    report = build_synthetic_corpus(args.out_dir, seed=args.seed)
    print(json.dumps(report, indent=2))
    ok = report["credentials_ok"] and report["manifest_ok"] and not report["schema_errors"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
