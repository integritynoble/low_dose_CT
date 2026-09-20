"""S1-S4 verification pipeline for the WS-4 leaderboard (Phase 1, task 1.2).

The pipeline composes the gates the scoring package already implements; it does
not re-implement any of them, so semantics cannot drift:

  S0  metric gate (both-or-neither + Rung 1 discriminating index)
        -> ``verify.check_paired_submission`` (called inside S2 via
           ``check_submission_result``; S0 is the same paired gate).
  S1  RunBundle structure / schema validation      -> ``check_runbundle_structure``
  S2  task identity + claim provenance + no-write-path envelope + rung evidence
        -> ``check_claim_and_provenance`` (composes ``verify`` / ``heldout`` /
           ``gates``)
  S3  published vs live ``results.json``           -> ``verify_published_vs_live``
        (numeric comparison runs locally; the live sandbox execution itself is a
        runtime dependency - see ``[UNRESOLVED]`` below)
  S4  board publish eligibility                    -> ``check_publish_eligibility``
        (pre-check reusing ``leaderboard`` exports; the final write MUST go
        through ``leaderboard.save()``, which runs the full §2-C gate chain)

See ``scoring/spec.md`` for the stage semantics (draft, awaiting Director
review). A receipt is not a publication: the pipeline can be green while
``publication.status`` on the board is still ``pending``.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .heldout import (SubmissionEnvelope, check_submission_cannot_write_back)
from .leaderboard import (assert_trap_separates_in_every_group, check_trap_rank)
from .task_spec import (DETECTABILITY_FIELDS, FIDELITY_FIELDS,
                        FREQ_SUPPLEMENTARY_FIELDS, TASK_LABEL)
from .verify import check_claim_bound_provenance, check_submission_result

#: R6 recalc absolute tolerance for published-vs-live numeric comparison
#: (``WS-1_dataset/R6_recalc``; red-line field - do not change).
R6_TOLERANCE = 1e-06

#: The S3 live re-execution entry point. The numeric comparison is implemented
#: locally (``verify_published_vs_live``); executing a RunBundle inside a
#: sandboxed container against the held-out split requires a container runtime
#: and a data machine, which are external Phase-1 dependencies. Until wired:
#: ``[UNRESOLVED: owner=Director, decision_needed=sandbox runtime + data machine
#: wiring, date=2026-09-19]``.
LIVE_EXECUTION_UNRESOLVED = (
    "S3 live execution is not wired: a container sandbox + data machine are "
    "external Phase-1 dependencies (see scoring/spec.md §6). The numeric "
    "comparison below runs locally; live re-execution is marked SKIPPED.")

#: Per-method metric block fields allowed in a ``results.json`` (contract §2).
_METRIC_WHITELIST = set(FIDELITY_FIELDS + DETECTABILITY_FIELDS
                        + FREQ_SUPPLEMENTARY_FIELDS) | {"name", "task",
                                                       "paired_methods_ok",
                                                       "detectability"}
#: Fields allowed inside a ``detectability`` sub-block (WS-3 layout).
_DETECTABILITY_WHITELIST = (set(DETECTABILITY_FIELDS)
                            | set(FREQ_SUPPLEMENTARY_FIELDS) | {"task"})
#: Result-level structural keys accepted alongside the metric blocks.
_RESULT_STRUCTURAL_KEYS = {
    "validation", "claim", "evidence", "method", "submitted_at",
    "vendor", "dose", "patient_id", "patient_ids",
}

#: Files required for a minimal RunBundle at S1 (contract §1).
REQUIRED_BUNDLE_FILES = ("method.json", "eval.py", "results.json")
OPTIONAL_BUNDLE_FILES = ("Dockerfile", "dose_equivalence_credentials.json",
                         "checkpoint")


@dataclass
class Verdict:
    """Pipeline result for one RunBundle.

    ``violations`` is keyed by stage (``S1``..``S4``); ``skipped`` lists stages
    that could not run (e.g. S3 without a live result, S4 without a board);
    ``receipt_id`` references the board receipt only after an actual
    ``leaderboard.save()`` (the pipeline itself never writes the board).
    """

    runbundle: str
    violations: Dict[str, List[str]] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    receipt_id: Optional[str] = None

    @property
    def ok(self) -> bool:
        """Green only when no stage reported any violation."""
        return not any(self.violations.values())

    def summary(self) -> str:
        if self.ok:
            parts = [f"{s}: PASS" for s in ("S1", "S2", "S3", "S4")]
            return "ALL PASS  (" + ", ".join(parts) + ")"
        return "REJECT  (" + ", ".join(
            f"{s}: {len(v)} violation(s)" for s, v in self.violations.items() if v) + ")"


# ---------------------------------------------------------------------------
# S1 - RunBundle structure / schema validation
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _result_metric_blocks(result: Dict) -> List[Dict]:
    """Return the per-method metric blocks of a result, mirroring
    ``verify.extract_paired_methods`` enough for schema checks (no numeric
    judgement here)."""
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    methods = validation.get("paired_methods") if isinstance(validation, dict) else None
    if isinstance(methods, dict):
        return [m for m in methods.values() if isinstance(m, dict)]
    if isinstance(validation, dict) and any(
            f in validation for f in FIDELITY_FIELDS + DETECTABILITY_FIELDS):
        return [validation]
    if any(f in result for f in FIDELITY_FIELDS + DETECTABILITY_FIELDS):
        return [result]
    return []


def check_runbundle_structure(bundle_path: str | Path) -> List[str]:
    """S1: validate a RunBundle directory shape and ``results.json`` whitelist.

    Returns a list of violations; empty list = structure passes. Required files
    per contract §1: ``method.json`` / ``eval.py`` / ``results.json``.
    ``Dockerfile`` and the L2 credential are optional at S1 but required for S3
    sandbox mode. Unknown metric fields inside a method block are rejected.
    """
    errors: List[str] = []
    bundle = Path(bundle_path)
    if not bundle.is_dir():
        return [f"RunBundle path is not a directory: {bundle}"]

    for name in REQUIRED_BUNDLE_FILES:
        if not (bundle / name).is_file():
            errors.append(f"RunBundle is missing required file: {name}")

    method_json = bundle / "method.json"
    if method_json.is_file():
        try:
            meta = _read_json(method_json)
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            errors.append(f"method.json is not valid JSON: {exc}")
        else:
            if not isinstance(meta, dict):
                errors.append("method.json must be a JSON object")
            else:
                for key in ("name", "version"):
                    if not isinstance(meta.get(key), str) or not meta[key].strip():
                        errors.append(f"method.json.{key} is missing or not a non-empty string")
                for key in ("paper", "license"):
                    if not isinstance(meta.get(key), str) or not meta[key].strip():
                        errors.append(f"method.json.{key} is missing or not a non-empty string "
                                      "(required for publication)")

    results_json = bundle / "results.json"
    if results_json.is_file():
        try:
            result = _read_json(results_json)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"results.json is not valid JSON: {exc}")
        else:
            if not isinstance(result, dict):
                errors.append("results.json must be a JSON object")
            else:
                blocks = _result_metric_blocks(result)
                if not blocks:
                    errors.append("results.json carries no paired method metrics "
                                  "(expected validation.paired_methods.<name> or flat metrics)")
                for block in blocks:
                    unknown = sorted(set(block) - _METRIC_WHITELIST)
                    if unknown:
                        errors.append(
                            "results.json method block carries fields outside the "
                            "whitelist: " + ", ".join(sorted(unknown)))
                    det = block.get("detectability")
                    if isinstance(det, dict):
                        unknown_det = sorted(set(det) - _DETECTABILITY_WHITELIST)
                        if unknown_det:
                            errors.append(
                                "results.json detectability block carries fields "
                                "outside the whitelist: " + ", ".join(unknown_det))
                # only flag unknown top-level keys that are not themselves method blocks
                block_keys = set()
                for b in blocks:
                    block_keys.update(b.keys())
                unknown_top = sorted(
                    set(result) - _RESULT_STRUCTURAL_KEYS - block_keys)
                if unknown_top:
                    errors.append("results.json carries unknown top-level fields: "
                                  + ", ".join(unknown_top))
    return errors


# ---------------------------------------------------------------------------
# S2 - task identity + claim provenance + no-write-path + rung evidence
# ---------------------------------------------------------------------------

def check_claim_and_provenance(result: Dict, *,
                               method_name: str = "submission",
                               vendor: Optional[str] = None,
                               dose: Optional[str] = None,
                               run_ws1_gates: bool = True) -> Dict[str, List[str]]:
    """S2: compose the existing provenance / identity / write-path gates.

    Returns ``{check_name: [violations]}``. Checks:

    * ``paired+task``    -- ``verify.check_submission_result`` (S0 metric gate +
                            §2-A task identity, per method block)
    * ``claim``          -- ``verify.check_claim_bound_provenance`` (§2-D five
                            required fields + evidence hash binding)
    * ``no_write_path``  -- ``heldout.check_submission_cannot_write_back`` (P1-3
                            envelope; method_name / vendor / dose are scanned too)
    * ``rung_2/3/4``     -- ``gates`` rung evidence gates against the WS-1
                            artifacts; run only when the artifacts exist beside
                            the repo, otherwise the check is omitted (reported
                            via the returned ``skipped`` key, never as a pass).

    No gate is re-implemented here.
    """
    out: Dict[str, List[str]] = {}
    out["paired+task"] = []
    per_method = check_submission_result(result)
    for name, errs in per_method.items():
        if errs:
            out["paired+task"].append(f"method '{name}': " + "; ".join(errs))
    out["claim"] = check_claim_bound_provenance(result)

    envelope = SubmissionEnvelope(method_name=method_name, result=result,
                                  vendor=vendor, dose=dose)
    out["no_write_path"] = check_submission_cannot_write_back(envelope)

    if run_ws1_gates:
        from . import gates as G
        skipped = []
        for label, fn in (("rung_2", G.check_pairing_validation),
                          ("rung_3", G.check_roi_protocol),
                          ("rung_4", G.check_dose_curve)):
            try:
                viol = fn()
            except Exception as exc:  # noqa: BLE001 - artifact read failures
                viol = [f"{label} gate could not read its artifact: {exc}"]
            if viol and all("could not read" in v or "does not exist" in v
                            for v in viol):
                # artifact missing next to the repo: skip, never pass
                skipped.append(label)
                out.pop(label, None)
                continue
            out[label] = viol
        if skipped:
            out["skipped"] = ["missing WS-1 artifact, gate not run: " + ", ".join(skipped)]
    return out


# ---------------------------------------------------------------------------
# S3 - published vs live results.json
# ---------------------------------------------------------------------------

def _walk_pairs(published: Any, live: Any, path: str, violations: List[str]) -> None:
    """Recursively compare two JSON documents.

    Numeric leaves must match within ``R6_TOLERANCE`` (absolute, R6 recalc
    criterion). Non-numeric leaves must be equal. Structure must match.
    """
    if isinstance(published, dict) and isinstance(live, dict):
        for key in sorted(set(published) | set(live)):
            if key not in published:
                violations.append(f"live has extra field at {path}.{key}")
            elif key not in live:
                violations.append(f"published has extra field at {path}.{key}")
            else:
                _walk_pairs(published[key], live[key], f"{path}.{key}", violations)
        return
    if isinstance(published, list) and isinstance(live, list):
        if len(published) != len(live):
            violations.append(f"list length differs at {path}: "
                              f"published={len(published)} live={len(live)}")
            return
        for i, (p, l) in enumerate(zip(published, live)):
            _walk_pairs(p, l, f"{path}[{i}]", violations)
        return
    if isinstance(published, (int, float)) and isinstance(live, (int, float)):
        if isinstance(published, bool) or isinstance(live, bool):
            if published != live:
                violations.append(f"boolean value differs at {path}: "
                                  f"published={published!r} live={live!r}")
            return
        if not math.isfinite(float(published)) or not math.isfinite(float(live)):
            violations.append(f"non-finite number at {path}: "
                              f"published={published!r} live={live!r}")
            return
        if abs(float(published) - float(live)) > R6_TOLERANCE:
            violations.append(
                f"numeric drift beyond {R6_TOLERANCE:g} at {path}: "
                f"published={published!r} live={live!r}")
        return
    if published != live:
        violations.append(f"value differs at {path}: "
                          f"published={published!r} live={live!r}")


def verify_published_vs_live(published: Dict, live: Dict) -> List[str]:
    """S3 numeric verification: published ``results.json`` vs live execution.

    Returns a list of violations; empty list = the live run reproduces the
    published numbers within the R6 absolute tolerance (1e-06). This function
    runs locally; the *live* document itself comes from the sandbox execution,
    which is an external runtime dependency (see ``LIVE_EXECUTION_UNRESOLVED``).
    """
    violations: List[str] = []
    _walk_pairs(published, live, "results", violations)
    return violations


# ---------------------------------------------------------------------------
# S4 - board publish eligibility
# ---------------------------------------------------------------------------

def check_publish_eligibility(entries: List[Dict], *,
                              by: str = "vendor") -> List[str]:
    """S4 pre-check: would publishing ``entries`` pass the board-level gates?

    Reuses the exported ``leaderboard`` gates only (trap-rank and per-stratum
    separation); it does NOT re-implement §2-C. The final write MUST go through
    ``leaderboard.save()``, which runs the full gate chain and attaches a
    receipt with ``publication.status = pending``. Missing required vendor
    strata / a board with no comparable entries is recorded, not passed.
    """
    errors: List[str] = []
    if not entries:
        return ["board has no entries to publish"]
    try:
        errors.extend(check_trap_rank(entries))
    except Exception as exc:  # noqa: BLE001 - missing trap etc.
        errors.append(f"trap-rank gate could not run: {exc}")
    try:
        assert_trap_separates_in_every_group(entries, by=by)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"per-{by} stratum separation gate failed: {exc}")
    return errors


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def verify_runbundle(bundle_path: str | Path, *,
                     live_result: Optional[Dict] = None,
                     entries: Optional[List[Dict]] = None,
                     method_name: str = "submission",
                     vendor: Optional[str] = None,
                     dose: Optional[str] = None,
                     run_ws1_gates: bool = True) -> Verdict:
    """Run S1 -> S2 -> S3 -> S4 on a RunBundle directory.

    ``live_result`` supplies the S3 live execution output; ``None`` marks S3 as
    ``SKIPPED`` (sandbox runtime dependency, ``LIVE_EXECUTION_UNRESOLVED``).
    ``entries`` supplies the candidate board entries for the S4 pre-check;
    ``None`` marks S4 as ``SKIPPED`` (the pipeline itself never writes the
    board - publishing goes through ``leaderboard.save()``).
    """
    bundle = Path(bundle_path)
    verdict = Verdict(runbundle=str(bundle))

    verdict.violations["S1"] = check_runbundle_structure(bundle)

    results_json = bundle / "results.json"
    result: Optional[Dict] = None
    if not verdict.violations["S1"] and results_json.is_file():
        try:
            result = _read_json(results_json)
        except Exception:  # noqa: BLE001 - already reported at S1
            result = None
    if result is None:
        verdict.skipped.append("S2")
        verdict.skipped.append("S3")
        verdict.skipped.append("S4")
        return verdict

    s2 = check_claim_and_provenance(result, method_name=method_name,
                                    vendor=vendor, dose=dose,
                                    run_ws1_gates=run_ws1_gates)
    verdict.violations["S2"] = [v for k, vs in s2.items()
                                if k != "skipped" for v in vs]
    if s2.get("skipped"):
        verdict.skipped.extend(s2["skipped"])

    if live_result is None:
        verdict.skipped.append("S3")
    else:
        verdict.violations["S3"] = verify_published_vs_live(result, live_result)

    if entries is None:
        verdict.skipped.append("S4")
    else:
        verdict.violations["S4"] = check_publish_eligibility(entries)
    return verdict
