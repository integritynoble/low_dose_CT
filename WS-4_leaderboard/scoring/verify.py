"""Paired submission gate for the WS-4 leaderboard (low-dose-ct.md §4, Rung 1).

Every submission must report **both** a fidelity number (PSNR/SSIM) **and** a task
detectability number measured on the WS-4 task specification (:mod:`task_spec`).
"Both numbers or neither": a result that reports PSNR without detectability is not
publishable and is rejected before it reaches the leaderboard.

The detectability side must include the **discriminating** index -- the
frequency-domain ``detectability-freq-v1`` ROI BandER (``bander_roi``). The
insertion-based observers (CNR / CHO-AUC / NPWE) are carried for transparency but
do not satisfy the gate alone. This is what Rung 1 of ``RUNG_REGISTRY.md`` declares
("insertion-based CNR/CHO/NPWE remain non-discriminative on real anatomy ...
reported as transparency"), and until 2026-09-04 the code did not enforce it: any
one of the three sufficed, so a submission could pass on a metric the permanent
blur trap *wins*.

This module is a dependency-free re-implementation of the paired gate semantics that
WS-3 wired into its RunBundle entrypoint
(``WS-3_reference_method/runbundle/run.py`` -> ``evaluation.validate_paired_report``),
kept in WS-4 so the leaderboard can verify submissions independently without importing
the WS-3 package (the leaderboard is the referee, not a contestant).
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List

from .task_spec import (
    DETECTABILITY_FIELDS,
    DISCRIMINATING_FIELDS,
    FIDELITY_FIELDS,
    FREQ_SUPPLEMENTARY_FIELDS,
    TASK_LABEL,
    TRANSPARENCY_FIELDS,
)

#: The versioned detectability protocol every WS-4 number must have been measured
#: under (task_spec's signal + ROI protocol). Claim-bound provenance (§2-D) ties
#: a submission to this protocol id and rejects numbers whose claim names a
#: different protocol.
PROTOCOL_ID = "detectability-freq-v1"


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
            for f in DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS:
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
        for f in DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS:
            if f in det:
                m[f] = det[f]
        m["task"] = det.get("task") or det.get("task_label") or det.get("label")
        return {"submission": m}

    m = {"name": result.get("method", "submission")}
    for f in FIDELITY_FIELDS + DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS:
        if f in result:
            m[f] = result[f]
    m["task"] = result.get("task") or result.get("task_label") or result.get("label")
    return {"submission": m}


def check_paired_submission(metrics: Dict) -> List[str]:
    """Enforce the §4 paired rule on one method's metrics.

    Two conditions, both required:

    1. **Paired** (§4 both-or-neither): a fidelity number *and* a detectability
       number, never one alone.
    2. **Discriminating** (Rung 1): the detectability side must include the
       frequency-domain ROI BandER (``bander_roi``). The insertion-based indices
       (CNR / CHO-AUC / NPWE) are transparency-only and do not satisfy the gate
       by themselves -- the permanent blur trap *outscores* real methods on CNR
       (1.08-2.23x on the simulated arm) and saturates CHO-AUC at 1.000 on real
       anatomy, so a gate resting on them admits the cheat it exists to catch.

    Reported metrics must be finite numbers, never booleans or strings.
    Null optional metrics remain absent. A valid alternative fidelity metric
    does not excuse an invalid value supplied for another metric.

    Returns a list of violations; empty list = this paired gate passes.
    Other publication checks still apply.
    """
    errors: List[str] = []
    if not isinstance(metrics, dict):
        return ["metrics is not an object"]

    # Task identity (§2-A): every submission must declare the WS-4 task it was
    # measured on. A missing, non-string or different ``task`` means the numbers
    # were measured on a task other than the one the board scores, so they are
    # not comparable and must not be published under this board's identity.
    task = metrics.get("task")
    if task is None:
        errors.append("submission does not declare the WS-4 task it was measured on "
                      "(task must be %r)" % TASK_LABEL)
    elif not isinstance(task, str):
        errors.append("submission task must be a string, got %s" % type(task).__name__)
    elif task != TASK_LABEL:
        errors.append("submission task %r is not the WS-4 task %r; numbers measured "
                      "on a different task are not comparable" % (task, TASK_LABEL))

    for field in FIDELITY_FIELDS + DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS:
        value = metrics.get(field)
        if value is None:
            continue
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or (isinstance(value, float) and not math.isfinite(value))):
            errors.append(f"{field} must be a finite number (not a boolean or string)")

    has_fidelity = any(metrics.get(f) is not None for f in FIDELITY_FIELDS)
    has_discriminating = any(metrics.get(f) is not None for f in DISCRIMINATING_FIELDS)
    has_transparency = any(metrics.get(f) is not None for f in TRANSPARENCY_FIELDS)
    has_detect = has_discriminating or has_transparency

    if not has_fidelity and not has_detect:
        errors.append("submission carries neither fidelity (psnr_db/ssim) nor "
                      "detectability (bander_roi/cnr_mean/cho_auc_mean/npwe_mean)")
        return errors
    if has_fidelity and not has_detect:
        errors.append("fidelity without detectability is not publishable "
                      "(§4: both numbers or neither)")
    if has_detect and not has_fidelity:
        errors.append("detectability without fidelity is not publishable "
                      "(§4: both numbers or neither)")
    if has_detect and not has_discriminating:
        errors.append(
            "detectability reports only insertion-based indices "
            "(" + "/".join(TRANSPARENCY_FIELDS) + "); the discriminating "
            "frequency-domain index " + "/".join(DISCRIMINATING_FIELDS) +
            " (detectability-freq-v1 ROI BandER) is required (Rung 1: the blur "
            "trap outscores real methods on CNR and saturates CHO-AUC, so these "
            "indices are transparency-only)")
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


# ---------------------------------------------------------------------------
# §2-D claim-bound provenance
# ---------------------------------------------------------------------------

def _canonical_bytes(obj: Any) -> bytes:
    """Deterministic JSON serialisation used for every provenance hash."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def provenance_sha256(obj: Any) -> str:
    """SHA-256 of a canonicalised JSON object (data manifest / model weights)."""
    return hashlib.sha256(_canonical_bytes(obj)).hexdigest()


