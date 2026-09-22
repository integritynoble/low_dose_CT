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
from .verify import (check_claim_bound_provenance, check_input_bound_provenance,
                     check_submission_result)

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
        """Green only when every required stage ran without violations."""
        return not self.skipped and not any(self.violations.values())

    def summary(self) -> str:
        if not any(self.violations.values()) and self.skipped:
            return "INCOMPLETE  (skipped: " + ", ".join(self.skipped) + ")"
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
                               run_ws1_gates: bool = True,
                               bind_inputs: bool = False) -> Dict[str, List[str]]:
    """S2: compose the existing provenance / identity / write-path gates.

    Returns ``{check_name: [violations]}``. Checks:

    * ``paired+task``    -- ``verify.check_submission_result`` (S0 metric gate +
                            §2-A task identity, per method block)
    * ``claim``          -- ``verify.check_claim_bound_provenance`` (§2-D five
                            required fields + evidence hash binding)
    * ``input_bound``    -- ``verify.check_input_bound_provenance`` (Task 4:
                            runtime byte/hash binding of model checkpoint files,
                            ASSET_MANIFEST membership, patient mapping and
                            method/task/dose identity). Only run when
                            ``bind_inputs=True`` so existing JSON-only fixtures
                            keep their historical verdict. Binding *violations*
                            are returned under this key (hard rejection); inputs
                            that cannot be verified (missing checkpoint /
                            placeholder manifest hash / no fixed patient source)
                            are returned under ``skipped_unverified`` -- never
                            certified, but not a rejection either, so the bundle
                            stays INCOMPLETE.
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

    if bind_inputs:
        # Task 4 (2026-09-21): runtime input-binding. Hard violations reject the
        # bundle; UNVERIFIED inputs are reported as skipped (never certified) so
        # the bundle stays INCOMPLETE instead of claiming a verified state.
        input_bound = check_input_bound_provenance(result, method=method_name,
                                                   vendor=vendor, dose=dose)
        out["input_bound"] = input_bound["binding"]["violations"]
        if input_bound["binding"]["unverified"]:
            out.setdefault("skipped_unverified", []).extend(
                input_bound["binding"]["unverified"])

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
            if type(published) is not type(live) or published != live:
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
                     run_ws1_gates: bool = True,
                     bind_inputs: bool = False) -> Verdict:
    """Run S1 -> S2 -> S3 -> S4 on a RunBundle directory.

    ``live_result`` supplies the S3 live execution output; ``None`` marks S3 as
    ``SKIPPED`` (sandbox runtime dependency, ``LIVE_EXECUTION_UNRESOLVED``).
    ``entries`` supplies the candidate board entries for the S4 pre-check;
    ``None`` marks S4 as ``SKIPPED`` (the pipeline itself never writes the
    board - publishing goes through ``leaderboard.save()``).
    ``bind_inputs=True`` additionally runs the Task 4 runtime input-binding
    checks (model checkpoint bytes / ASSET_MANIFEST / patient mapping); its
    violations reject the bundle, its UNVERIFIED inputs keep it INCOMPLETE.
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
                                    run_ws1_gates=run_ws1_gates,
                                    bind_inputs=bind_inputs)
    verdict.violations["S2"] = [v for k, vs in s2.items()
                                if k not in ("skipped", "skipped_unverified")
                                for v in vs]
    if not run_ws1_gates:
        verdict.skipped.append("S2 rung gates disabled")
    if s2.get("skipped"):
        verdict.skipped.extend(s2["skipped"])
    # Task 4: inputs that could not be runtime-verified stay unverified, so the
    # bundle is INCOMPLETE rather than certified.
    if s2.get("skipped_unverified"):
        verdict.skipped.append(
            "S2 input binding UNVERIFIED: %d input(s) could not be runtime-bound; "
            "result is not certified" % len(s2["skipped_unverified"]))

    if live_result is None:
        verdict.skipped.append("S3")
    else:
        verdict.violations["S3"] = verify_published_vs_live(result, live_result)

    if entries is None:
        verdict.skipped.append("S4")
    else:
        verdict.violations["S4"] = check_publish_eligibility(entries)
    return verdict


# ---------------------------------------------------------------------------
# Task 3 (2026-09-21): publication-state visibility
#
# A board receipt is not a publication. The states below are the five-state
# classification the assignment requires (NO_CLAIM / missing layer /
# INCOMPLETE / rejected / published). Two hard constraints are enforced here:
#
#   * pending / skipped / BLOCKED items are never reported as ``published``
#     or ``verified`` (``PublicationStatus.published`` and ``.verified`` are
#     only True for a referee-verified publication);
#   * a published view must cite *referee* verification evidence
#     (``publication.referee_evidence``), never a submitter-controlled flag.
#     ``publication.status == "published"`` without referee evidence is
#     downgraded to INCOMPLETE, not trusted.
#
# The classification composes the existing S1-S4 pipeline and the board
# artifact (``leaderboard.json`` receipt / publication / trap_rank /
# trap_rank_by_vendor); it does not re-implement any gate.
# ---------------------------------------------------------------------------

