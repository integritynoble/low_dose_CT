"""Task 4 (2026-09-21): byte/hash-level binding of the inputs actually evaluated.

Trust boundary
--------------
A submitted result JSON can claim any manifest / weights hashes it likes. A hash
of a submitted object (``provenance_sha256``) proves *internal consistency of
that JSON*, not that those bytes were evaluated. Likewise, one ``patient_id``
somewhere in JSON does not establish slice-to-patient mapping. This module adds
evaluator-owned evidence by binding the three input classes to **runtime-computed
facts**:

1. **model bytes** -- SHA-256 computed with ``hashlib`` over the actual
   checkpoint file bytes, cross-checked against the ASSET_MANIFEST entry and
   against the claim's declared *file* hash. A JSON that names model A while the
   file bytes belong to model B is rejected. The pre-existing
   ``claim.model_sha256`` remains the canonical-JSON hash of
   ``evidence.model_weights`` (internal consistency); the *new* optional field
   ``claim.model_file_sha256`` declares the file-byte hash, and the runtime file
   hash is always cross-checked against the ASSET_MANIFEST listing.
2. **asset manifest** -- the ASSET_MANIFEST (or a ``hashes/`` listing) is parsed
   and the claimed model must be a member; an entry whose SHA256 is a
   placeholder / empty is marked UNVERIFIED, never invented or filled in.
3. **patient mapping** -- slice/result ``patient_id`` values are bound to a
   fixed split source (``splits/split_assignment.csv`` + ``splits/aapm_*.txt``).
   A claimed patient bootstrap with no binding source is NO_BINDING
   (UNVERIFIED); a patient_id absent from the fixed source is inconsistent and
   rejected. Self-reported patient maps inside the JSON are decoration, never a
   binding source.

Every check falls into one of three states:

* ``PASS``        -- runtime fact available and consistent (``ok`` True)
* ``UNVERIFIED``  -- no runtime fact available (missing file / source /
                     placeholder hash): the result stays unverified / pending,
                     it is never certified
* ``FAIL``        -- runtime fact contradicts the claim (``violations``)

Nothing in this module writes files, changes scores/tolerances/registry, or
certifies anything. It only computes evidence and reports states.
"""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

#: Three-state binding verdicts.
BIND_PASS = "PASS"
BIND_UNVERIFIED = "UNVERIFIED"
BIND_FAIL = "FAIL"

#: Regex for a 64-char uppercase/lowercase SHA-256.
_HEX64 = re.compile(r"\b[0-9a-fA-F]{64}\b")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

#: Default probe locations, resolved only when the caller does not pass one.
_DEFAULT_MANIFEST = _REPO_ROOT / "WS-1_dataset" / "R6_recalc" / "ASSET_MANIFEST.md"
_DEFAULT_CHECKPOINT_DIR = _REPO_ROOT / "WS-1_dataset" / "baselines" / "checkpoints"
_DEFAULT_SPLITS_DIR = _REPO_ROOT / "WS-1_dataset" / "splits"


def _clean_hash(value: Any) -> Optional[str]:
    """Normalise a SHA-256 string to uppercase without whitespace; None if empty."""
    if not isinstance(value, str):
        return None
    h = value.strip()
    if not h or h in ("-", "TBD", "TODO", "PLACEHOLDER", "N/A", "NA"):
        return None
    return h.upper()