def _collect_patient_ids(result: Any, found: set) -> None:
    """Collect every ``patient_id`` (or ``patient_ids`` list) anywhere in the
    result. The bootstrap gate uses this to tell a real patient-level submission
    from a stack of slices masquerading as independent patients."""
    if isinstance(result, dict):
        for key, value in result.items():
            if key == "patient_id" and isinstance(value, str) and value.strip():
                found.add(value)
            elif key == "patient_ids" and isinstance(value, list):
                for pid in value:
                    if isinstance(pid, str) and pid.strip():
                        found.add(pid)
            else:
                _collect_patient_ids(value, found)
    elif isinstance(result, list):
        for item in result:
            _collect_patient_ids(item, found)


def check_claim_bound_provenance(result: Dict) -> List[str]:
    """§2-D: the submission's numbers must be bound to the evidence they claim.

    A result is publishable only when it declares a **claim** naming the versioned
    task / protocol id, the hashes of the data manifest and the model weights it
    was produced from, and the evaluator version -- and when the hashes actually
    match the evidence shipped with the result. Without this, an unverifiable
    number could be published under the board's identity, and a claim pointing at
    a different task or protocol must be refused rather than silently recorded.

    Also enforced here: a claim that requests patient-level bootstrap must carry
    ``patient_id`` evidence. Bootstrap aggregation over slices without patient
    identity would let one patient's many slices count as many independent
    patients (see ``bootstrap_lidc_sim`` patient_id refusal).

    Returns a list of violations; empty list = provenance gate passes.
    """
    errors: List[str] = []
    claim = _as_dict(result.get("claim"))
    evidence = _as_dict(result.get("evidence"))

    if not claim:
        errors.append(
            "submission declares no claim (claim.task_id / claim.protocol_id / "
            "claim.data_manifest_sha256 / claim.model_sha256 / "
            "claim.evaluator_version are required): without provenance the "
            "submission is not publishable")
        return errors

    required = ("task_id", "protocol_id", "data_manifest_sha256",
                "model_sha256", "evaluator_version")
    for key in required:
        if not claim.get(key):
            errors.append("claim.%s is missing or empty" % key)

    if claim.get("task_id") is not None and claim["task_id"] != TASK_LABEL:
        errors.append("claim.task_id %r is not the WS-4 task %r; the numbers are "
                      "claimed for a different task and are not comparable"
                      % (claim["task_id"], TASK_LABEL))
    if claim.get("protocol_id") is not None and claim["protocol_id"] != PROTOCOL_ID:
        errors.append("claim.protocol_id %r is not the expected %r; the numbers "
                      "were not measured under detectability-freq-v1"
                      % (claim["protocol_id"], PROTOCOL_ID))

    if claim.get("data_manifest_sha256"):
        manifest = evidence.get("data_manifest")
        if not isinstance(manifest, dict):
            errors.append("claim declares data_manifest_sha256 but "
                          "evidence.data_manifest is missing or not an object")
        elif provenance_sha256(manifest) != claim["data_manifest_sha256"]:
            errors.append("claim.data_manifest_sha256 does not match the "
                          "evidence.data_manifest shipped with the result")

    if claim.get("model_sha256"):
        weights = evidence.get("model_weights")
        if not isinstance(weights, dict):
            errors.append("claim declares model_sha256 but evidence.model_weights "
                          "is missing or not an object")
        elif provenance_sha256(weights) != claim["model_sha256"]:
            errors.append("claim.model_sha256 does not match the "
                          "evidence.model_weights shipped with the result")

    if (claim.get("bootstrap_level") == "patient"
            or claim.get("aggregation") == "patient-level"):
        patient_ids: set = set()
        _collect_patient_ids(result, patient_ids)
        if not patient_ids:
            errors.append(
                "claim requests patient-level bootstrap but the result carries no "
                "patient_id anywhere; slices of one patient could be counted as "
                "independent patients")

    return errors