PUBLISH_NO_CLAIM = "NO_CLAIM"
PUBLISH_MISSING_LAYER = "MISSING_LAYER"
PUBLISH_INCOMPLETE = "INCOMPLETE"
PUBLISH_REJECTED = "REJECTED"
PUBLISH_PUBLISHED = "PUBLISHED"

#: Human-readable labels for the five states.
PUBLISH_LABELS = {
    PUBLISH_NO_CLAIM: "NO_CLAIM (no publication claim)",
    PUBLISH_MISSING_LAYER: "MISSING_LAYER (unpublishable: a required publication layer is absent)",
    PUBLISH_INCOMPLETE: "INCOMPLETE (claimed but not complete / not released)",
    PUBLISH_REJECTED: "REJECTED (publication refused)",
    PUBLISH_PUBLISHED: "PUBLISHED (referee-verified)",
}


@dataclass
class PublicationStatus:
    """Five-state publication classification for one object.

    ``state`` is one of the ``PUBLISH_*`` constants. ``detail`` explains the
    decision in one line. ``published`` is True only for a referee-verified
    PUBLISHED state; ``verified`` mirrors the referee-evidence check and stays
    False for pending / skipped / submitter-flagged items.
    """

    state: str
    detail: str
    published: bool = False
    verified: bool = False
    evidence: Optional[Dict] = None


def _referee_evidence(pub: Dict) -> Optional[Dict]:
    """Return referee verification evidence, or None when it is not trustworthy.

    A submitter-controlled ``status`` flag is not evidence. Only a dict carrying
    the referee identity, a verification timestamp and an evidence digest counts.
    """
    ev = pub.get("referee_evidence")
    if not isinstance(ev, dict):
        return None
    if not ev.get("referee") or not ev.get("verified_at"):
        return None
    if not ev.get("evidence_sha256"):
        return None
    return ev


def _gate_failures(board: Dict) -> List[str]:
    """Collect board-level gate failures that refuse publication.

    A written board's receipt records the gates that ran at save time; a
    FAIL / INDETERMINATE verdict there means the write was refused (or, for a
    hand-edited artifact, the board must not be treated as publishable). The
    live ``trap_rank`` / ``trap_rank_by_vendor`` blocks are re-read so a stale
    receipt cannot hide a failing gate.
    """
    failures: List[str] = []
    receipt = board.get("receipt")
    if isinstance(receipt, dict):
        gate = receipt.get("gate")
        if isinstance(gate, dict):
            for key, verdict in gate.items():
                if isinstance(verdict, str) and verdict.upper() in ("FAIL", "INDETERMINATE"):
                    failures.append(f"receipt.gate.{key}={verdict}")
    for block_name in ("trap_rank", "trap_rank_by_vendor"):
        block = board.get(block_name)
        if isinstance(block, dict):
            verdict = block.get("verdict")
            if verdict in ("FAIL", "INDETERMINATE"):
                failures.append(f"{block_name}.verdict={verdict}")
    return failures


