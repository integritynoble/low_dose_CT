"""Tests for the ``pwm-audit`` CLI (L0.2.2)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pytest

from pwm_dose_equivalence import Task, signal_equivalence_credential
from pwm_dose_equivalence.cli import main


@pytest.fixture
def credential_path(tmp_path: Path) -> Path:
    rng = np.random.default_rng(0)
    deltas = rng.normal(0.0, 0.01, size=200)
    cred = signal_equivalence_credential(
        paired_a=np.zeros(200),
        paired_b=-deltas,
        signal_ratio=0.25,
        modality="CT",
        task=Task("liver_dice", metric="dice"),
        subpopulation="adult_abdomen_pwm_l3_test_v1",
        epsilon=0.05,
        alpha=0.05,
        n_bootstrap=500,
        seed=42,
        sigma_delta_hint=0.05,
    )
    path = tmp_path / "credential.json"
    path.write_text(cred.to_json())
    return path


def _run(argv, stdin_text: str = ""):
    stdin = io.StringIO(stdin_text)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(argv, stdin=stdin, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


# -- happy paths -----------------------------------------------------------

def test_valid_credential_exits_zero(credential_path):
    code, out, err = _run([str(credential_path)])
    assert code == 0
    assert "pwm-audit: OK" in out
    assert "Issues: none" in out
    assert err == ""


def test_json_output_is_parseable(credential_path):
    code, out, _ = _run([str(credential_path), "--json"])
    assert code == 0
    report = json.loads(out)
    assert report["ok"] is True
    assert report["schema_valid"] is True
    assert report["verdict_self_consistent"] is True
    assert "issues" in report
    assert "warnings" in report


def test_stdin_input(credential_path):
    raw = credential_path.read_text()
    code, out, _ = _run(["-"], stdin_text=raw)
    assert code == 0
    assert "OK" in out


# -- failure paths --------------------------------------------------------

def test_tampered_verdict_exits_one(credential_path, tmp_path):
    d = json.loads(credential_path.read_text())
    # Flip verdict to something the CI does not support
    d["credential"]["verdict"] = "FAIL" if d["credential"]["verdict"] == "PASS" else "PASS"
    bad = tmp_path / "tampered.json"
    bad.write_text(json.dumps(d))
    code, out, _ = _run([str(bad)])
    assert code == 1
    assert "FAIL" in out
    assert "verdict" in out


def test_bad_json_exits_one(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    code, out, _ = _run([str(p)])
    assert code == 1
    assert "not valid JSON" in out


def test_nonexistent_file_exits_two(tmp_path):
    missing = tmp_path / "nope.json"
    code, _, err = _run([str(missing)])
    assert code == 2
    assert "cannot read" in err


# -- argparse plumbing ----------------------------------------------------

def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "pwm-audit" in out


def test_missing_argument_exits_two(capsys):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


# -- soft-signal surfacing in human output -------------------------------

def test_warnings_section_visible_when_present(credential_path, tmp_path):
    d = json.loads(credential_path.read_text())
    d["credential"]["estimator"] = "bca"  # emits opt-in warning
    p = tmp_path / "bca.json"
    p.write_text(json.dumps(d))
    code, out, _ = _run([str(p)])
    # BCa warning is soft; ok stays True
    assert code == 0
    assert "Warnings" in out
    assert "opt-in" in out


def test_unknown_framework_hash_surfaces_warning(credential_path, tmp_path):
    d = json.loads(credential_path.read_text())
    d["framework_hash"] = "sha256:" + "0" * 64
    p = tmp_path / "stale.json"
    p.write_text(json.dumps(d))
    code, out, _ = _run([str(p)])
    assert code == 0  # framework-hash mismatch is a warning, not an issue
    assert "framework_hash_known     = False" in out
    assert "does not match" in out


def test_default_uses_real_streams(credential_path, monkeypatch, capsys):
    """When stdin/stdout/stderr are omitted, sys.* are used."""
    monkeypatch.setattr("sys.argv", ["pwm-audit", str(credential_path)])
    code = main()
    captured = capsys.readouterr()
    assert code == 0
    assert "OK" in captured.out
