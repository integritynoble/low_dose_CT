"""Artefact-class sub-scores (P2-6).

low-dose-ct.md §7.5 / §5 "artefact-specific behaviour": the evaluation must be able
to report per-artefact-class scores (metal / motion / truncation / ring-streak / ...)
instead of only a global mean.  This module provides an *extensible configuration
layer*: it does not re-run the full dataset now, but it defines the registry,
the naming convention and the validation helpers so that any future artefact probe
can be plugged in and scored without changing the eval schema.

Design decisions
----------------
* ``ARTEFACT_CLASSES`` is the single source of truth for known classes.
* A per-artefact score entry follows the paired-gate convention from evaluation.py:
  it always carries ``fidelity`` (psnr_db) **and** ``detectability`` (cnr or auc)
  together -- both numbers or neither (low-dose-ct.md §4).
* ``validate_artefact_report`` is a gate used by the RunBundle; unknown classes or
  unpaired metric fields are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Known artefact classes.  ``blur`` is the permanent in-suite trap (Rung 1.3) and is
# deliberately not listed here as a "deployable" class -- it lives in the paired
# validation block itself.  The classes below are the *deployable* extra probes.
ARTEFACT_CLASSES: dict[str, dict[str, Any]] = {
    "metal": {
        "description": "metal implant streak / photon starvation",
        "fidelity_metric": "psnr_db",
        "detectability_metric": "cnr",
        "min_samples": 1,
    },
    "motion": {
        "description": "patient motion blur / ghosting",
        "fidelity_metric": "psnr_db",
        "detectability_metric": "cnr",
        "min_samples": 1,
    },
    "truncation": {
        "description": "field-of-view truncation artefacts",
        "fidelity_metric": "psnr_db",
        "detectability_metric": "cnr",
        "min_samples": 1,
    },
    "ring_streak": {
        "description": "ring / streak detector calibration artefacts",
        "fidelity_metric": "psnr_db",
        "detectability_metric": "cnr",
        "min_samples": 1,
    },
}


def artefact_class_names() -> list[str]:
    """Known artefact class names, sorted for stable reporting."""
    return sorted(ARTEFACT_CLASSES)


# ---------------------------------------------------------------------------
# Per-artefact score container
# ---------------------------------------------------------------------------

@dataclass
class ArtefactScore:
    """One artefact-class sub-score.  Paired fidelity+detectability by construction.

    ``ok`` is True only when both fields are finite and detectability passes the
    supplied threshold (default: Rose criterion CNR >= 3.0).
    """

    artefact_class: str
    psnr_db: float
    cnr: float
    detectability_threshold: float = 3.0
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        try:
            return float(self.psnr_db) == float(self.psnr_db) and \
                float(self.cnr) >= self.detectability_threshold
        except (TypeError, ValueError):
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "artefact_class": self.artefact_class,
            "fidelity": {"psnr_db": self.psnr_db},
            "detectability": {"cnr": self.cnr, "pass_threshold": self.ok},
            "notes": self.notes,
            "extra": self.extra,
        }


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------

def validate_artefact_report(report: dict[str, Any]) -> list[str]:
    """Gate the artefact sub-report block of a results.json.

    Rejects: unknown artefact classes, missing paired metrics, non-finite values.
    Returns a list of human-readable problems (empty == pass).
    """
    problems: list[str] = []
    scores = report.get("artefact_scores", [])
    if not isinstance(scores, list):
        return ["artefact_scores must be a list"]
    seen: set[str] = set()
    for i, s in enumerate(scores):
        if not isinstance(s, dict):
            problems.append(f"artefact_scores[{i}] not an object")
            continue
        cls = s.get("artefact_class")
        if not isinstance(cls, str) or cls not in ARTEFACT_CLASSES:
            problems.append(f"artefact_scores[{i}]: unknown artefact_class {cls!r}")
            continue
        if cls in seen:
            problems.append(f"artefact_scores[{i}]: duplicate artefact_class {cls!r}")
        seen.add(cls)
        fid = s.get("fidelity") or {}
        det = s.get("detectability") or {}
        psnr = fid.get("psnr_db")
        cnr = det.get("cnr")
        if psnr is None or cnr is None:
            problems.append(
                f"artefact_scores[{i}] ({cls}): paired metrics required "
                f"(fidelity.psnr_db + detectability.cnr) -- both or neither")
            continue
        for name, val in (("psnr_db", psnr), ("cnr", cnr)):
            try:
                fval = float(val)
            except (TypeError, ValueError):
                problems.append(f"artefact_scores[{i}] ({cls}): {name} not numeric")
                continue
            if fval != fval or fval in (float("inf"), float("-inf")):
                problems.append(f"artefact_scores[{i}] ({cls}): {name} not finite")
    return problems


def empty_artefact_block() -> dict[str, Any]:
    """Schema-shaped artefact block with no probes (safe default for self-test)."""
    return {"enabled": True, "artefact_scores": [], "note": "no artefact probes run yet"}


# ---------------------------------------------------------------------------
# Extensible probe interface (future use)
# ---------------------------------------------------------------------------

ArtefactProbe = Callable[[Any], dict[str, float]]  # input -> {psnr_db, cnr}


def register_artefact_probe(artefact_class: str, probe: ArtefactProbe) -> None:
    """Register a scoring probe for an artefact class.

    ``probe`` takes the artefact-perturbed evaluation input and returns a dict with
    at least ``psnr_db`` and ``cnr``.  Registration is additive: existing class
    metadata is not overwritten unless the class already exists and ``probe`` is a
    callable.
    """
    if artefact_class not in ARTEFACT_CLASSES:
        ARTEFACT_CLASSES[artefact_class] = {
            "description": "user-registered artefact class",
            "fidelity_metric": "psnr_db",
            "detectability_metric": "cnr",
            "min_samples": 1,
        }
    if callable(probe):
        ARTEFACT_CLASSES[artefact_class]["probe"] = probe