def board_publication_status(board: Dict, *,
                             board_path: Optional[str | Path] = None) -> PublicationStatus:
    """Five-state publication status for a saved leaderboard.

    ``board_path`` is only used to detect a ``<path>.failed.json`` save-failure
    diagnostic (``leaderboard.save()`` writes one when the gate chain refuses a
    board). Classification order:

    1. REJECTED -- explicit ``publication.status == "rejected"``;
    2. REJECTED -- a ``.failed.json`` diagnostic exists next to the board;
    3. REJECTED -- any gate verdict on the receipt / trap blocks is FAIL or
       INDETERMINATE;
    4. NO_CLAIM -- no ``publication`` block and no ``receipt``: the board makes
       no publishable claim;
    5. PUBLISHED -- ``publication.status == "published"`` **and** referee
       verification evidence is present; otherwise the flag is not trusted and
       the state stays INCOMPLETE (never published);
    6. MISSING_LAYER -- required vendor strata are not fully covered
       (``trap_rank_by_vendor.verdict == MISSING_STRATUM``); the per-group
       claim cannot be certified;
    7. INCOMPLETE -- pending / receipt-without-publication / any other
       unfinished path.
    """
    pub = board.get("publication") if isinstance(board.get("publication"), dict) else {}
    receipt = board.get("receipt")
    status = pub.get("status")

    if isinstance(status, str) and status.lower() == "rejected":
        return PublicationStatus(PUBLISH_REJECTED,
                                 "publication.status is 'rejected'; publication was refused",
                                 published=False, verified=False)

    if board_path is not None:
        failed_path = Path(str(board_path) + ".failed.json")
        if failed_path.is_file():
            try:
                failed = json.loads(failed_path.read_text(encoding="utf-8"))
                n = len(failed.get("gate_violations", []))
            except Exception:  # noqa: BLE001 - unreadable diagnostic is still a refusal record
                n = -1
            return PublicationStatus(
                PUBLISH_REJECTED,
                f"save gate refused this board ({failed_path.name}); "
                f"{n if n >= 0 else 'unreadable'} gate violation(s) recorded",
                published=False, verified=False)

    failures = _gate_failures(board)
    if failures:
        return PublicationStatus(
            PUBLISH_REJECTED,
            "gate failure recorded: " + "; ".join(failures),
            published=False, verified=False)

    if not pub and receipt is None:
        return PublicationStatus(
            PUBLISH_NO_CLAIM,
            "board carries no receipt or publication block; there is no publishable claim",
            published=False, verified=False)

    if isinstance(status, str) and status.lower() == "published":
        evidence = _referee_evidence(pub)
        if evidence is not None:
            return PublicationStatus(
                PUBLISH_PUBLISHED,
                "published with referee-verified evidence",
                published=True, verified=True, evidence=evidence)
        return PublicationStatus(
            PUBLISH_INCOMPLETE,
            "publication.status says 'published' but no referee-verified evidence is "
            "attached; a submitter-controlled flag is not verification, so this is NOT "
            "treated as published",
            published=False, verified=False)

    strata = board.get("trap_rank_by_vendor")
    if isinstance(strata, dict) and strata.get("verdict") == "MISSING_STRATUM":
        missing = strata.get("missing_strata") or []
        return PublicationStatus(
            PUBLISH_MISSING_LAYER,
            "missing required publication layer: required vendor strata not fully "
            "covered (trap_rank_by_vendor.verdict=MISSING_STRATUM; uncovered: %s); "
            "per-group claim cannot be certified" % (", ".join(missing) or "not recorded"),
            published=False, verified=False)

    if status is None:
        return PublicationStatus(
            PUBLISH_INCOMPLETE,
            "receipt exists but publication block is missing/empty; release status "
            "is undefined (a receipt is not a publication)",
            published=False, verified=False)

    return PublicationStatus(
        PUBLISH_INCOMPLETE,
        f"publication.status='{status}'; not released (a receipt is not a publication)",
        published=False, verified=False)


def verdict_publication_status(verdict: Verdict) -> PublicationStatus:
    """Five-state publication status for a verified RunBundle.

    Maps an S1-S4 ``Verdict`` onto the same five states. A bundle that passed
    every required stage is *publishable*, not *published*: publication requires
    a board save and referee evidence, so the state stays INCOMPLETE with an
    explicit 'not released' detail.
    """
    if not any(verdict.violations.values()) and verdict.skipped:
        return PublicationStatus(
            PUBLISH_INCOMPLETE,
            "claimed but incomplete: stage(s) skipped -> "
            + ", ".join(verdict.skipped),
            published=False, verified=False)
    if any(verdict.violations.values()):
        return PublicationStatus(
            PUBLISH_REJECTED,
            "rejected: " + ", ".join(
                f"{s}: {len(v)} violation(s)" for s, v in verdict.violations.items() if v),
            published=False, verified=False)
    return PublicationStatus(
        PUBLISH_INCOMPLETE,
        "verification passed (S1-S4) but not published; publication requires a "
        "board save and referee verification evidence",
        published=False, verified=False)


def entry_publication_status(entry: Dict, *,
                             board_state: Optional[PublicationStatus] = None) -> PublicationStatus:
    """Five-state publication status for one leaderboard entry.

    Traps and placeholders are not publication objects and are reported as
    NO_CLAIM with an explanatory detail (they never become PUBLISHED). A real
    submission inherits the board state: publishing happens at board level and
    an entry cannot be 'published' on a board whose own state is not PUBLISHED.
    """
    if entry.get("trap"):
        return PublicationStatus(
            PUBLISH_NO_CLAIM, "permanent control trap; not a publication object",
            published=False, verified=False)
    if entry.get("placeholder"):
        return PublicationStatus(
            PUBLISH_NO_CLAIM, "placeholder entry; not a publication object",
            published=False, verified=False)
    if board_state is None:
        return PublicationStatus(
            PUBLISH_NO_CLAIM, "no board state supplied; cannot certify this entry",
            published=False, verified=False)
    return PublicationStatus(board_state.state, board_state.detail,
                             published=board_state.published,
                             verified=board_state.verified,
                             evidence=board_state.evidence)
