"""Deep-ensemble UQ report: low-confidence <-> missed-lesion association (P2-7).

low-dose-ct.md §7.6 / §5 self-modelling dimension: the reference method already
produces deep-ensemble uncertainty (mean + per-pixel std, see ensemble.py).  This
module turns that signal into an *association report* -- not just a number, but the
mechanism that links low model confidence to missed lesions.

Current status
--------------
* The analysis functions are complete and unit-tested on synthetic ensemble maps.
* The wiring point for real inference is ``analyze_ensemble_bundle``: it consumes the
  same bundle layout produced by ``ensemble.ensemble_infer`` and writes a machine
  readable report (JSON) + human-readable summary (Markdown).
* Running on the real dataset is gated by the same held-out / reproduction gates as
  the rest of the RunBundle -- no numbers are claimed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np


@dataclass
class ConfidenceLesionStats:
    """Association statistics between model confidence and lesion detection."""

    n_lesions: int = 0
    n_low_confidence: int = 0
    n_missed: int = 0
    n_missed_and_low_confidence: int = 0
    # precision of low confidence as a missed-lesion predictor
    low_conf_precision: float = float("nan")
    # recall: fraction of missed lesions that were flagged low-confidence
    low_conf_recall: float = float("nan")
    # sensitivity of confidence flag on ALL lesions (not just missed)
    flag_rate: float = float("nan")
    iou_std_lesion: float = float("nan")  # mean std overlap with lesion mask
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_lesions": self.n_lesions,
            "n_low_confidence": self.n_low_confidence,
            "n_missed": self.n_missed,
            "n_missed_and_low_confidence": self.n_missed_and_low_confidence,
            "low_conf_precision": self.low_conf_precision,
            "low_conf_recall": self.low_conf_recall,
            "flag_rate": self.flag_rate,
            "iou_std_lesion": self.iou_std_lesion,
            "notes": self.notes,
        }


def _safe_ratio(num: float, den: float) -> float:
    if den <= 0:
        return float("nan")
    return float(num) / float(den)


def analyze_confidence_lesion(
    confidence_map: np.ndarray,
    lesion_mask: np.ndarray,
    confidence_threshold: float,
    low_confidence_is_high_std: bool = True,
) -> ConfidenceLesionStats:
    """Measure low-confidence <-> missed-lesion association on one slice.

    Parameters
    ----------
    confidence_map : (H, W) float
        Model confidence map.  For deep-ensemble we use the per-pixel std (higher =
        less certain) so ``low_confidence_is_high_std=True`` is the default; pass
        False if the map is a "confidence" where higher is better.
    lesion_mask : (H, W) bool
        Ground-truth lesion pixels (any positive values are treated as lesion).
    confidence_threshold : float
        Threshold above which a pixel is "low confidence".
    low_confidence_is_high_std : bool
        Whether the map is a std (True) or a confidence (False).

    Returns
    -------
    ConfidenceLesionStats with the association statistics.  A lesion is *missed*
    when its mask pixel is not inside the high-confidence (low-std) region; the
    stats report how much of the miss rate is covered by the low-confidence flag.
    """
    conf = np.asarray(confidence_map, dtype=float)
    mask = np.asarray(lesion_mask, dtype=bool)
    if conf.shape != mask.shape:
        raise ValueError(f"shape mismatch: conf {conf.shape} vs mask {mask.shape}")

    if low_confidence_is_high_std:
        low_conf = conf > confidence_threshold
    else:
        low_conf = conf < confidence_threshold

    n_lesion_px = int(mask.sum())
    missed_px = int((mask & ~low_conf).sum())
    low_conf_px = int(low_conf.sum())
    missed_and_low_conf = int((mask & low_conf).sum())
    # fraction of lesion pixels that are flagged low confidence
    lesion_low_conf = _safe_ratio(int((mask & low_conf).sum()), n_lesion_px)
    std_at_lesion = conf[mask].mean() if n_lesion_px else float("nan")

    return ConfidenceLesionStats(
        n_lesions=n_lesion_px,
        n_low_confidence=low_conf_px,
        n_missed=missed_px,
        n_missed_and_low_confidence=missed_and_low_conf,
        low_conf_precision=_safe_ratio(missed_and_low_conf, low_conf_px),
        low_conf_recall=_safe_ratio(missed_and_low_conf, missed_px),
        flag_rate=lesion_low_conf,
        iou_std_lesion=std_at_lesion,
        notes=[
            "per-pixel association on this slice; aggregate over slices for the "
            "full report",
            f"confidence_threshold={confidence_threshold}, "
            f"low_confidence_is_high_std={low_confidence_is_high_std}",
        ],
    )


def analyze_ensemble_bundle(
    recon_mean: np.ndarray,
    recon_std: np.ndarray,
    lesion_mask: np.ndarray | None = None,
    confidence_threshold: float | None = None,
) -> dict[str, Any]:
    """End-to-end entry point for one ensemble inference bundle.

    Returns a JSON-ready dict (not a dataclass) so the RunBundle can write it
    directly into results.json.  When ``lesion_mask`` is None the report only
    contains the low-confidence fraction (no lesion association) -- useful for
    warning-level reporting on unlabelled data.
    """
    mean = np.asarray(recon_mean, dtype=float)
    std = np.asarray(recon_std, dtype=float)
    if mean.shape != std.shape:
        raise ValueError(f"shape mismatch: mean {mean.shape} vs std {std.shape}")

    default_threshold = float(np.percentile(std, 90)) if std.size else 0.0
    thr = confidence_threshold if confidence_threshold is not None else default_threshold

    report: dict[str, Any] = {
        "module": "pwm_ldct_recon.uq_report",
        "analysis": "low_confidence_vs_missed_lesion",
        "confidence_metric": "deep_ensemble_per_pixel_std",
        "confidence_threshold": thr,
        "n_pixels": int(mean.size),
        "std_range": [float(std.min()), float(std.max())] if std.size else [],
        "low_confidence_fraction": float(_safe_ratio(int((std > thr).sum()), int(std.size))),
    }
    if lesion_mask is not None:
        stats = analyze_confidence_lesion(std, lesion_mask, thr)
        report["lesion_association"] = stats.to_dict()
    else:
        report["lesion_association"] = None
        report["notes"] = [
            "no lesion mask provided; association block left null. "
            "Provide the held-out lesion mask to enable the low-confidence <-> "
            "missed-lesion report."]
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """Render the association report as a human-readable Markdown section."""
    lines = [
        "## Low-confidence <-> missed-lesion association (deep-ensemble UQ)",
        "",
        f"- Confidence metric: `{report.get('confidence_metric')}`",
        f"- Threshold: {report.get('confidence_threshold')}",
        f"- Pixels: {report.get('n_pixels')}, low-confidence fraction: "
        f"{report.get('low_confidence_fraction'):.3f}",
    ]
    assoc = report.get("lesion_association")
    if assoc is None:
        lines.append("- Lesion association: not computed (no mask supplied)")
    else:
        lines.append(
            f"- Lesions: {assoc.get('n_lesions')} px, missed: {assoc.get('n_missed')} px "
            f"({100 * _safe_ratio(assoc.get('n_missed'), assoc.get('n_lesions')):.1f}%)")
        lines.append(
            f"- Low-confidence precision (missed / low-conf): "
            f"{assoc.get('low_conf_precision'):.3f}")
        lines.append(
            f"- Low-confidence recall (flagged-missed / missed): "
            f"{assoc.get('low_conf_recall'):.3f}")
        lines.append(
            f"- Mean ensemble std at lesion: {assoc.get('iou_std_lesion'):.3f}")
    return "\n".join(lines)


def future_wiring_points() -> str:
    """Documented future integration points for the UQ report."""
    return (
        "Future wiring points:\n"
        "1. runbundle/run.py --emit: call analyze_ensemble_bundle(mean, std, mask) "
        "after ensemble_infer and store under results['uq_report'].\n"
        "2. WS-4 observer sensitivity: feed ensemble std into the second-observer "
        "channel to test whether low-confidence regions flip detectability.\n"
        "3. Per-artefact UQ: combine with artefacts.py probes (metal/motion/...) to "
        "report confidence degradation by artefact class.")
