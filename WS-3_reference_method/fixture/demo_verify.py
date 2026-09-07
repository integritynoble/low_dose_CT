#!/usr/bin/env python3
"""H1a/H8a demonstration: an artifact-verification run that accepts the valid synthetic package and
rejects deliberately corrupted copies for named reasons, and writes an evidence packet.

    python demo_verify.py <out_dir> [--seed 42] [--host-alias NAME] [--packet PATH]

What it does, in order:

  1. builds ONE valid synthetic corpus at <out_dir>/valid with make_synthetic_corpus (RNG pixels, RNG
     scores; NOT scientific data);
  2. runs every deposit verifier on it: completeness, integrity (MANIFEST.sha256), error-map construction,
     credential audit, metadata consistency against disk, metadata schema;
  3. makes one disposable copy per corruption case under <out_dir>/cases/<case>/, corrupts ONLY the copy,
     re-runs the same verifiers, and compares the decision with the one fixed in advance;
  4. proves the valid corpus is byte-identical after all cases ran;
  5. writes an evidence packet (JSON) in the minimum R1-compatible envelope of the September plan.

Execution status, artifact-check result and claim decision are kept separate: a verifier that cannot run
yields UNVERIFIED, never REJECT and never ACCEPT. A check that silently did not execute (for example the
schema check when jsonschema is absent) is reported as not executed and blocks ACCEPT.

No LLM, no model, no network, no GPU, no patient data. Exit 0 only when every case decided as expected.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "corpus_emit"))
sys.path.insert(0, str(_HERE.parent / "deposit"))

from make_synthetic_corpus import SCHEMA, SEED_METADATA, build_synthetic_corpus, write_nifti  # noqa: E402
from emit_credentials import verify_corpus_credentials  # noqa: E402
import package_corpus as pkg  # noqa: E402

REDUCED_FILES = ("recon_mean.nii.gz", "uncertainty_sigma.nii.gz", "error_abs.nii.gz",
                 "task_nodule_score.nii.gz", "scan_meta.json")
REFERENCE_FILES = ("recon_mean.nii.gz", "scan_meta.json")
TOP_FILES = ("MANIFEST.sha256", "dataset_metadata.json", "credentials/all_credentials.jsonl")

ACCEPT, REJECT, UNVERIFIED = "ACCEPT", "REJECT", "UNVERIFIED"


# --------------------------------------------------------------------------- #
# the verifier bundle
# --------------------------------------------------------------------------- #
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_completeness(root: Path) -> dict[str, Any]:
    """Every record folder carries the files its dose level requires, and the top-level artifacts exist."""
    missing: list[str] = []
    for f in TOP_FILES:
        if not (root / f).exists():
            missing.append(f)
    for d in sorted(p for p in root.glob("reconstructions/*/*/r*") if p.is_dir()):
        need = REFERENCE_FILES if d.name == "r100" else REDUCED_FILES
        for f in need:
            if not (d / f).exists():
                missing.append((d / f).relative_to(root).as_posix())
    return {"ok": not missing, "missing": missing}


def check_metadata_consistency(root: Path) -> dict[str, Any]:
    """The counts written into dataset_metadata.json equal the counts derivable from disk right now."""
    md = json.loads((root / "dataset_metadata.json").read_text(encoding="utf-8"))
    fresh = pkg.fill_metadata(json.loads(Path(SEED_METADATA).read_text(encoding="utf-8")), root)
    mismatches: list[str] = []
    for key in ("n_scans", "n_patients", "n_records_total"):
        if md.get("counts", {}).get(key) != fresh["counts"].get(key):
            mismatches.append(f"counts.{key}: metadata says {md.get('counts', {}).get(key)!r}, disk holds {fresh['counts'].get(key)!r}")
    on_file = {rt["type"]: rt.get("count") for rt in md.get("record_types", [])}
    on_disk = {rt["type"]: rt.get("count") for rt in fresh.get("record_types", [])}
    for t in sorted(set(on_file) | set(on_disk)):
        if on_file.get(t) != on_disk.get(t):
            mismatches.append(f"record_types[{t}].count: metadata says {on_file.get(t)!r}, disk holds {on_disk.get(t)!r}")
    return {"ok": not mismatches, "mismatches": mismatches}


def check_schema(root: Path) -> dict[str, Any]:
    """Metadata schema validation, with an explicit statement of whether the validator actually ran."""
    if importlib.util.find_spec("jsonschema") is None:
        return {"ok": None, "executed": False, "errors": [],
                "note": "jsonschema is not importable; package_corpus would silently report no errors"}
    md = json.loads((root / "dataset_metadata.json").read_text(encoding="utf-8"))
    errors = pkg._validate_against_schema(md, Path(SCHEMA))
    return {"ok": not errors, "executed": True, "errors": errors}


def _run_check(name: str, fn, root: Path) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        out = fn(root)
        status = "completed"
    except Exception as exc:  # execution error is a distinct outcome, kept with its reason
        out = {"ok": None, "error": f"{type(exc).__name__}: {exc}"}
        status = "error"
    out = dict(out)
    out.update({"check": name, "status": status, "seconds": round(time.perf_counter() - t0, 4)})
    if "executed" not in out:
        out["executed"] = status == "completed"
    return out


def verify_bundle(root: Path) -> dict[str, Any]:
    """Run every verifier; decide ACCEPT / REJECT / UNVERIFIED with the reasons that produced it."""
    root = Path(root)
    checks = [
        _run_check("completeness", check_completeness, root),
        _run_check("integrity", pkg.verify_manifest, root),
        _run_check("error_maps", pkg.verify_error_maps, root),
        _run_check("credentials", verify_corpus_credentials, root),
        _run_check("metadata_consistency", check_metadata_consistency, root),
        _run_check("schema", check_schema, root),
    ]
    reasons: list[str] = []
    not_executed: list[str] = []
    for c in checks:
        if c["status"] != "completed" or not c.get("executed", True):
            not_executed.append(f"{c['check']}: {c.get('error') or c.get('note') or 'not executed'}")
            continue
        if c["ok"]:
            continue
        n = c["check"]
        if n == "completeness":
            reasons += [f"completeness: missing {m}" for m in c["missing"]]
        elif n == "integrity":
            reasons += [f"integrity: bytes differ from MANIFEST.sha256 for {m}" for m in c["mismatched"]]
            reasons += [f"integrity: listed in MANIFEST.sha256 but absent: {m}" for m in c["missing"]]
            reasons += [f"integrity: on disk but not in MANIFEST.sha256: {m}" for m in c["untracked"]]
        elif n == "error_maps":
            reasons += [f"error_maps: {f['record']} is not |recon - reference| ({f.get('reason') or ('max deviation %.3g' % f['max_abs_dev'])})" for f in c["failures"]]
        elif n == "credentials":
            reasons += [f"credentials: {f['path']}: {'; '.join(f['issues'])}" for f in c["failures"]]
        elif n == "metadata_consistency":
            reasons += [f"metadata: {m}" for m in c["mismatches"]]
        elif n == "schema":
            reasons += [f"schema: {e}" for e in c["errors"]]
    if not_executed:
        decision = UNVERIFIED
    elif reasons:
        decision = REJECT
    else:
        decision = ACCEPT
    return {"decision": decision, "reasons": reasons, "not_executed": not_executed, "checks": checks}


# --------------------------------------------------------------------------- #
# the corruption cases: each acts on a disposable copy and never on the valid corpus
# --------------------------------------------------------------------------- #
def _first(root: Path, pattern: str) -> Path:
    return sorted(root.glob(pattern))[0]


def corrupt_missing_file(copy: Path) -> str:
    victim = _first(copy, "reconstructions/*/*/r025/task_nodule_score.nii.gz")
    victim.unlink()
    return victim.relative_to(copy).as_posix()


def corrupt_tampered_bytes(copy: Path) -> str:
    victim = _first(copy, "reconstructions/*/*/r010/recon_mean.nii.gz")
    write_nifti(victim, np.full((8, 8, 2), 123.0, dtype="f4"))
    return victim.relative_to(copy).as_posix()


def corrupt_metadata_counts(copy: Path) -> str:
    md_path = copy / "dataset_metadata.json"
    md = json.loads(md_path.read_text(encoding="utf-8"))
    md["counts"]["n_scans"] = 9
    md_path.write_text(json.dumps(md, indent=2), encoding="utf-8")
    pkg.write_manifest(copy)          # the manifest is rebuilt, so only the consistency check can catch it
    return "dataset_metadata.json: counts.n_scans -> 9, manifest rebuilt"


def corrupt_credential_verdict(copy: Path) -> str:
    victim = _first(copy, "credentials/lung_nodule_5mm/r025/pwm_ref_v1__*.json")
    payload = json.loads(victim.read_text(encoding="utf-8"))
    cred = payload["credential"]
    cred["verdict"] = "FAIL" if cred["verdict"] == "PASS" else "PASS"
    victim.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pkg.write_manifest(copy)
    return victim.relative_to(copy).as_posix() + f": verdict -> {cred['verdict']}, manifest rebuilt"


def corrupt_error_map(copy: Path) -> str:
    victim = _first(copy, "reconstructions/*/*/r025/error_abs.nii.gz")
    write_nifti(victim, np.full((8, 8, 2), 99.0, dtype="f4"))
    pkg.write_manifest(copy)
    return victim.relative_to(copy).as_posix() + ": constant map, manifest rebuilt"


def corrupt_manifest_missing(copy: Path) -> str:
    (copy / "MANIFEST.sha256").unlink()
    return "MANIFEST.sha256 deleted"


CASES: list[tuple[str, str, Any, str]] = [
    # id, description, corruption, expected decision
    ("D01", "valid synthetic package, claims limited to the pipeline", None, ACCEPT),
    ("D02", "second valid package with its own seed", "reseed", ACCEPT),
    ("D03", "required file missing", corrupt_missing_file, REJECT),
    ("D04", "artifact bytes no longer match the manifest", corrupt_tampered_bytes, REJECT),
    ("D05", "metadata counts disagree with the records on disk", corrupt_metadata_counts, REJECT),
    ("D06", "credential verdict contradicts its own interval", corrupt_credential_verdict, REJECT),
    ("D07", "released error map is not |recon - reference|", corrupt_error_map, REJECT),
    ("D08", "integrity manifest absent, so the integrity verifier cannot execute", corrupt_manifest_missing, UNVERIFIED),
]


# --------------------------------------------------------------------------- #
# provenance for the evidence packet
# --------------------------------------------------------------------------- #
def _git(args: list[str], cwd: Path) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def source_identity() -> dict[str, Any]:
    top = _git(["rev-parse", "--show-toplevel"], _HERE)
    if not top:
        return {"commit": None, "dirty": None, "note": "not inside a git checkout"}
    commit = _git(["rev-parse", "HEAD"], Path(top))
    diff = _git(["diff", "HEAD", "--", "WS-3_reference_method", "WS-2_framework"], Path(top)) or ""
    untracked = _git(["ls-files", "--others", "--exclude-standard", "WS-3_reference_method", "WS-2_framework"], Path(top)) or ""
    dirty = bool(diff.strip() or untracked.strip())
    return {"commit": commit, "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"], Path(top)), "dirty": dirty,
            "dirty_diff_sha256": hashlib.sha256((diff + "\n" + untracked).encode()).hexdigest() if dirty else None,
            "untracked_in_scope": untracked.splitlines()}


def runtime_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {"python": platform.python_version(), "platform": platform.platform()}
    from importlib.metadata import PackageNotFoundError, version
    for mod in ("numpy", "scipy", "nibabel", "jsonschema", "pwm_dose_equivalence"):
        try:
            out[mod] = version(mod)
        except PackageNotFoundError:
            out[mod] = None
    return out


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
def run_demo(out_dir: Path, seed: int = 42, host_alias: str | None = None, log=print) -> dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"refusing to write into a non-empty directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t_all = time.perf_counter()
    run_id = f"ldct-h1a-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"

    valid = out_dir / "valid"
    build_report = build_synthetic_corpus(valid, seed=seed)
    valid_manifest_hash = _sha256(valid / "MANIFEST.sha256")

    results: list[dict[str, Any]] = []
    for case_id, desc, corruption, expected in CASES:
        t0 = time.perf_counter()
        if corruption is None:
            target = valid
            applied = "none"
        elif corruption == "reseed":
            target = out_dir / "cases" / case_id
            build_synthetic_corpus(target, seed=seed + 1)
            applied = f"fresh build at seed {seed + 1}"
        else:
            target = out_dir / "cases" / case_id
            shutil.copytree(valid, target)
            applied = corruption(target)
        verdict = verify_bundle(target)
        results.append({"case": case_id, "description": desc, "target": str(target), "corruption": applied,
                        "expected": expected, "observed": verdict["decision"], "as_expected": verdict["decision"] == expected,
                        "reasons": verdict["reasons"], "not_executed": verdict["not_executed"],
                        "checks": verdict["checks"], "seconds": round(time.perf_counter() - t0, 3)})
        log(f"{case_id} {verdict['decision']:10} expected {expected:10} {'ok ' if verdict['decision'] == expected else 'MISMATCH'} {desc}")
        for r in verdict["reasons"][:3]:
            log(f"      {r}")
        for r in verdict["not_executed"]:
            log(f"      not executed: {r}")

    # the valid corpus must be untouched by everything above
    valid_after = verify_bundle(valid)
    untouched = _sha256(valid / "MANIFEST.sha256") == valid_manifest_hash and valid_after["decision"] == ACCEPT

    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    completed = [r for r in results if r["observed"] in (ACCEPT, REJECT, UNVERIFIED)]
    admissible = [r for r in results if r["observed"] in (ACCEPT, REJECT)]
    all_ok = all(r["as_expected"] for r in results) and untouched
    packet = {
        "packet_version": "ldct-h1a-evidence/0.1 (minimum R1-compatible envelope; not the full cross-consumer R1 contract)",
        "run_id": run_id, "started_utc": started, "finished_utc": finished,
        "host_alias": host_alias or socket.gethostname(),
        "source": source_identity(),
        "script_sha256": _sha256(Path(__file__)),
        "agent": {"identity": "deterministic verification script; no LLM, no model, no harness",
                  "backend": None, "model_digest": None, "human_interventions": 0},
        "runtime": runtime_versions(),
        "data": {"designation": "synthetic", "detail": f"RNG pixels and RNG scores at seed {seed}; no patient data, no restricted data",
                 "use_scope": "public engineering demonstration of the deposit verifiers",
                 "input_hashes": {"seed_metadata": _sha256(Path(SEED_METADATA)), "metadata_schema": _sha256(Path(SCHEMA))},
                 "build_report": build_report},
        "cases": {"requested": len(CASES), "completed": len(completed), "with_admissible_verdict": len(admissible),
                  "as_expected": sum(r["as_expected"] for r in results), "attempts_per_case": 1,
                  "failures_or_timeouts": [r["case"] for r in results if r["observed"] == UNVERIFIED and r["expected"] != UNVERIFIED],
                  "results": results},
        "valid_corpus_untouched_after_all_cases": untouched,
        "resources": {"wall_seconds": round(time.perf_counter() - t_all, 3), "gpu_seconds": 0, "tokens": "not applicable",
                      "cost_status": "none: local CPU, no paid calls"},
        "outputs": {"valid_manifest_sha256": valid_manifest_hash, "out_dir": str(out_dir)},
        "acceptance_verdict": "PASS" if all_ok else "FAIL",
        "limitations": [
            "No reconstruction ran and no image quality number was computed; this exercises the deposit verifiers, not the method.",
            "Inputs are synthetic; nothing here is a clinical or scientific result.",
            "The decisions are about a package's structural claims (completeness, integrity, construction, consistency); they are not claims about any method's performance.",
            "An UNVERIFIED case is an execution outcome, not a refusal of a scientific claim.",
            "One seed, eight cases: an engineering pilot, not a reliability estimate.",
        ],
        "supersedes": None,
        "public_export_allowlist": ["evidence packet JSON", "DEMO_RUN_GUIDE.md", "the synthetic corpus itself (RNG content)"],
    }
    return packet


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out_dir", type=Path, help="new or empty directory")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--host-alias", default=None, help="alias to record instead of the hostname")
    ap.add_argument("--packet", type=Path, default=None, help="where to write the evidence packet (default <out_dir>/evidence_packet.json)")
    a = ap.parse_args(argv)
    packet = run_demo(a.out_dir, seed=a.seed, host_alias=a.host_alias)
    dest = a.packet or (a.out_dir / "evidence_packet.json")
    dest.write_text(json.dumps(packet, indent=1), encoding="utf-8")
    c = packet["cases"]
    print(f"\nrequested {c['requested']}  completed {c['completed']}  admissible {c['with_admissible_verdict']}  as expected {c['as_expected']}"
          f"  valid corpus untouched: {packet['valid_corpus_untouched_after_all_cases']}  verdict: {packet['acceptance_verdict']}")
    print(f"packet: {dest}  sha256 {_sha256(dest)}")
    return 0 if packet["acceptance_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
