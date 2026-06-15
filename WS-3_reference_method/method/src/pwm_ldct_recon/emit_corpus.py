"""Phase-3 corpus run: ensemble inference over scans x dose levels -> the deposit corpus.

This is the entry point the WS-3 README calls the "Phase-3 corpus run". For each scan it
writes the same record layout the synthetic ``fixture/`` stands in for -- but from real
deep-ensemble reconstructions -- then drives the existing ``corpus_emit`` (credentials) and
``deposit`` (metadata + manifest + construction-check) tools:

    reconstructions/<vendor>/<scan>/r100/recon_mean.nii.gz   # full-dose reference (x_ref)
    reconstructions/<vendor>/<scan>/r{010,025,050}/
        recon_mean.nii.gz  uncertainty_sigma.nii.gz  error_abs.nii.gz  task_nodule_score.nii.gz
    credentials/<task>/<dose>/<method>__<vendor>.json
    dataset_metadata.json   MANIFEST.sha256

All maps are written in HU. ``error_abs = |recon_mean - x_ref|`` against the scan's own r100
reference, so ``package_corpus.verify_error_maps`` passes by construction (manuscript V4).
"""
from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

import numpy as np
import torch

from .config import EnsembleConfig
from .data import denormalize, normalize
from .detector import FrozenDetector
from .ensemble import ensemble_infer
from .models import UnrolledRecon
from .niftiio import write_nifti

_WS3_ROOT = Path(__file__).resolve().parents[3]


def _load_deposit_tools(corpus_emit_dir: Optional[Path] = None, deposit_dir: Optional[Path] = None):
    """Import the sibling corpus_emit / deposit script modules (repo-tree run)."""
    ce = corpus_emit_dir or (_WS3_ROOT / "corpus_emit")
    dp = deposit_dir or (_WS3_ROOT / "deposit")
    for d in (ce, dp):
        if not (d / "__init__.py").exists() and str(d) not in sys.path:
            sys.path.insert(0, str(d))
    if not (ce / "emit_credentials.py").exists():
        raise FileNotFoundError(f"corpus_emit not found at {ce}; pass corpus_emit_dir.")
    emit = importlib.import_module("emit_credentials")
    pkg = importlib.import_module("package_corpus")
    return emit, pkg, dp


@dataclass
class ScanInput:
    """One scan: full-dose reference + per-dose low-dose volumes, all ``[Z,H,W]`` in HU."""

    scan_id: str
    vendor: str
    patient_id: str
    full_dose: np.ndarray
    low_dose: Dict[float, np.ndarray]
    anatomy: str = "chest"          # v1 is lung-nodule-only (manuscript M3)
    split: str = "test"
    low_dose_origin: Dict[float, str] = field(default_factory=dict)


@dataclass
class TaskSpec:
    """The single v1 credentialed task (manuscript M3; sec:detector)."""

    task_name: str = "lung_nodule_5mm"
    metric: str = "auc"
    subpopulation: str = "adult_chest_pwm_l3_test_v1"
    epsilon: float = 0.05


# scores_fn(vendor, anatomy, signal_ratio) -> AucScores for the credential at that stratum.
ScoresFn = Callable[[str, str, float], object]


@torch.no_grad()
def reconstruct_volume(models: List[UnrolledRecon], low_hu: np.ndarray, device: str = "cpu"):
    """Ensemble-reconstruct a ``[Z,H,W]`` HU volume; return (recon_mean_hu, sigma_hu) in HU."""
    low = torch.from_numpy(normalize(low_hu)).unsqueeze(1).to(device)  # [Z,1,H,W]
    y = models[0].physics.forward(low)
    res = ensemble_infer(models, y)
    mean = denormalize(res.mean.squeeze(1).cpu().numpy())
    # Clamp to the HU window: reconstructions are HU images, and bounding the range keeps
    # |recon - ref| within float32 precision so the construction-check (V4) holds at 1e-3 HU.
    mean = np.clip(mean, -1024.0, 3072.0)
    sigma = res.sigma.squeeze(1).cpu().numpy() * (3072.0 - (-1024.0))   # std -> HU units
    return mean.astype("f4"), sigma.astype("f4")


