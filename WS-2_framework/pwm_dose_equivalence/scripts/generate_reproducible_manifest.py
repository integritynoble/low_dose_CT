#!/usr/bin/env python3
"""Generate the reproducible-artifact manifest for pwm_dose_equivalence.

P3-4: publish the 140-test matrix + 5-tuple credential artifacts as a
content-addressed manifest (SHA-256 per artifact), aligned with WS-1's
content-addressed manifest discipline, so an independent verifier can recompute
every claim from the committed files alone.

Regenerate with:
    python scripts/generate_reproducible_manifest.py

Drift protection: tests/test_reproducible_manifest.py re-runs this generator and
fails CI if the committed manifest no longer matches the current tree.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PACKAGE_ROOT / "reproducibility"
OUT_FILE = OUT_DIR / "reproducible_manifest.json"

# Paths (relative to PACKAGE_ROOT) whose SHA-256 the manifest pins.
# Each entry: (relpath, role)
PINNED_ARTIFACTS = [
    ("credential_schema.json", "schema-artifact"),
    ("examples/valid_ct_lung_nodule.json", "credential-example-clean"),
    ("examples/failures/tampered_verdict.json", "credential-example-broken"),
    ("examples/failures/inverted_ci.json", "credential-example-broken"),
    ("examples/failures/missing_field.json", "credential-example-broken"),
    ("examples/failures/unknown_framework_hash.json", "credential-example-broken"),
    ("examples/failures/undersized_pass.json", "credential-example-broken"),
    ("examples/failures/bca_headline.json", "credential-example-broken"),
    ("examples/expected_audit_output.txt", "audit-snapshot"),
    ("../experiments/cross_modality_consistency/results.json", "6-credential-demo"),
    ("../experiments/estimator_coverage/results.json", "estimator-coverage"),
    ("../experiments/estimator_coverage/power_results.json", "estimator-power"),
    ("../experiments/estimator_coverage/dice_results.json", "estimator-dice"),
    ("../experiments/estimator_coverage/cr_results.json", "estimator-cr"),
]

# Human-facing reproduce commands (independent verifier path).
REPRODUCE_COMMANDS = [
    "pip install -e \"pwm_dose_equivalence[test]\"",
    "cd pwm_dose_equivalence && pytest -q            # 140/140 tests",
    "cd pwm_dose_equivalence && python examples/regenerate.py   # re-issue examples",
    "cd pwm_dose_equivalence && python scripts/generate_reproducible_manifest.py",
    "cd experiments/cross_modality_consistency && python cross_modality_consistency.py"
    "  # 6-credential demo (seed=42)",
]


def sha256_of(relpath: str) -> str:
    p = (PACKAGE_ROOT / relpath).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"manifest artifact missing: {p}")
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def main() -> int:
    # Framework hash from the library itself (content-addressed L2 spec).
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))
    try:
        from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA
        from pwm_dose_equivalence.framework_hash import framework_hash
    except ImportError:
        print(
            "error: run from WS-2_framework root or with pwm_dose_equivalence installed",
            file=sys.stderr,
        )
        return 2

    schema_version = CREDENTIAL_JSON_SCHEMA.get("$id", "unknown")
    artifacts = []
    for relpath, role in PINNED_ARTIFACTS:
        artifacts.append({"path": relpath, "sha256": sha256_of(relpath), "role": role})

    manifest = {
        "schema_version": "pwm-reproducible-artifact/v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "library": {
            "name": "pwm_dose_equivalence",
            "version": "0.2.2",
            "framework_hash": framework_hash(),
            "credential_schema": schema_version,
        },
        "test_matrix": {
            "total": 140,
            "integration_e2e": 10,
            "credential_audit": 35,
            "cli": 12,
            "examples_schema_artifact": 11,
        },
        "artifacts": artifacts,
        "reproduce_commands": REPRODUCE_COMMANDS,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"wrote {OUT_FILE}")
    print(f"framework_hash: {manifest['library']['framework_hash']}")
    print(f"artifacts pinned: {len(artifacts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
