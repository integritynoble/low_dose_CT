"""Regression tests for the WS-4 submission gate's referee-path bypass.

Two independent holes in ``WS-4_leaderboard/scoring/heldout.py``:

  A. ``assert_no_referee_paths`` walks ``dict.values()`` only, so a referee-owned
     path placed in a dict **key** is never scanned. (The sibling traversal
     ``_find_nested_write_surface`` has the same key-blindness.)
  B. ``check_submission_cannot_write_back`` scans ``submission.result`` only; the
     submitter-controlled ``submission.method_name`` is never checked at all.

Each hole is covered separately, at the library level and end-to-end through
``python -m scoring.cli submit``. Stdlib + pytest only; no network.

Locating the source tree, in order:
  1. ``$WS4_ROOT`` -- the directory containing ``scoring/heldout.py``;
  2. otherwise, the nearest ancestor of this file (or ancestor/``WS-4_leaderboard``)
     that contains ``scoring/heldout.py``.

Run:  WS4_ROOT=/path/to/WS-4_leaderboard python -m pytest test_referee_path_bypass.py -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# --------------------------------------------------------------------------- #
# locating and loading the module under test
# --------------------------------------------------------------------------- #

def _ws4_root() -> Path:
    env = os.environ.get("WS4_ROOT")
    if env:
        root = Path(env).resolve()
        if not (root / "scoring" / "heldout.py").is_file():
            raise RuntimeError(f"WS4_ROOT={root} has no scoring/heldout.py")
        return root
    here = Path(__file__).resolve().parent
    for base in (here, *here.parents):
        for cand in (base, base / "WS-4_leaderboard"):
            if (cand / "scoring" / "heldout.py").is_file():
                return cand
    raise RuntimeError(
        "could not find a directory containing scoring/heldout.py; "
        "set WS4_ROOT to the WS-4_leaderboard root")


WS4_ROOT = _ws4_root()


def _load_heldout():
    """Import heldout.py by path, bypassing the package __init__."""
    path = WS4_ROOT / "scoring" / "heldout.py"
    name = "_ws4_heldout_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # @dataclass resolves annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


H = _load_heldout()
LEADERBOARD = H.LEADERBOARD_FILE_NAME     # "leaderboard.json"
HELDOUT = H.HELDOUT_FILE_NAME             # "heldout.json"


def _paths_flagged(violations) -> bool:
    return any("referee-owned files" in v for v in violations)


def _valid_payload() -> dict:
    """A submission body that passes the §4 paired gate, so the CLI reaches the
    write-back gate and any rejection is attributable to it alone."""
    return {"validation": {"paired_methods": {"algo": {
        "psnr_db": 18.0, "ssim": 0.91,
        "detectability": {"bander_roi": 0.63, "cnr_mean": 6.0,
                          "cho_auc_mean": 0.99,
                          "task": "SKE-Gaussian20HU-s2px"}}}}}


# --------------------------------------------------------------------------- #
# control: the parts of the gate that are sound must stay sound
# --------------------------------------------------------------------------- #

def test_control_referee_path_in_a_value_is_rejected():
    """Baseline. Passes before and after the fix; if it fails, the harness is
    wrong, not the gate."""
    bad = H.SubmissionEnvelope(method_name="ok",
                               result={"save_to": f"../data/{LEADERBOARD}"})
    assert _paths_flagged(H.check_submission_cannot_write_back(bad))


def test_control_clean_submission_still_accepted():
    """The fix must not start refusing honest submissions."""
    ok = H.SubmissionEnvelope(method_name="MyMethod", result=_valid_payload())
    assert H.check_submission_cannot_write_back(ok) == []


# --------------------------------------------------------------------------- #
# Hole A -- the traversal walks values only, so dict keys are never scanned
# --------------------------------------------------------------------------- #

def test_hole_a_referee_path_as_a_top_level_dict_key():
    bad = H.SubmissionEnvelope(
        method_name="ok", result={f"../scoring/data/{LEADERBOARD}": 1})
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as a dict KEY was accepted; "
        "assert_no_referee_paths extends its stack with dict.values() only")


def test_hole_a_referee_path_as_a_nested_dict_key():
    bad = H.SubmissionEnvelope(
        method_name="ok",
        result={"validation": {"artifacts": [{f"../data/{HELDOUT}": "x"}]}})
    assert _paths_flagged(H.check_submission_cannot_write_back(bad)), (
        "a referee-owned path nested as a dict KEY was accepted")


def test_hole_a_scanner_flags_keys_directly():
    """The traversal itself, without the envelope wrapper."""
    assert H.assert_no_referee_paths({f"../data/{LEADERBOARD}": 1}) != []


def test_hole_a_write_surface_object_as_a_dict_key():
    """Same key-blindness in the sibling traversal _find_nested_write_surface:
    a smuggled write handle used as a key escapes the scan."""
    class Handle:
        def write(self):
            pass

        def __hash__(self):
            return 0

    bad = H.SubmissionEnvelope(method_name="ok", result={Handle(): "v"})
    violations = H.check_submission_cannot_write_back(bad)
    assert any("write surface" in v for v in violations), (
        "an object exposing write() used as a dict KEY was accepted; "
        "_find_nested_write_surface extends its stack with dict.values() only")


# --------------------------------------------------------------------------- #
# Hole B -- the gate is never applied to the method name
# --------------------------------------------------------------------------- #

def test_hole_b_referee_path_as_the_method_name():
    bad = H.SubmissionEnvelope(method_name=f"../scoring/data/{LEADERBOARD}",
                               result=_valid_payload())
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as the METHOD NAME was accepted; "
        "check_submission_cannot_write_back scans submission.result only")


def test_hole_b_heldout_path_as_the_method_name():
    bad = H.SubmissionEnvelope(method_name=f"../scoring/data/{HELDOUT}",
                               result=_valid_payload())
    assert _paths_flagged(H.check_submission_cannot_write_back(bad))


def test_hole_b_is_independent_of_hole_a():
    """Method name poisoned, payload entirely clean: hole B alone."""
    bad = H.SubmissionEnvelope(method_name=f"./{LEADERBOARD}", result={})
    assert H.assert_no_referee_paths(bad.result) == []          # payload is clean
    assert _paths_flagged(H.check_submission_cannot_write_back(bad))


# --------------------------------------------------------------------------- #
# end-to-end through the CLI (`scoring.cli submit`)
# --------------------------------------------------------------------------- #

def _cli_submit(tmp_path: Path, result: dict, method: str,
                vendor: str | None = None, dose: str | None = None):
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result), encoding="utf-8")
    env = dict(os.environ,
               PYTHONPATH=str(WS4_ROOT),
               PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-m", "scoring.cli", "submit",
           "--result", str(result_file), "--method", method,
           "--out", str(tmp_path / "board.json")]
    if vendor is not None:
        cmd += ["--vendor", vendor]
    if dose is not None:
        cmd += ["--dose", dose]
    return subprocess.run(cmd, cwd=str(tmp_path), env=env,
                          capture_output=True, text=True)


def test_cli_accepts_a_clean_submission(tmp_path):
    """Control for the two CLI tests below."""
    r = _cli_submit(tmp_path, _valid_payload(), "HonestMethod")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "accepted" in r.stdout


def test_cli_hole_a_rejects_key_smuggled_referee_path(tmp_path):
    payload = _valid_payload()
    payload[f"../scoring/data/{LEADERBOARD}"] = "smuggled as a key"
    r = _cli_submit(tmp_path, payload, "Attacker")
    assert r.returncode == 1, (
        "CLI accepted a submission carrying a referee path as a dict key\n"
        + r.stdout + r.stderr)
    assert "REJECT" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


def test_cli_hole_b_rejects_referee_path_method_name(tmp_path):
    r = _cli_submit(tmp_path, _valid_payload(), f"../scoring/data/{HELDOUT}")
    assert r.returncode == 1, (
        "CLI accepted a referee-owned path as the method name\n"
        + r.stdout + r.stderr)
    assert "REJECT" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


# --------------------------------------------------------------------------- #
# Hole C -- the metadata fields beside method_name are never scanned
# --------------------------------------------------------------------------- #
#
# Hole B was fixed for ``method_name`` only. ``vendor`` and ``dose`` are the
# same shape: submitter-controlled strings recorded verbatim on the board
# (as group keys for spread / per-group trap rank). They never travel inside
# ``submission.result``, so the result-tree scan cannot see them, and the
# envelope does not carry them, so nothing scans them at all. A referee-owned
# file name smuggled through ``--vendor`` / ``--dose`` is accepted and written
# to the board today.


def test_hole_c_referee_path_as_vendor_is_rejected():
    bad = H.SubmissionEnvelope(method_name="ok", result=_valid_payload(),
                               vendor=f"../data/{LEADERBOARD}")
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as the VENDOR was accepted; "
        "the envelope carries no vendor/dose and the metadata fields are unscanned")


def test_hole_c_referee_path_as_dose_is_rejected():
    bad = H.SubmissionEnvelope(method_name="ok", result=_valid_payload(),
                               dose=f"../data/{HELDOUT}")
    assert _paths_flagged(H.check_submission_cannot_write_back(bad))


def test_hole_c_is_independent_of_holes_a_and_b():
    """Vendor poisoned, payload and method name entirely clean: hole C alone."""
    bad = H.SubmissionEnvelope(method_name="ok", result={},
                               vendor=f"./{LEADERBOARD}")
    assert H.assert_no_referee_paths(bad.result) == []          # payload is clean
    assert H.assert_no_referee_paths(bad.method_name) == []     # method is clean
    assert _paths_flagged(H.check_submission_cannot_write_back(bad))


def test_cli_hole_c_rejects_referee_path_vendor(tmp_path):
    r = _cli_submit(tmp_path, _valid_payload(), "Attacker",
                    vendor=f"../scoring/data/{LEADERBOARD}")
    assert r.returncode == 1, (
        "CLI accepted a referee-owned path as the vendor\n" + r.stdout + r.stderr)
    assert "REJECT" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


def test_cli_hole_c_rejects_referee_path_dose(tmp_path):
    r = _cli_submit(tmp_path, _valid_payload(), "Attacker",
                    dose=f"../scoring/data/{HELDOUT}")
    assert r.returncode == 1, (
        "CLI accepted a referee-owned path as the dose\n" + r.stdout + r.stderr)
    assert "REJECT" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


def test_cli_hole_c_control_clean_vendor_and_dose_still_accepted(tmp_path):
    """The fix must not start refusing honest metadata."""
    r = _cli_submit(tmp_path, _valid_payload(), "HonestMethod",
                    vendor="Siemens", dose="0.25")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "accepted" in r.stdout


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
