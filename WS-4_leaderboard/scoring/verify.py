"""Paired submission gate for the WS-4 leaderboard (low-dose-ct.md §4).

Every submission must report **both** a fidelity number (PSNR/SSIM) **and** a task
detectability number (CNR / CHO-AUC / NPWE) measured on the WS-4 task specification
(:mod:`task_spec`). "Both numbers or neither": a result that reports PSNR without
detectability is not publishable and is rejected before it reaches the leaderboard.

This module is a dependency-free re-implementation of the paired gate semantics that
WS-3 wired into its RunBundle entrypoint
(``WS-3_reference_method/runbundle/run.py`` -> ``evaluation.validate_paired_report``),
kept in WS-4 so the leaderboard can verify submissions independently without importing
the WS-3 package (the leaderboard is the referee, not a contestant).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .task_spec import DETECTABILITY_FIELDS, FIDELITY_FIELDS


def _as_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}


def extract_paired_methods(result: Dict) -> Dict[str, Dict]:
    """Extract per-method paired blocks from a submission result.

    Accepts either the WS-3 RunBundle ``results.json`` layout
    (``validation.paired_methods.<name>`` with ``psnr_db`` / ``ssim`` /
    ``detectability`` per method) or a flat method metrics dict. Returns
    ``{method_name: metrics_dict}`` where each metrics dict has both a fidelity
    field and a detectability field (if the input was flat and paired).
    """
    validation = _as_dict(result.get("validation"))
    methods = _as_dict(validation.get("paired_methods"))
    if methods:
        out: Dict[str, Dict] = {}
        for name, block in methods.items():
            block = _as_dict(block)
            det = _as_dict(block.get("detectability"))
            m = {"name": name}
            for f in FIDELITY_FIELDS:
                if f in block:
                    m[f] = block[f]
            for f in DETECTABILITY_FIELDS:
                if f in det:
                    m[f] = det[f]
            m["task"] = det.get("task") or det.get("task_label") or det.get("label")
            m["paired_methods_ok"] = block.get("paired_methods_ok")
            out[name] = m
        return out

    # Flat submission: either top-level validation block or a bare metrics dict.
    if validation and ("psnr_db" in validation or "detectability" in validation):
        det = _as_dict(validation.get("detectability"))
        m = {"name": validation.get("method", "submission")}
        for f in FIDELITY_FIELDS:
            if f in validation:
                m[f] = validation[f]
        for f in DETECTABILITY_FIELDS:
            if f in det:
                m[f] = det[f]
        m["task"] = det.get("task") or det.get("task_label") or det.get("label")
        return {"submission": m}

    m = {"name": result.get("method", "submission")}
    for f in FIDELITY_FIELDS + DETECTABILITY_FIELDS:
        if f in result:
            m[f] = result[f]
    m["task"] = result.get("task") or result.get("task_label") or result.get("label")
    return {"submission": m}


def check_paired_submission(metrics: Dict) -> List[str]:
    """Enforce the §4 paired rule on one method's metrics.

    Returns a list of violations; empty list = gate passes (publishable).
    """
    errors: List[str] = []
    if not isinstance(metrics, dict):
        return ["metrics is not an object"]

    has_fidelity = any(metrics.get(f) is not None for f in FIDELITY_FIELDS)
    has_detect = any(metrics.get(f) is not None for f in DETECTABILITY_FIELDS)

    if not has_fidelity and not has_detect:
        errors.append("submission carries neither fidelity (psnr_db/ssim) nor "
                      "detectability (cnr_mean/cho_auc_mean/npwe_mean)")
        return errors
    if has_fidelity and not has_detect:
        errors.append("fidelity without detectability is not publishable "
                      "(§4: both numbers or neither)")
    if has_detect and not has_fidelity:
        errors.append("detectability without fidelity is not publishable "
                      "(§4: both numbers or neither)")
    return errors


def check_submission_result(result: Dict) -> Dict[str, List[str]]:
    """Run the paired gate on a full submission result.

    Returns ``{method_name: [violations, ...]}``. An empty dict means every method in
    the submission passes; any non-empty list means that method is not publishable.
    """
    methods = extract_paired_methods(result)
    if not methods:
        return {"submission": ["no paired metrics found in result"]}
    return {name: check_paired_submission(m) for name, m in methods.items()}
