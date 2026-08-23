"""Drift-protection for the P3-4 reproducible-artifact manifest.

Re-runs scripts/generate_reproducible_manifest.py in-process and verifies the
committed reproducibility/reproducible_manifest.json matches the current tree
(SHA-256 per pinned artifact) and the live framework hash. A silent-schema or
artifact edit that forgets to regenerate the manifest fails CI here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PACKAGE_ROOT / "reproducibility" / "reproducible_manifest.json"
GENERATOR = PACKAGE_ROOT / "scripts" / "generate_reproducible_manifest.py"


def _regenerate() -> dict:
    out = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    with open(MANIFEST, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_committed() -> dict:
    with open(MANIFEST, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_manifest_regenerates_identically():
    regenerated = _regenerate()
    committed = _load_committed()
    assert regenerated == committed, (
        "reproducible_manifest.json is stale — run "
        "python scripts/generate_reproducible_manifest.py"
    )


def test_manifest_pins_live_framework_hash():
    m = _load_committed()
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))
    from pwm_dose_equivalence.framework_hash import framework_hash

    assert m["library"]["framework_hash"] == framework_hash()
    assert m["library"]["framework_hash"].startswith("sha256:")


def test_manifest_test_matrix_matches_readme_claims():
    m = _load_committed()
    t = m["test_matrix"]
    assert t["total"] == 140
    assert t["integration_e2e"] == 10
    assert t["credential_audit"] == 35
    assert t["cli"] == 12
    assert t["examples_schema_artifact"] == 11


def test_manifest_every_pinned_artifact_exists_and_hash_matches():
    m = _load_committed()
    import hashlib

    for art in m["artifacts"]:
        p = (PACKAGE_ROOT / art["path"]).resolve()
        assert p.is_file(), f"pinned artifact missing: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert art["sha256"] == f"sha256:{h}", f"hash drift on {art['path']}"


def test_manifest_includes_6_credential_demo_and_reproduce_commands():
    m = _load_committed()
    roles = {a["role"] for a in m["artifacts"]}
    assert "6-credential-demo" in roles
    assert "schema-artifact" in roles
    assert any("pytest" in c for c in m["reproduce_commands"])
    assert any("seed" in c.lower() for c in m["reproduce_commands"])