def run(out_dir: Path | str, scans: Iterable[ScanInput], models: List[UnrolledRecon],
        detector: FrozenDetector, scores_fn: ScoresFn, *,
        cfg: EnsembleConfig = EnsembleConfig(), task: TaskSpec = TaskSpec(),
        seed_metadata: Optional[Path] = None, schema: Optional[Path] = None,
        method: str = "pwm_ref_v1", reference_method: str = "full_dose_fbp",
        device: str = "cpu", corpus_emit_dir: Optional[Path] = None,
        deposit_dir: Optional[Path] = None) -> dict:
    """Generate the corpus from ensemble inference and run the full deposit pipeline."""
    emit, pkg, dp = _load_deposit_tools(corpus_emit_dir, deposit_dir)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    seed_metadata = seed_metadata or (dp / "dataset_metadata.example.json")
    schema = schema or (dp / "dataset_metadata.schema.json")

    for scan in scans:
        ref_hu = np.asarray(scan.full_dose, dtype="f4")
        rdir = root / "reconstructions" / scan.vendor / scan.scan_id
        # r=1.00 full-dose reference (recon_mean == x_ref; no error/task; manuscript M4).
        write_nifti(rdir / "r100" / "recon_mean.nii.gz", ref_hu)
        (rdir / "r100" / "scan_meta.json").write_text(json.dumps({
            "vendor": scan.vendor, "r": 1.0, "anatomy": scan.anatomy, "split": scan.split,
            "source_scan_id": scan.scan_id, "patient_id": scan.patient_id,
            "role": "full_dose_reference",
        }, indent=2) + "\n", encoding="utf-8")

        for r, low_hu in sorted(scan.low_dose.items()):
            dd = f"r{int(round(r * 100)):03d}"
            sdir = rdir / dd
            recon, sigma = reconstruct_volume(models, np.asarray(low_hu, dtype="f4"), device)
            error = np.abs(recon - ref_hu).astype("f4")
            task_map = np.asarray(detector.score_map(recon), dtype="f4")
            write_nifti(sdir / "recon_mean.nii.gz", recon)
            write_nifti(sdir / "uncertainty_sigma.nii.gz", sigma)
            write_nifti(sdir / "error_abs.nii.gz", error)
            write_nifti(sdir / "task_nodule_score.nii.gz", task_map)
            (sdir / "scan_meta.json").write_text(json.dumps({
                "vendor": scan.vendor, "r": r, "anatomy": scan.anatomy, "split": scan.split,
                "source_scan_id": scan.scan_id, "patient_id": scan.patient_id,
                "low_dose_origin": scan.low_dose_origin.get(r, "simulated"),
                "detector": {"name": detector.name, "version": detector.version},
            }, indent=2) + "\n", encoding="utf-8")

    # credentials: one per (task, dose, vendor) for the reference method. Vendors are read
    # back from the tree just written, so `scans` may be a one-shot iterator.
    doses = sorted(cfg.base.doses)
    for vendor in _vendors_from(root):
        for r in doses:
            spec = emit.StratumSpec(
                task_name=task.task_name, metric=task.metric, signal_ratio=r,
                subpopulation=task.subpopulation, epsilon=task.epsilon,
                method=method, reference_method=reference_method,
                vendor=vendor, anatomy="chest",
            )
            emit.emit_stratum_credential(root, spec, scores_fn(vendor, "chest", r))

    emit.rebuild_index(root)
    cred_report = emit.verify_corpus_credentials(root)
    pkg_report = pkg.package(root, seed_metadata, schema_path=schema, require_schema_valid=True)
    manifest_report = pkg.verify_manifest(root)
    errmap_report = pkg.verify_error_maps(root)
    return {
        "root": str(root),
        "credentials_ok": cred_report["ok"],
        "n_credentials": cred_report["n_credentials"],
        "manifest_ok": manifest_report["ok"],
        "error_maps_ok": errmap_report["ok"],
        "n_error_maps_checked": errmap_report["n_checked"],
        "counts": pkg_report["counts"],
        "schema_errors": pkg_report["schema_errors"],
    }


def _vendors_from(root: Path) -> List[str]:
    rec = root / "reconstructions"
    return sorted(d.name for d in rec.iterdir() if d.is_dir()) if rec.is_dir() else []
