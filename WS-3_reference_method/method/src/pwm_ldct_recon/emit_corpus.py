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
from typing import Callable, Dict, Iterable, List, Optional, Protocol

import numpy as np
import torch

from .config import EnsembleConfig
from .data import denormalize, normalize
from .detector import FrozenDetector
from .ensemble import ensemble_infer
from .models import UnrolledRecon
from .niftiio import write_nifti
from .physics import RadonTransform

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


def _to_recon_hu(recon_norm: torch.Tensor) -> np.ndarray:
    """[Z,1,H,W] normalised tensor -> [Z,H,W] HU array, clamped to the HU window (V4 precision)."""
    arr = denormalize(recon_norm.squeeze(1).cpu().numpy())
    return np.clip(arr, -1024.0, 3072.0).astype("f4")


# --------------------------------------------------------------------------- #
# Baseline reconstructors (single-model; no uncertainty -- manuscript D4)
# --------------------------------------------------------------------------- #
class BaselineReconstructor(Protocol):
    """A single-model comparison baseline (manuscript sec:baselines): low -> recon, no UQ."""

    name: str

    def reconstruct(self, low_hu: np.ndarray, device: str = "cpu") -> np.ndarray:
        """[Z,H,W] HU low-dose -> [Z,H,W] HU reconstruction."""
        ...


class FBPBaseline:
    """Filtered-backprojection baseline (manuscript sec:baselines, method 'fbp')."""

    name = "fbp"

    def __init__(self, physics: RadonTransform):
        self.physics = physics

    @torch.no_grad()
    def reconstruct(self, low_hu: np.ndarray, device: str = "cpu") -> np.ndarray:
        low = torch.from_numpy(normalize(low_hu)).unsqueeze(1).to(device)
        return _to_recon_hu(self.physics.fbp(self.physics.forward(low)))


class ModelBaseline:
    """A single trained model as a baseline (e.g. RED-CNN). ``mode`` selects the domain:

    ``image``       the model maps the normalised low-dose *image* -> recon (RED-CNN-style);
    ``measurement`` the model maps the measurement ``y = R(low)`` -> recon (unrolled-style).
    """

    def __init__(self, name: str, model: torch.nn.Module, mode: str = "image",
                 physics: Optional[RadonTransform] = None):
        self.name = name
        self.model = model
        self.mode = mode
        self.physics = physics

    @torch.no_grad()
    def reconstruct(self, low_hu: np.ndarray, device: str = "cpu") -> np.ndarray:
        self.model.eval()
        low = torch.from_numpy(normalize(low_hu)).unsqueeze(1).to(device)
        if self.mode == "measurement":
            phys = self.physics or getattr(self.model, "physics", None)
            if phys is None:
                raise ValueError("measurement-mode baseline needs a physics operator.")
            return _to_recon_hu(self.model(phys.forward(low)))
        return _to_recon_hu(self.model(low))


# baseline_scores_fn(method, vendor, anatomy, signal_ratio) -> AucScores.
BaselineScoresFn = Callable[[str, str, str, float], object]


def _emit_baseline_records(root: Path, scan: "ScanInput", ref_hu: np.ndarray,
                           baseline: BaselineReconstructor, detector: FrozenDetector,
                           device: str) -> None:
    """Write one baseline's records for a scan: recon + error + task map (no scan_meta, no sigma)."""
    for r, low_hu in sorted(scan.low_dose.items()):
        dd = f"r{int(round(r * 100)):03d}"
        bdir = root / "baselines" / baseline.name / scan.vendor / scan.scan_id / dd
        recon = baseline.reconstruct(np.asarray(low_hu, dtype="f4"), device)
        write_nifti(bdir / "recon.nii.gz", recon)               # 'recon', not 'recon_mean'
        write_nifti(bdir / "error_abs.nii.gz", np.abs(recon - ref_hu).astype("f4"))
        write_nifti(bdir / "task_nodule_score.nii.gz",
                    np.asarray(detector.score_map(recon), dtype="f4"))


def run(out_dir: Path | str, scans: Iterable[ScanInput], models: List[UnrolledRecon],
        detector: FrozenDetector, scores_fn: ScoresFn, *,
        cfg: EnsembleConfig = EnsembleConfig(), task: TaskSpec = TaskSpec(),
        seed_metadata: Optional[Path] = None, schema: Optional[Path] = None,
        method: str = "pwm_ref_v1", reference_method: str = "full_dose_fbp",
        baselines: Optional[List[BaselineReconstructor]] = None,
        baseline_scores_fn: Optional[BaselineScoresFn] = None,
        device: str = "cpu", corpus_emit_dir: Optional[Path] = None,
        deposit_dir: Optional[Path] = None) -> dict:
    """Generate the corpus from ensemble inference and run the full deposit pipeline.

    Optionally also emits single-model ``baselines`` (manuscript sec:baselines) under
    ``baselines/<method>/...``; if any are given, ``baseline_scores_fn`` is required so each
    baseline gets matched credentials.
    """
    emit, pkg, dp = _load_deposit_tools(corpus_emit_dir, deposit_dir)
    baselines = baselines or []
    if baselines and baseline_scores_fn is None:
        raise ValueError("baseline_scores_fn is required when baselines are provided.")
    scans = list(scans)  # materialised: reused by the reference, baseline, and credential passes
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

        # baseline records for this scan (single-model; no sigma, no scan_meta -- matches fixture).
        for baseline in baselines:
            _emit_baseline_records(root, scan, ref_hu, baseline, detector, device)

    # credentials: one per (task, dose, vendor) for the reference method and each baseline.
    doses = sorted(cfg.base.doses)
    vendors = _vendors_from(root)
    for vendor in vendors:
        for r in doses:
            spec = emit.StratumSpec(
                task_name=task.task_name, metric=task.metric, signal_ratio=r,
                subpopulation=task.subpopulation, epsilon=task.epsilon,
                method=method, reference_method=reference_method,
                vendor=vendor, anatomy="chest",
            )
            emit.emit_stratum_credential(root, spec, scores_fn(vendor, "chest", r))
            for baseline in baselines:
                bspec = emit.StratumSpec(
                    task_name=task.task_name, metric=task.metric, signal_ratio=r,
                    subpopulation=task.subpopulation, epsilon=task.epsilon,
                    method=baseline.name, reference_method=reference_method,
                    vendor=vendor, anatomy="chest",
                )
                assert baseline_scores_fn is not None  # guaranteed above
                emit.emit_stratum_credential(
                    root, bspec, baseline_scores_fn(baseline.name, vendor, "chest", r))

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
        "n_baseline_methods": len(baselines),
        "counts": pkg_report["counts"],
        "schema_errors": pkg_report["schema_errors"],
    }


def _vendors_from(root: Path) -> List[str]:
    rec = root / "reconstructions"
    return sorted(d.name for d in rec.iterdir() if d.is_dir()) if rec.is_dir() else []
