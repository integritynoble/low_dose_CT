"""The H1a demonstration accepts the valid synthetic package, rejects every corrupted copy for a named
reason, reports a verifier that could not run as UNVERIFIED rather than as either verdict, and leaves the
valid package byte-identical. The last test guards the silent skip: with jsonschema absent the schema check
must report itself as not executed and the package must not be ACCEPTed.

Run from the fixture/ directory:  PYTHONPATH=. pytest -q tests/test_demo_verify.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

import demo_verify as dv


@pytest.fixture(scope="module")
def packet(tmp_path_factory):
    out = tmp_path_factory.mktemp("demo")
    return out, dv.run_demo(out / "run", seed=3, host_alias="test-host", log=lambda *a, **k: None)


def test_every_case_decides_as_fixed_in_advance(packet):
    _, P = packet
    by = {r["case"]: r for r in P["cases"]["results"]}
    assert P["cases"]["requested"] == P["cases"]["completed"] == len(dv.CASES) == 8
    assert P["cases"]["with_admissible_verdict"] == 7          # D08 is UNVERIFIED, not a verdict
    for case_id, _desc, _corruption, expected in dv.CASES:
        assert by[case_id]["observed"] == expected, (case_id, by[case_id]["reasons"], by[case_id]["not_executed"])
    assert P["acceptance_verdict"] == "PASS"


def test_rejections_name_the_thing_that_is_wrong(packet):
    _, P = packet
    by = {r["case"]: r for r in P["cases"]["results"]}
    assert any("task_nodule_score.nii.gz" in r for r in by["D03"]["reasons"])
    assert any(r.startswith("integrity: bytes differ") and "recon_mean.nii.gz" in r for r in by["D04"]["reasons"])
    assert any("counts.n_scans" in r and "metadata says 9" in r for r in by["D05"]["reasons"])
    assert any("$.credential.verdict" in r for r in by["D06"]["reasons"])
    assert any("error_abs.nii.gz is not |recon - reference|" in r for r in by["D07"]["reasons"])


def test_a_verifier_that_cannot_run_is_unverified_not_a_verdict(packet):
    _, P = packet
    d08 = {r["case"]: r for r in P["cases"]["results"]}["D08"]
    assert d08["observed"] == "UNVERIFIED"
    assert any(x.startswith("integrity: PackageError") for x in d08["not_executed"])
    integrity = {c["check"]: c for c in d08["checks"]}["integrity"]
    assert integrity["status"] == "error" and integrity["executed"] is False


def test_the_valid_corpus_is_untouched_by_the_cases(packet):
    out, P = packet
    assert P["valid_corpus_untouched_after_all_cases"] is True
    valid = out / "run" / "valid"
    assert hashlib.sha256((valid / "MANIFEST.sha256").read_bytes()).hexdigest() == P["outputs"]["valid_manifest_sha256"]
    assert dv.verify_bundle(valid)["decision"] == "ACCEPT"
    # and every corruption happened in its own disposable copy
    assert all(Path(r["target"]).resolve() != valid.resolve() for r in P["cases"]["results"] if r["corruption"] != "none")


def test_the_packet_carries_the_minimum_envelope(packet):
    _, P = packet
    for key in ("run_id", "started_utc", "finished_utc", "host_alias", "source", "script_sha256", "agent", "runtime",
                "data", "cases", "resources", "outputs", "acceptance_verdict", "limitations", "supersedes", "public_export_allowlist"):
        assert key in P, key
    assert P["host_alias"] == "test-host"
    assert P["data"]["designation"] == "synthetic"
    assert P["agent"]["backend"] is None and P["agent"]["human_interventions"] == 0
    assert P["resources"]["gpu_seconds"] == 0
    assert P["runtime"]["numpy"] and P["runtime"]["pwm_dose_equivalence"]
    json.dumps(P)   # serialisable as written


def test_schema_check_reports_itself_when_jsonschema_is_absent(packet, monkeypatch):
    """package_corpus returns no errors when jsonschema is missing. The demonstration must not read that as a pass."""
    out, _ = packet
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a, **k: None if name == "jsonschema" else real(name, *a, **k))
    v = dv.verify_bundle(out / "run" / "valid")
    assert v["decision"] == "UNVERIFIED"
    assert any(x.startswith("schema:") and "not importable" in x for x in v["not_executed"])


def test_refuses_a_non_empty_output_directory(tmp_path):
    (tmp_path / "x").write_text("occupied")
    with pytest.raises(SystemExit):
        dv.run_demo(tmp_path, seed=1, log=lambda *a, **k: None)


def test_runtime_versions_falls_back_when_a_dependency_is_not_installed(monkeypatch):
    """A dependency on PYTHONPATH is importable but carries no distribution metadata.

    A host without ``pip`` can only supply dependencies that way, and before this
    fallback the packet recorded ``None`` for them, leaving the evidence packet
    incomplete for a run that was otherwise fine. Metadata still wins where it exists.
    """
    import importlib.metadata as md

    import pwm_dose_equivalence

    real_version = md.version

    def no_metadata(name):
        if name == "pwm_dose_equivalence":
            raise md.PackageNotFoundError(name)
        return real_version(name)

    monkeypatch.setattr(md, "version", no_metadata)

    out = dv.runtime_versions()
    assert out["pwm_dose_equivalence"] == pwm_dose_equivalence.__version__
    assert out["numpy"], "metadata must still be preferred where it exists"


def test_runtime_versions_records_none_for_a_genuinely_absent_module(monkeypatch):
    """Absent is still absent: the fallback must not invent a version."""
    import importlib.metadata as md

    monkeypatch.setattr(md, "version", lambda name: (_ for _ in ()).throw(md.PackageNotFoundError(name)))
    monkeypatch.setattr(dv.importlib, "import_module", lambda name: (_ for _ in ()).throw(ImportError(name)))

    out = dv.runtime_versions()
    assert out["numpy"] is None and out["pwm_dose_equivalence"] is None
    assert out["python"], "python and platform are not looked up this way"