# ---------------------------------------------------------------------------
# Task 4 (2026-09-21): input-bound provenance
#
# ``check_claim_bound_provenance`` proves *internal consistency* of the submitted
# JSON (claim hashes match the shipped evidence objects). It does not prove that
# those bytes were actually evaluated. ``check_input_bound_provenance`` adds the
# runtime byte/hash binding of the three input classes -- model checkpoint file
# bytes, ASSET_MANIFEST membership, and slice/result patient mapping against a
# fixed split source -- plus method/task/dose identity binding. It is a pure
# read-only evidence computation: it never certifies, never writes, and never
# invents a hash.
# ---------------------------------------------------------------------------

def check_input_bound_provenance(result: Dict, *,
                                 method: Optional[str] = None,
                                 vendor: Optional[str] = None,
                                 dose: Optional[str] = None,
                                 bundle_dir: Optional[str] = None,
                                 checkpoint_dir: Optional[str] = None,
                                 manifest_path: Optional[str] = None,
                                 splits_dir: Optional[str] = None) -> Dict:
    """Runtime input-binding checks for a submitted result (Task 4).

    Composes the JSON-internal gate (``check_claim_bound_provenance``) with the
    runtime three-class binding from :mod:`scoring.binding`. Every binding fact is
    computed from the filesystem (checkpoint bytes via ``hashlib``, parsed
    ASSET_MANIFEST, parsed fixed split source); no self-reported JSON field is
    accepted as a binding source on its own.

    Returns a dict::

        {"claim": [internal-consistency violations],
         "binding": {"status": PASS|UNVERIFIED|FAIL,
                     "ok": bool,
                     "checks": {check: status},
                     "details": {check: detail},
                     "violations": [...],   # FAIL: hard rejection
                     "unverified": [...]}}  # UNVERIFIED: not certified

    The result must stay unverified / pending whenever ``unverified`` is
    non-empty; only ``ok`` and an empty ``unverified`` together certify inputs.
    """
    from .binding import check_input_binding

    claim_errors = check_claim_bound_provenance(result)
    binding = check_input_binding(
        result, method=method, vendor=vendor, dose=dose,
        bundle_dir=bundle_dir, checkpoint_dir=checkpoint_dir,
        manifest_path=manifest_path, splits_dir=splits_dir)
    return {
        "claim": claim_errors,
        "binding": binding.to_dict(),
    }