def sha256_file(path: str | Path) -> str:
    """SHA-256 of the actual file bytes (runtime-computed, not self-reported)."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


# ---------------------------------------------------------------------------
# ASSET_MANIFEST parsing
# ---------------------------------------------------------------------------

def parse_asset_manifest(path: str | Path) -> Dict[str, Optional[str]]:
    """Parse an ASSET_MANIFEST.md A1-style table or a ``hashes/`` listing.

    Returns ``{filename: sha256_or_None}``. A table cell that is empty, ``-`` or
    a placeholder yields ``None`` so the caller can mark it UNVERIFIED instead of
    inventing a hash. The A1 table row format is
    ``| `name.pt` | size | source path | `HASH` |``; the hashes listing format is
    ``HASH  <path>`` (``ckpt_hashes.txt`` style) or ``name=HASH``.
    """
    out: Dict[str, Optional[str]] = {}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out

    # 1) A1 table rows: | `name` | size | source | `HASH` |
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        name_cell = cells[0].strip("`").strip()
        hash_cell = cells[3].strip("`").strip()
        if not name_cell or not _looks_like_asset_name(name_cell):
            continue
        out[name_cell] = _clean_hash(hash_cell)

    # 2) key-value / "HASH  path" listing lines (ckpt_hashes.txt style).
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("|"):
            continue
        m = _HEX64.search(line)
        if m:
            h = m.group(0).upper()
            rest = (line[: m.start()] + " " + line[m.end():]).strip()
            name = None
            if "=" in rest:
                name = rest.split("=", 1)[0].strip()
            elif " " in rest:
                name = Path(rest.split(" ", 1)[1].strip()).name
            elif rest:
                name = rest
            if name:
                out[name] = h
        elif "=" in line:
            name, h = line.split("=", 1)
            out[name.strip()] = _clean_hash(h)
    return out


def _looks_like_asset_name(name: str) -> bool:
    """Heuristic: A1 rows carry a filename-like first cell, not a section label."""
    return "." in name or name.lower().endswith((".pt", ".pth", ".ckpt", ".zip", ".tar"))


# ---------------------------------------------------------------------------
# Model bytes
# ---------------------------------------------------------------------------

def _model_reference(claim: Dict, evidence: Dict) -> Optional[str]:
    """Extract the concrete checkpoint reference from claim/evidence.

    Resolution order: ``claim.model_file`` (explicit), then
    ``evidence.model_weights.checkpoint``, then ``evidence.model_weights.name``.
    Returns a filename or path; None when nothing concrete is referenced.
    """
    ref = claim.get("model_file")
    if isinstance(ref, str) and ref.strip():
        return ref.strip()
    weights = evidence.get("model_weights")
    if isinstance(weights, dict):
        ref = weights.get("checkpoint")
        if isinstance(ref, str) and ref.strip():
            return ref.strip()
        ref = weights.get("name")
        if isinstance(ref, str) and ref.strip():
            return ref.strip()
    return None


def _candidate_checkpoint_paths(name: str, *,
                                bundle_dir: Optional[str | Path],
                                checkpoint_dir: Optional[str | Path]) -> List[Path]:
    """Candidate file locations for a checkpoint name.

    The name itself may be a bare filename or a path; we only ever read files the
    caller has placed in the bundle / checkpoint dirs (no arbitrary traversal
    into other directories when resolving a bare name).
    """
    p = Path(name)
    candidates: List[Path] = []
    if p.is_absolute():
        candidates.append(p)
    else:
        if bundle_dir:
            candidates.append(Path(bundle_dir) / p)
        if checkpoint_dir:
            candidates.append(Path(checkpoint_dir) / p)
    return candidates


def check_model_bytes(claim: Dict, evidence: Dict, *,
                      bundle_dir: Optional[str | Path] = None,
                      checkpoint_dir: Optional[str | Path] = None,
                      manifest: Optional[Dict[str, Optional[str]]] = None,
                      method_name: Optional[str] = None) -> Tuple[str, List[str], List[str], str]:
    """Bind the evaluated model to runtime checkpoint bytes.

    Returns ``(status, violations, unverified, detail)``.
    """
    ref = _model_reference(claim, evidence)
    if not ref:
        return (BIND_UNVERIFIED, [],
                ["claim/evidence does not reference a concrete checkpoint file "
                 "(model bytes cannot be bound)"],
                "model_bytes: NO_REFERENCE")
    name = Path(ref).name
    declared_file_hash = _clean_hash(claim.get("model_file_sha256"))

    # Asset-manifest membership.
    membership_unverified: List[str] = []
    declared_manifest_hash: Optional[str] = None
    if manifest is None:
        membership_unverified.append(
            "ASSET_MANIFEST not available; model membership cannot be cross-checked")
    elif name not in manifest:
        return (BIND_FAIL,
                ["model %r is not a member of ASSET_MANIFEST (changed manifest "
                 "membership: the claim names a checkpoint the manifest does not "
                 "list)" % name],
                [],
                "model_bytes: NOT_IN_MANIFEST")
    else:
        declared_manifest_hash = manifest.get(name)
        if not declared_manifest_hash:
            membership_unverified.append(
                "ASSET_MANIFEST entry %r has no SHA256 (placeholder); the runtime "
                "file hash cannot be cross-checked against the manifest" % name)

    # Runtime byte hash.
    candidates = _candidate_checkpoint_paths(ref, bundle_dir=bundle_dir,
                                             checkpoint_dir=checkpoint_dir)
    file_path = next((p for p in candidates if p.is_file()), None)
    if file_path is None:
        return (BIND_UNVERIFIED, [], membership_unverified + [
            "checkpoint file for %r not found in bundle/checkpoint dirs; byte "
            "hash not computed (runtime fact unavailable)" % name],
            "model_bytes: FILE_MISSING")
    try:
        actual = sha256_file(file_path)
    except OSError as exc:  # pragma: no cover - defensive
        return (BIND_UNVERIFIED, [], membership_unverified + [
            "checkpoint file for %r could not be read: %s" % (name, exc)],
            "model_bytes: READ_FAILED")

    # Cross-checks against runtime fact.
    if declared_manifest_hash and actual != declared_manifest_hash:
        return (BIND_FAIL,
                ["model bytes changed: %r SHA256 %s... != ASSET_MANIFEST %s... "
                 "(the file bytes actually present are not the manifest's "
                 "checkpoint)" % (name, actual[:12], declared_manifest_hash[:12])],
                [],
                "model_bytes: MANIFEST_MISMATCH")
    if declared_file_hash and actual != declared_file_hash:
        return (BIND_FAIL,
                ["claim.model_file_sha256 does not match the actual checkpoint "
                 "bytes: %r is %s... not %s... (JSON claimed a different file)"
                 % (name, actual[:12], declared_file_hash[:12])],
                [],
                "model_bytes: CLAIM_MISMATCH")

    detail = "model_bytes: BOUND %r SHA256 %s..." % (name, actual[:12])
    if method_name and name != method_name:
        detail += " (method label %r differs from checkpoint name)" % method_name
    if membership_unverified:
        return (BIND_UNVERIFIED, [], membership_unverified, detail)
    return (BIND_PASS, [], [], detail)


def check_asset_manifest_binding(claim: Dict, evidence: Dict, *,
                                 manifest: Optional[Dict[str, Optional[str]]] = None,
                                 manifest_path: Optional[str | Path] = None) -> Tuple[str, List[str], List[str], str]:
    """Cross-check claimed model identity against the asset manifest listing.

    A claim must reference a checkpoint the manifest actually lists; a manifest
    entry whose SHA256 is a placeholder marks the claim UNVERIFIED instead of
    certifying it.
    """
    if manifest is None and manifest_path is not None:
        manifest = parse_asset_manifest(manifest_path)
    ref = _model_reference(claim, evidence)
    if not ref:
        return (BIND_UNVERIFIED, [],
                ["claim/evidence does not reference a concrete checkpoint file; "
                 "asset-manifest membership cannot be bound"],
                "asset_manifest: NO_REFERENCE")
    name = Path(ref).name
    if manifest is None or not manifest:
        return (BIND_UNVERIFIED, [],
                ["ASSET_MANIFEST not available; membership cannot be cross-checked"],
                "asset_manifest: MANIFEST_UNAVAILABLE")
    if name not in manifest:
        return (BIND_FAIL,
                ["asset manifest binding: %r is not listed in ASSET_MANIFEST "
                 "(changed manifest membership)" % name],
                [], "asset_manifest: NOT_IN_MANIFEST")
    h = manifest.get(name)
    if not h:
        return (BIND_UNVERIFIED, [],
                ["ASSET_MANIFEST entry %r has no SHA256 (placeholder); the entry "
                 "cannot be verified, its hash must not be invented" % name],
                "asset_manifest: PLACEHOLDER_HASH")
    return (BIND_PASS, [], [], "asset_manifest: %r listed with SHA256 %s..." % (name, h[:12]))


# ---------------------------------------------------------------------------
# Patient mapping
# ---------------------------------------------------------------------------

def load_split_source(splits_dir: str | Path) -> Dict[str, Dict[str, str]]:
    """Load the fixed split source: ``split_assignment.csv`` -> patient map.

    Returns ``{patient_id: {"split": ..., "source": ..., "seed": ...}}``.
    The CSV header is ``patient_id,native_id,split,source,seed,canonical_key,series_id``.
    """
    out: Dict[str, Dict[str, str]] = {}
    csv_path = Path(splits_dir) / "split_assignment.csv"
    try:
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = (row.get("patient_id") or "").strip()
                if not pid:
                    continue
                out[pid] = {
                    "split": (row.get("split") or "").strip(),
                    "source": (row.get("source") or "").strip(),
                    "seed": (row.get("seed") or "").strip(),
                }
    except OSError:
        return out
    return out


def load_test_set(splits_dir: str | Path) -> Set[str]:
    """Load ``aapm_test.txt`` (one patient_id per line) as the test-set roster."""
    out: Set[str] = set()
    p = Path(splits_dir) / "aapm_test.txt"
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            pid = line.strip()
            if pid:
                out.add(pid)
    except OSError:
        pass
    return out


def _collect_patient_ids(result: Any, found: Set[str]) -> None:
    """Mirror of ``verify._collect_patient_ids`` kept local to avoid import cycles."""
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


def check_patient_mapping_binding(result: Dict, claim: Dict, *,
                                  splits_dir: Optional[str | Path] = None) -> Tuple[str, List[str], List[str], str]:
    """Bind result-level patient ids to a fixed split source.

    A claim that requests patient-level bootstrap must name a fixed source
    (``claim.patient_source`` / ``claim.split_source``) and every result
    patient_id must appear in that source. When no fixed source is available the
    state is NO_BINDING / UNVERIFIED; self-reported maps in JSON are decoration
    and never a binding source, but a self-report that contradicts the fixed
    source is rejected.
    """
    declares_bootstrap = (claim.get("bootstrap_level") == "patient"
                          or claim.get("aggregation") == "patient-level")
    fixed_source = claim.get("patient_source") or claim.get("split_source")
    if not declares_bootstrap:
        return (BIND_UNVERIFIED, [],
                ["claim does not declare patient-level bootstrap; patient mapping "
                 "is NO_BINDING (no fixed source claimed)"],
                "patient_mapping: NO_BINDING_DECLARED")

    pids: Set[str] = set()
    _collect_patient_ids(result, pids)
    if not pids:
        return (BIND_FAIL,
                ["claim requests patient-level bootstrap but the result carries no "
                 "patient_id anywhere; slices of one patient could be counted as "
                 "independent patients"],
                [], "patient_mapping: NO_PATIENT_ID")

    if not fixed_source:
        return (BIND_UNVERIFIED, [],
                ["claim requests patient-level bootstrap but names no fixed "
                 "patient_source/split_source; patient mapping is NO_BINDING (a "
                 "self-reported JSON map is not a binding source)"],
                "patient_mapping: NO_FIXED_SOURCE")
    if splits_dir is None:
        splits_dir = _DEFAULT_SPLITS_DIR
    source = load_split_source(splits_dir)
    if not source:
        return (BIND_UNVERIFIED, [],
                ["fixed split source %r is not readable; patient mapping cannot be "
                 "bound (NO_BINDING)" % str(Path(splits_dir) / "split_assignment.csv")],
                "patient_mapping: SPLIT_SOURCE_UNAVAILABLE")

    missing = sorted(pid for pid in pids if pid not in source)
    if missing:
        return (BIND_FAIL,
                ["patient mapping inconsistent with the fixed split source: "
                 "patient_id(s) not in split_assignment.csv: " + ", ".join(missing)],
                [], "patient_mapping: INCONSISTENT")

    # A self-reported map may decorate the result but must never override the
    # fixed source; a contradiction is evidence of forgery.
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    self_map = claim.get("patient_map")
    if not isinstance(self_map, dict):
        self_map = evidence.get("patient_map") if isinstance(evidence, dict) else None
    if isinstance(self_map, dict):
        for pid, split in self_map.items():
            if pid in source and str(source[pid].get("split")) != str(split):
                return (BIND_FAIL,
                        ["self-reported patient_map contradicts the fixed split "
                         "source for %r (claimed %r, fixed %r)"
                         % (pid, split, source[pid].get("split"))],
                        [], "patient_mapping: SELF_REPORT_CONTRADICTS_SOURCE")

    return (BIND_PASS, [], [],
            "patient_mapping: %d patient_id(s) bound to fixed split source %r"
            % (len(pids), str(Path(splits_dir) / "split_assignment.csv")))


# ---------------------------------------------------------------------------
# Method / task / dose identity binding
# ---------------------------------------------------------------------------

def check_identity_binding(claim: Dict, evidence: Dict, *,
                           method: Optional[str] = None,
                           vendor: Optional[str] = None,
                           dose: Optional[str] = None) -> Tuple[str, List[str], List[str], str]:
    """Bind claim identity fields to the submission context.

    ``task_id`` / ``protocol_id`` remain the job of
    ``verify.check_claim_bound_provenance`` (internal gate); this check binds the
    evaluator-owned *context* (method / vendor / dose) and the evaluator version
    to the claim, refusing contradictions and leaving gaps UNVERIFIED.
    """
    violations: List[str] = []
    unverified: List[str] = []
    details: List[str] = []

    claim_method = claim.get("method_name") or claim.get("method")
    if method:
        if claim_method and str(claim_method) != str(method):
            violations.append("claim names method %r but the submission context is "
                              "%r (wrong method binding)" % (claim_method, method))
        elif not claim_method:
            unverified.append("claim does not declare method_name; method identity "
                              "is not bound to the submission context")
    elif claim_method:
        details.append("method identity declared as %r (no context to bind)" % claim_method)
    else:
        unverified.append("no method context and no claim.method_name; method "
                          "identity is NO_BINDING")

    claim_dose = claim.get("dose") or claim.get("dose_level")
    if dose:
        if claim_dose and str(claim_dose) != str(dose):
            violations.append("claim names dose %r but the submission context is "
                              "%r (wrong dose binding)" % (claim_dose, dose))
        elif not claim_dose:
            unverified.append("claim does not declare dose; dose identity is not "
                              "bound to the submission context")
    elif claim_dose:
        details.append("dose identity declared as %r (no context to bind)" % claim_dose)
    else:
        unverified.append("no dose context and no claim.dose; dose identity is "
                          "NO_BINDING")

    claim_vendor = claim.get("vendor")
    if vendor:
        if claim_vendor and str(claim_vendor) != str(vendor):
            violations.append("claim names vendor %r but the submission context is "
                              "%r (wrong vendor binding)" % (claim_vendor, vendor))
        elif not claim_vendor:
            unverified.append("claim does not declare vendor; vendor identity is "
                              "not bound to the submission context")
    elif claim_vendor:
        details.append("vendor identity declared as %r (no context to bind)" % claim_vendor)
    else:
        unverified.append("no vendor context and no claim.vendor; vendor identity "
                          "is NO_BINDING")

    ev_claim = claim.get("evaluator_version")
    ev_evidence = evidence.get("evaluator_version") if isinstance(evidence, dict) else None
    if ev_claim:
        if not ev_evidence:
            unverified.append("claim declares evaluator_version but evidence has "
                              "none (evaluator-owned version missing; result stays "
                              "UNVERIFIED, not rejected)")
        elif str(ev_claim) != str(ev_evidence):
            violations.append("claim.evaluator_version %r differs from "
                              "evidence.evaluator_version %r"
                              % (ev_claim, ev_evidence))
    else:
        unverified.append("claim does not declare evaluator_version")

    if violations:
        return (BIND_FAIL, violations, [], "; ".join(details) or "identity: FAIL")
    if unverified:
        return (BIND_UNVERIFIED, [], unverified, "; ".join(details) or "identity: UNVERIFIED")
    return (BIND_PASS, [], [], "; ".join(details) or "identity: BOUND")


# ---------------------------------------------------------------------------
# Combined entry point
# ---------------------------------------------------------------------------

@dataclass
class BindingResult:
    """Aggregate three-state result of the input-binding checks.

    ``ok`` is True only when there are no violations; it says nothing about
    verification, so an UNVERIFIED result with no violations still has ``ok``
    True but **must not be certified** (the caller reads ``unverified``).
    """

    checks: Dict[str, str] = field(default_factory=dict)   # check -> PASS/UNVERIFIED/FAIL
    details: Dict[str, str] = field(default_factory=dict)  # check -> detail line
    violations: List[str] = field(default_factory=list)    # FAIL lines (hard rejection)
    unverified: List[str] = field(default_factory=list)    # UNVERIFIED lines (not certified)

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def status(self) -> str:
        if self.violations:
            return BIND_FAIL
        if self.unverified:
            return BIND_UNVERIFIED
        return BIND_PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "ok": self.ok,
            "checks": dict(self.checks),
            "details": dict(self.details),
            "violations": list(self.violations),
            "unverified": list(self.unverified),
        }


def _default_manifest() -> Optional[Dict[str, Optional[str]]]:
    manifest_path = _DEFAULT_MANIFEST
    if manifest_path.is_file():
        return parse_asset_manifest(manifest_path)
    listing = _DEFAULT_MANIFEST.parent / "hashes" / "ckpt_hashes.txt"
    if listing.is_file():
        return parse_asset_manifest(listing)
    return None


def check_input_binding(result: Dict, *,
                        method: Optional[str] = None,
                        vendor: Optional[str] = None,
                        dose: Optional[str] = None,
                        bundle_dir: Optional[str | Path] = None,
                        checkpoint_dir: Optional[str | Path] = None,
                        manifest_path: Optional[str | Path] = None,
                        splits_dir: Optional[str | Path] = None) -> BindingResult:
    """Run all three input-binding classes plus identity binding on one result.

    Every fact is runtime-computed (file bytes, parsed manifest, parsed split
    source). Nothing trusts a self-reported hash on its own; self-reported values
    are only ever cross-checked *against* runtime facts.
    """
    claim = result.get("claim") if isinstance(result.get("claim"), dict) else {}
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}

    manifest: Optional[Dict[str, Optional[str]]] = None
    if manifest_path is not None:
        if Path(manifest_path).is_file():
            manifest = parse_asset_manifest(manifest_path)
    else:
        manifest = _default_manifest()

    if checkpoint_dir is None and _DEFAULT_CHECKPOINT_DIR.is_dir():
        checkpoint_dir = _DEFAULT_CHECKPOINT_DIR
    if splits_dir is None and _DEFAULT_SPLITS_DIR.is_dir():
        splits_dir = _DEFAULT_SPLITS_DIR

    out = BindingResult()
    model_status, model_viol, model_unv, model_detail = check_model_bytes(
        claim, evidence, bundle_dir=bundle_dir, checkpoint_dir=checkpoint_dir,
        manifest=manifest, method_name=method)
    out.checks["model_bytes"] = model_status
    out.details["model_bytes"] = model_detail
    out.violations += ["model_bytes: " + v for v in model_viol]
    out.unverified += ["model_bytes: " + v for v in model_unv]

    am_status, am_viol, am_unv, am_detail = check_asset_manifest_binding(
        claim, evidence, manifest=manifest)
    out.checks["asset_manifest"] = am_status
    out.details["asset_manifest"] = am_detail
    out.violations += ["asset_manifest: " + v for v in am_viol]
    out.unverified += ["asset_manifest: " + v for v in am_unv]

    pm_status, pm_viol, pm_unv, pm_detail = check_patient_mapping_binding(
        result, claim, splits_dir=splits_dir)
    out.checks["patient_mapping"] = pm_status
    out.details["patient_mapping"] = pm_detail
    out.violations += ["patient_mapping: " + v for v in pm_viol]
    out.unverified += ["patient_mapping: " + v for v in pm_unv]

    id_status, id_viol, id_unv, id_detail = check_identity_binding(
        claim, evidence, method=method, vendor=vendor, dose=dose)
    out.checks["identity"] = id_status
    out.details["identity"] = id_detail
    out.violations += ["identity: " + v for v in id_viol]
    out.unverified += ["identity: " + v for v in id_unv]
    return out
