"""End-to-end tests for the ``examples/`` directory and the standalone
``credential_schema.json`` artifact.

The examples are *generated* by ``examples/regenerate.py``; the schema JSON
is *generated* by ``scripts/dump_schema.py``. Both these tests catch drift
between the generator and the on-disk artifact, and verify that every
failure example produces the expected audit signal.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pwm_dose_equivalence.audit import audit_credential
from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
FAILURES = EXAMPLES / "failures"
SCHEMA_JSON = ROOT / "credential_schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# -- the clean credential audits ok --------------------------------------

def test_valid_example_audits_clean():
    cred = _load(EXAMPLES / "valid_ct_lung_nodule.json")
    report = audit_credential(cred)
    assert report.ok is True
    assert report.schema_valid is True
    assert report.verdict_self_consistent is True
    assert report.framework_hash_known is True
    assert report.sample_size_check_ok is True
    assert report.issues == []
    assert report.warnings == []


def test_valid_example_verdict_is_pass():
    """The canonical example should land on PASS, not INDETERMINATE."""
    cred = _load(EXAMPLES / "valid_ct_lung_nodule.json")
    assert cred["credential"]["verdict"] == "PASS"


# -- each failure example produces its expected audit signal -------------

def test_tampered_verdict_caught_as_hard_issue():
    cred = _load(FAILURES / "tampered_verdict.json")
    report = audit_credential(cred)
    assert report.ok is False
    assert report.schema_valid is True
    assert report.verdict_self_consistent is False
    assert any("verdict" in i for i in report.issues)


def test_inverted_ci_caught_as_hard_issue():
    cred = _load(FAILURES / "inverted_ci.json")
    report = audit_credential(cred)
    assert report.ok is False
    assert any("delta_ci_low > delta_ci_high" in i for i in report.issues)


def test_missing_field_caught_as_hard_issue():
    cred = _load(FAILURES / "missing_field.json")
    report = audit_credential(cred)
    assert report.ok is False
    assert report.schema_valid is False
    assert any("missing required field" in i for i in report.issues)


def test_unknown_framework_hash_is_warning():
    cred = _load(FAILURES / "unknown_framework_hash.json")
    report = audit_credential(cred)
    # Soft signal: hard checks still pass, but framework_hash_known is False
    assert report.ok is True
    assert report.framework_hash_known is False
    assert any("does not match" in w for w in report.warnings)


def test_undersized_pass_is_warning():
    cred = _load(FAILURES / "undersized_pass.json")
    report = audit_credential(cred)
    assert report.ok is True
    assert report.sample_size_check_ok is False
    assert any("formula prescription" in w.lower() or "fluke" in w.lower()
               for w in report.warnings)


def test_bca_headline_is_warning():
    cred = _load(FAILURES / "bca_headline.json")
    report = audit_credential(cred)
    assert report.ok is True
    assert any("opt-in" in w for w in report.warnings)


# -- drift detection: regenerate.py output matches on-disk JSON ---------

def _import_regenerate():
    spec = importlib.util.spec_from_file_location(
        "examples_regenerate", EXAMPLES / "regenerate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_examples_match_regenerate_output(tmp_path: Path, monkeypatch):
    """If someone edits an example by hand, this test fails."""
    regen = _import_regenerate()

    # Redirect regenerate's HERE/FAILURES to tmp_path so we don't clobber
    # the committed files while computing the expected outputs.
    monkeypatch.setattr(regen, "HERE", tmp_path)
    monkeypatch.setattr(regen, "FAILURES", tmp_path / "failures")
    regen.regenerate()

    committed = sorted(p for p in EXAMPLES.rglob("*.json"))
    regenerated = sorted(p for p in tmp_path.rglob("*.json"))
    assert {p.name for p in committed} == {p.name for p in regenerated}, (
        "Example filename set differs between committed and regenerated."
    )
    for committed_path in committed:
        rel = committed_path.relative_to(EXAMPLES)
        regen_path = tmp_path / rel
        assert json.loads(committed_path.read_text()) == json.loads(
            regen_path.read_text()
        ), f"Drift detected in {rel}: re-run examples/regenerate.py"


# -- the standalone JSON Schema artifact stays in sync with the dict ----

def test_schema_json_matches_python_dict():
    assert SCHEMA_JSON.exists(), (
        "credential_schema.json missing; run python3 scripts/dump_schema.py"
    )
    on_disk = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    assert on_disk == CREDENTIAL_JSON_SCHEMA, (
        "credential_schema.json out of sync with CREDENTIAL_JSON_SCHEMA; "
        "re-run python3 scripts/dump_schema.py"
    )


def test_schema_json_is_draft_07_compatible():
    on_disk = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    assert on_disk["$schema"].startswith("http://json-schema.org/draft-07")
    assert on_disk["type"] == "object"


# -- snapshot of expected pwm-audit output stays in sync ----------------

def test_expected_audit_output_matches_snapshot():
    """Drift detection on examples/expected_audit_output.txt — re-runs
    pwm-audit on every example and asserts the concatenated output is
    bit-identical to the committed snapshot.

    Failures here mean either (a) the CLI's output formatting changed,
    (b) the audit logic changed, (c) an example was edited, or (d) the
    snapshot was edited by hand. In all four cases the fix is to
    re-run examples/regenerate_expected_outputs.py and commit the
    refreshed file alongside whatever else changed.
    """
    spec = importlib.util.spec_from_file_location(
        "examples_regenerate_outputs",
        EXAMPLES / "regenerate_expected_outputs.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    regenerated = module.regenerate()
    on_disk = (EXAMPLES / "expected_audit_output.txt").read_text(encoding="utf-8")
    assert regenerated == on_disk, (
        "Drift detected in examples/expected_audit_output.txt: re-run "
        "python3 examples/regenerate_expected_outputs.py"
    )
