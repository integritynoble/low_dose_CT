"""Drift-protection for the P3-4 reproducible-artifact manifest.

Verifies the committed reproducibility/reproducible_manifest.json matches what
scripts/generate_reproducible_manifest.py produces from the current tree
(SHA-256 per pinned artifact) and the live framework hash. A silent-schema or
artifact edit that forgets to regenerate the manifest fails CI here.

The generator writes its output file in place and takes no output-path option,
so any test that runs it must read the committed manifest *before* regenerating
and put the original bytes back afterwards. Comparing against the file after
the generator has run compares it with itself, which is always true and is the
defect this file carried until issue #8.

The generator also stamps `generated_at_utc` from the wall clock, so a
byte-identical regeneration is impossible by construction and the comparison
must exclude that one field. Everything else is required to match exactly.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PACKAGE_ROOT / "reproducibility" / "reproducible_manifest.json"
GENERATOR = PACKAGE_ROOT / "scripts" / "generate_reproducible_manifest.py"

# Fields the generator cannot reproduce across runs. Keep this list as short as
# it can possibly be: every name here is a field the drift test stops guarding.
VOLATILE_FIELDS = ("generated_at_utc",)


def _comparable(manifest: dict) -> dict:
    """The manifest minus the fields regeneration is allowed to change."""
    stripped = copy.deepcopy(manifest)
    for field in VOLATILE_FIELDS:
        stripped.pop(field, None)
    return stripped


@pytest.fixture
def committed() -> Iterator[dict]:
    """The manifest as committed, with the file restored when the test ends.

    Read before anything can regenerate it, and written back unconditionally so
    a test that runs the generator does not leave the working tree dirty or
    repair a manifest a later test is about to inspect.
    """
    original = MANIFEST.read_bytes()
    try:
        yield json.loads(original.decode("utf-8"))
    finally:
        MANIFEST.write_bytes(original)


def _regenerate() -> dict:
    """Run the generator and return what it wrote. Overwrites MANIFEST."""
    proc = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"generator exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_regenerates_identically(committed):
    regenerated = _regenerate()
    assert _comparable(regenerated) == _comparable(committed), (
        "reproducible_manifest.json is stale — run "
        "python scripts/generate_reproducible_manifest.py"
    )


def test_volatile_fields_are_present_so_excluding_them_stays_honest(committed):
    """Excluding a field from the drift comparison must not let it vanish."""
    from datetime import datetime

    for field in VOLATILE_FIELDS:
        assert field in committed, f"{field} is excluded from the comparison but absent"
    datetime.fromisoformat(committed["generated_at_utc"])


def test_falsified_manifest_is_detected_not_repaired(committed):
    """Regression guard for issue #8.

    Falsify the committed file, then compare what is on disk *before* the
    generator runs against what it produces. If these compare equal the
    comparison is reading the file after the overwrite, and the drift test has
    become a tautology again.
    """
    falsified = copy.deepcopy(committed)
    falsified["library"]["framework_hash"] = "sha256:" + "0" * 64
    falsified["test_matrix"]["total"] = 99999
    MANIFEST.write_text(json.dumps(falsified, indent=2) + "\n", encoding="utf-8")

    on_disk_before = json.loads(MANIFEST.read_text(encoding="utf-8"))
    regenerated = _regenerate()

    assert on_disk_before == falsified, "the falsified manifest was not the file read back"
    assert _comparable(on_disk_before) != _comparable(regenerated), (
        "a falsified manifest compared equal to the regenerated one, so the "
        "comparison is reading the file after the generator overwrote it "
        "(issue #8)"
    )
    assert _comparable(regenerated) == _comparable(committed), (
        "regeneration did not reproduce the committed manifest"
    )


def test_manifest_pins_live_framework_hash(committed):
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))
    from pwm_dose_equivalence.framework_hash import framework_hash

    assert committed["library"]["framework_hash"] == framework_hash()
    assert committed["library"]["framework_hash"].startswith("sha256:")


def test_manifest_test_matrix_matches_readme_claims(committed):
    t = committed["test_matrix"]
    assert t["total"] == 140
    assert t["integration_e2e"] == 10
    assert t["credential_audit"] == 35
    assert t["cli"] == 12
    assert t["examples_schema_artifact"] == 11


def test_manifest_every_pinned_artifact_exists_and_hash_matches(committed):
    import hashlib

    for art in committed["artifacts"]:
        p = (PACKAGE_ROOT / art["path"]).resolve()
        assert p.is_file(), f"pinned artifact missing: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert art["sha256"] == f"sha256:{h}", f"hash drift on {art['path']}"


def test_manifest_includes_6_credential_demo_and_reproduce_commands(committed):
    roles = {a["role"] for a in committed["artifacts"]}
    assert "6-credential-demo" in roles
    assert "schema-artifact" in roles
    assert any("pytest" in c for c in committed["reproduce_commands"])
    assert any("seed" in c.lower() for c in committed["reproduce_commands"])
