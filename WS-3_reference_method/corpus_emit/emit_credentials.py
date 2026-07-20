"""Credential-emission step for the WS-3 derived-reconstruction corpus.

This module turns per-cohort task scores into the ``credential.json`` records
that the *Scientific Data* Data Descriptor releases, in exactly the wire format
that ``pwm-audit`` and ``deposit/dataset_metadata.schema.json`` expect.

Signal-equivalence credentials are **cohort/stratum-level** artifacts: one
credential summarises a whole test cohort (``n_test`` patients) for a given
``(task, signal_ratio, subpopulation)``. They are therefore written under
``credentials/`` in the corpus, *not* inside the per-scan record folders
(which hold the reconstruction / uncertainty / error / task-score maps).

Typical Phase-3 usage::

    from emit_credentials import StratumSpec, AucScores, emit_stratum_credential, rebuild_index

    spec = StratumSpec(
        task_name="lung_nodule_5mm", metric="auc",
        signal_ratio=0.25, subpopulation="adult_chest_pwm_l3_test_v1",
        epsilon=0.05, method="pwm_ref_v1", reference_method="full_dose_fbp",
        anatomy="chest",
    )
    emit_stratum_credential(corpus_root, spec, AucScores(a_pos, a_neg, b_pos, b_neg))
    ...
    rebuild_index(corpus_root)   # writes credentials/all_credentials.jsonl

The score arrays come from the frozen downstream task evaluation (lung-nodule
detector for AUC; segmentation Dice / contrast-recovery for the other tasks);
this module is agnostic to how they were produced.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from pwm_dose_equivalence import (
    Task,
    audit_credential,
    signal_equivalence_credential,
)
from pwm_dose_equivalence.credential import SignalEquivalenceCredential

__all__ = [
    "AucScores",
    "PairedScores",
    "StratumSpec",
    "dose_tag",
    "build_credential",
    "emit_stratum_credential",
    "rebuild_index",
    "verify_corpus_credentials",
    "CredentialEmitError",
]


class CredentialEmitError(RuntimeError):
    """Raised when a credential fails its internal audit at emit time."""


@dataclass(frozen=True)
class AucScores:
    """Paired case-level detector scores for an AUC task.

    ``*_pos`` / ``*_neg`` are the candidate (``a``) and reference (``b``) method
    scores on the positive and negative cases respectively.
    """

    a_pos: Sequence[float]
    a_neg: Sequence[float]
    b_pos: Sequence[float]
    b_neg: Sequence[float]

    def n_test(self) -> int:
        return len(self.a_pos) + len(self.a_neg)


@dataclass(frozen=True)
class PairedScores:
    """Per-patient paired scores for a general metric (dice / mae / contrast_recovery)."""

    paired_a: Sequence[float]
    paired_b: Sequence[float]

    def n_test(self) -> int:
        return len(self.paired_a)


@dataclass(frozen=True)
class StratumSpec:
    """Identifies one credential stratum and its credential parameters."""

    task_name: str
    metric: str  # "auc" | "dice" | "mae" | "contrast_recovery"
    signal_ratio: float
    subpopulation: str
    epsilon: float
    alpha: float = 0.05
    method: str = "pwm_ref_v1"
    reference_method: str = "full_dose_fbp"
    modality: str = "CT"
    seed: int = 42
    n_bootstrap: int = 10_000
    # Provenance for the index (None = pooled across that axis)
    vendor: str | None = None
    anatomy: str | None = None
    ground_truth_protocol: str | None = None

    def slug(self) -> str:
        """Filesystem-safe credential stem: ``<method>__<vendor|pooled>``.

        Task and dose are encoded by the directory path
        (``credentials/<task>/<dose_tag>/``), so the stem only needs to
        disambiguate the method (reference vs each baseline) and the vendor
        stratum (or ``pooled``).
        """
        vendor = self.vendor or "pooled"
        return f"{_safe(self.method)}__{_safe(vendor)}"


def _safe(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", s).strip("_")


def dose_tag(signal_ratio: float) -> str:
    """Canonical dose-folder tag, e.g. 0.25 -> 'r025', 0.10 -> 'r010', 1.0 -> 'r100'."""
    pct = int(round(signal_ratio * 100))
    if not 0 < pct <= 100:
        raise ValueError(f"signal_ratio must be in (0, 1]; got {signal_ratio!r}")
    return f"r{pct:03d}"


def build_credential(
    spec: StratumSpec,
    scores: AucScores | PairedScores,
) -> SignalEquivalenceCredential:
    """Compute a credential for one stratum via the WS-2 library.

    Dispatches on ``spec.metric``: AUC tasks consume :class:`AucScores`
    (DeLong estimator by default); all other metrics consume
    :class:`PairedScores` (percentile bootstrap).
    """
    task = Task(
        name=spec.task_name,
        metric=spec.metric,  # type: ignore[arg-type]
        ground_truth_protocol=spec.ground_truth_protocol,
    )
    common = dict(
        signal_ratio=spec.signal_ratio,
        modality=spec.modality,  # type: ignore[arg-type]
        task=task,
        subpopulation=spec.subpopulation,
        epsilon=spec.epsilon,
        alpha=spec.alpha,
        method=spec.method,
        reference_method=spec.reference_method,
        seed=spec.seed,
        n_bootstrap=spec.n_bootstrap,
    )

    if spec.metric == "auc":
        if not isinstance(scores, AucScores):
            raise TypeError("metric='auc' requires AucScores (a_pos/a_neg/b_pos/b_neg).")
        return signal_equivalence_credential(
            a_pos=_arr(scores.a_pos),
            a_neg=_arr(scores.a_neg),
            b_pos=_arr(scores.b_pos),
            b_neg=_arr(scores.b_neg),
            **common,
        )
    if not isinstance(scores, PairedScores):
        raise TypeError(
            f"metric={spec.metric!r} requires PairedScores (paired_a/paired_b)."
        )
    return signal_equivalence_credential(
        paired_a=_arr(scores.paired_a),
        paired_b=_arr(scores.paired_b),
        **common,
    )


def emit_stratum_credential(
    corpus_root: Path | str,
    spec: StratumSpec,
    scores: AucScores | PairedScores,
    *,
    require_audit_ok: bool = True,
) -> Path:
    """Build, audit, and write one stratum credential to the corpus.

    Path: ``credentials/<task>/<dose_tag>/<slug>.json``.

    With ``require_audit_ok`` (default), a credential that fails its internal
    ``audit_credential`` hard checks raises :class:`CredentialEmitError` rather
    than landing a broken record in the corpus. Soft warnings (e.g. BCa
    headline, undersized PASS) do not block emission but are surfaced by
    :func:`verify_corpus_credentials`.
    """
    corpus_root = Path(corpus_root)
    cred = build_credential(spec, scores)
    payload = cred.to_dict()

    audit = audit_credential(payload)
    if require_audit_ok and not audit.ok:
        raise CredentialEmitError(
            f"credential for stratum {spec.task_name}/{dose_tag(spec.signal_ratio)}/"
            f"{spec.slug()} failed audit: issues={audit.issues}"
        )

    out_dir = corpus_root / "credentials" / _safe(spec.task_name) / dose_tag(spec.signal_ratio)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{spec.slug()}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_path


def rebuild_index(corpus_root: Path | str) -> Path:
    """(Re)write ``credentials/all_credentials.jsonl`` from every credential on disk.

    One JSON object per line, sorted by relative path for stable diffs, with the
    fields a reuser queries on (task, dose, subpopulation, verdict, CI) plus the
    audit verdict and the relative path to the full credential.
    """
    corpus_root = Path(corpus_root)
    cred_root = corpus_root / "credentials"
    cred_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for path in sorted(cred_root.rglob("*.json")):
        if path.name == "all_credentials.jsonl":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        c = payload["credential"]
        audit = audit_credential(payload)
        rows.append(
            {
                "path": str(path.relative_to(corpus_root)),
                "task": c["task"]["name"],
                "metric": c["task"]["metric"],
                "signal_ratio": c["signal_ratio"],
                "subpopulation": c["subpopulation"],
                "epsilon": c["epsilon"],
                "alpha": c["alpha"],
                "n_test": c["n_test"],
                "verdict": c["verdict"],
                "delta_mean": c["delta_mean"],
                "delta_ci_low": c["delta_ci_low"],
                "delta_ci_high": c["delta_ci_high"],
                "framework_hash": payload["framework_hash"],
                "audit_ok": audit.ok,
            }
        )

    index_path = cred_root / "all_credentials.jsonl"
    with index_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return index_path


def verify_corpus_credentials(corpus_root: Path | str) -> dict:
    """Audit every credential in the corpus; return a summary report.

    Backs deposit checklist §4: ``ok`` is True only when every credential
    passes its hard audit checks. ``warnings`` collects soft signals
    (undersized PASS, BCa headline, unknown framework hash) for review.
    """
    corpus_root = Path(corpus_root)
    cred_root = corpus_root / "credentials"
    failures: list[dict] = []
    warnings_list: list[dict] = []
    n = 0
    for path in sorted(cred_root.rglob("*.json")):
        if path.name == "all_credentials.jsonl":
            continue
        n += 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        audit = audit_credential(payload)
        rel = str(path.relative_to(corpus_root))
        if not audit.ok:
            failures.append({"path": rel, "issues": audit.issues})
        if audit.warnings:
            warnings_list.append({"path": rel, "warnings": audit.warnings})
    return {
        "n_credentials": n,
        "ok": len(failures) == 0,
        "failures": failures,
        "warnings": warnings_list,
    }


def _arr(x: Sequence[float]):
    import numpy as np

    return np.asarray(x, dtype=float)
