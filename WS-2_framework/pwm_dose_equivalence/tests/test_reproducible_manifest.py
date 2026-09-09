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

`generated_at_utc` is excluded from the content comparison, and that exclusion
is irreducible rather than a shortcut: the field is provenance metadata with no
source of truth inside the tree. Taken from the manifest itself any check is
circular, and taken from git commit dates it breaks on every history rewrite --
which this repository has had. What CAN be established is that generation is
deterministic, and test_generation_is_byte_reproducible does that.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PACKAGE_ROOT / "reproducibility" / "reproducible_manifest.json"
GENERATOR = PACKAGE_ROOT / "scripts" / "generate_reproducible_manifest.py"



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


def _regenerate(source_date_epoch: str | None = None) -> dict:
    """Run the generator and return what it wrote. Overwrites MANIFEST.

    Passing source_date_epoch pins the manifest's timestamp, which is what
    makes a whole-file comparison possible.
    """
    env = os.environ.copy()
    if source_date_epoch is not None:
        env["SOURCE_DATE_EPOCH"] = source_date_epoch
    proc = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, (
        f"generator exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _epoch_of(manifest: dict) -> str:
    """The manifest's own timestamp as a SOURCE_DATE_EPOCH value."""
    return str(int(datetime.fromisoformat(manifest["generated_at_utc"]).timestamp()))


# The one field regeneration cannot be asked to reproduce. See the module
# docstring: it has no in-tree source of truth, so no test here can guard it.
# Every other field is compared exactly.
UNVERIFIABLE_FIELDS = ("generated_at_utc",)


def _content(manifest: dict) -> dict:
    stripped = copy.deepcopy(manifest)
    for field in UNVERIFIABLE_FIELDS:
        stripped.pop(field, None)
    return stripped


def test_manifest_regenerates_identically(committed):
    regenerated = _regenerate()
    assert _content(regenerated) == _content(committed), (
        "reproducible_manifest.json is stale — run "
        "python scripts/generate_reproducible_manifest.py"
    )


def test_generation_is_byte_reproducible(committed):
    """Two runs at the same SOURCE_DATE_EPOCH must agree on every byte.

    This is what the timestamp support buys. It does not establish that the
    committed timestamp is truthful -- nothing here can -- but it does
    establish that the manifest is a deterministic function of the tree plus
    that one input, so anyone can reproduce the committed file exactly.
    """
    first = _regenerate(source_date_epoch="1700000000")
    second = _regenerate(source_date_epoch="1700000000")
    assert first == second
    assert first["generated_at_utc"] == "2023-11-14T22:13:20+00:00"

    at_committed_epoch = _regenerate(source_date_epoch=_epoch_of(committed))
    assert at_committed_epoch == committed, (
        "regenerating at the committed manifest's own epoch did not reproduce "
        "it byte for byte"
    )


def test_unverifiable_fields_are_present_so_excluding_them_stays_honest(committed):
    """Excluding a field from the content comparison must not let it vanish."""
    for field in UNVERIFIABLE_FIELDS:
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
    assert _content(on_disk_before) != _content(regenerated), (
        "a falsified manifest compared equal to the regenerated one, so the "
        "comparison is reading the file after the generator overwrote it "
        "(issue #8)"
    )
    assert _content(regenerated) == _content(committed), (
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
