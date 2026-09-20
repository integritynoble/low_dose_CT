"""Regression tests for the WS-4 submission gate's referee-path bypass.

The write-back gate lives in ``scoring/heldout.py`` and is exercised here at two
layers with two different scopes:

* heldout layer (:func:`check_submission_cannot_write_back`) -- scans the whole
  submission for a structural ability to write back to the board / held-out
  data. It walks **dict keys and values** recursively, scans the payload tree,
  and scans the submitter-controlled metadata fields ``method_name``, ``vendor``
  and ``dose`` (all are recorded verbatim on the board, so all are referee-path
  surfaces).
* CLI layer (``scoring.cli submit``, main baseline) -- builds
  ``SubmissionEnvelope(method_name=..., result=...)`` only. ``vendor`` / ``dose``
  are passed to :func:`add_submission` as grouping metadata and do **not** travel
  inside the envelope, so the CLI's write-back gate rejects a poisoned payload
  tree or a poisoned method name, and accepts a poisoned vendor / dose as
  metadata recorded verbatim. The library gate still covers them; the CLI just
  does not route them through it.

The CLI also exercises the ValueError rejection path of :func:`add_submission`
(a result with no paired block, or a block that violates the §4 paired rule) and
its all-blocks-validated-before-append behaviour.

Stdlib + pytest only; no network. Locating the source tree, in order:
  1. ``$WS4_ROOT`` -- the directory containing ``scoring/heldout.py``;
  2. otherwise, the nearest ancestor of this file (or ancestor/``WS-4_leaderboard``)
     that contains ``scoring/heldout.py``.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scoring.task_spec import TASK_LABEL
from scoring.verify import provenance_sha256


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
    write-back gate and any rejection is attributable to it alone. Carries a
    §2-D claim block so the submission also clears the provenance gate."""
    manifest = {"corpus": "LIDC lowdose_sim", "r": 0.25, "seed": 42, "n_patients": 2}
    weights = {"arch": "conv", "params": 1000}
    return {"validation": {"paired_methods": {"algo": {
        "psnr_db": 18.0, "ssim": 0.91,
        "detectability": {"bander_roi": 0.63, "cnr_mean": 6.0,
                          "cho_auc_mean": 0.99,
                          "task": "SKE-Gaussian20HU-s2px"}}}},
        "claim": {"task_id": TASK_LABEL,
                  "protocol_id": "detectability-freq-v1",
                  "data_manifest_sha256": provenance_sha256(manifest),
                  "model_sha256": provenance_sha256(weights),
                  "evaluator_version": "pwm_ldct_recon-2026-09-14"},
        "evidence": {"data_manifest": manifest, "model_weights": weights}}


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
# Hole A -- a referee path smuggled into a dict KEY
# --------------------------------------------------------------------------- #
# ``assert_no_referee_paths`` pushes dict keys onto its traversal stack, so a
# referee-owned path used as a key is scanned exactly like one in a value.

def test_hole_a_referee_path_as_a_top_level_dict_key():
    bad = H.SubmissionEnvelope(
        method_name="ok", result={f"../scoring/data/{LEADERBOARD}": 1})
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as a dict KEY was accepted; "
        "dict keys are submitter-controlled data and must be scanned")


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
    """A smuggled write handle used as a key escapes neither traversal:
    _find_nested_write_surface walks keys as well as values."""
    class Handle:
        def write(self):
            pass

        def __hash__(self):
            return 0

    bad = H.SubmissionEnvelope(method_name="ok", result={Handle(): "v"})
    violations = H.check_submission_cannot_write_back(bad)
    assert any("write surface" in v for v in violations), (
        "an object exposing write() used as a dict KEY was accepted; "
        "_find_nested_write_surface must traverse dict keys")


# --------------------------------------------------------------------------- #
# Hole B -- a referee path smuggled into the method name
# --------------------------------------------------------------------------- #
# ``method_name`` is recorded verbatim on the board, so the envelope gate scans
# it for referee-owned paths exactly like the payload tree.

def test_hole_b_referee_path_as_the_method_name():
    bad = H.SubmissionEnvelope(method_name=f"../scoring/data/{LEADERBOARD}",
                               result=_valid_payload())
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as the METHOD NAME was accepted; "
        "check_submission_cannot_write_back scans submission.method_name")


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
# Hole C -- referee paths in vendor / dose at the HELDOUT layer
# --------------------------------------------------------------------------- #
# ``vendor`` and ``dose`` are recorded verbatim as grouping keys, so the heldout
# gate scans them exactly like ``method_name``. Note the scope: the **main CLI**
# builds the envelope with ``method_name`` + ``result`` only, so at the CLI layer
# vendor / dose do not pass through this gate (see the CLI section below).

def test_hole_c_referee_path_as_vendor_is_rejected():
    bad = H.SubmissionEnvelope(method_name="ok", result=_valid_payload(),
                               vendor=f"../data/{LEADERBOARD}")
    violations = H.check_submission_cannot_write_back(bad)
    assert _paths_flagged(violations), (
        "a referee-owned path used as the VENDOR was accepted at the heldout layer")


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


# --------------------------------------------------------------------------- #
# end-to-end through the CLI (`scoring.cli submit`, main baseline)
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
    """Control for the CLI tests below."""
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


def test_cli_records_poisoned_vendor_as_metadata(tmp_path):
    """Main-baseline behaviour: vendor/dose do not travel inside the envelope,
    so the CLI write-back gate does not scan them; they are recorded verbatim
    as grouping metadata. The heldout-layer gate still covers them (above), and
    the §2-B save gate now backstops the CLI too: a board whose vendor group is
    missing a trap measurement cannot be written, so the CLI refuses it."""
    r = _cli_submit(tmp_path, _valid_payload(), "Attacker",
                    vendor=f"../scoring/data/{LEADERBOARD}")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "REJECT" in r.stdout
    assert "no trap measured" in r.stdout + r.stderr
    assert not (tmp_path / "board.json").exists(), (
        "a submission whose vendor group has no trap was written to the board")


def test_cli_records_poisoned_dose_as_metadata(tmp_path):
    r = _cli_submit(tmp_path, _valid_payload(), "Attacker",
                    dose=f"../scoring/data/{HELDOUT}")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "accepted" in r.stdout
    board = json.loads((tmp_path / "board.json").read_text(encoding="utf-8"))
    assert any(e["dose"] == f"../scoring/data/{HELDOUT}"
               for e in board["entries"]), "dose was not recorded verbatim"


def test_cli_clean_vendor_and_dose_still_accepted(tmp_path):
    """Honest metadata must keep working."""
    r = _cli_submit(tmp_path, _valid_payload(), "HonestMethod",
                    vendor="Siemens", dose="0.25")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "accepted" in r.stdout


def test_cli_rejects_result_without_paired_block(tmp_path):
    """ValueError path: add_submission refuses a result with no paired §4 block
    and the CLI prints REJECT without writing a board."""
    r = _cli_submit(tmp_path, {}, "Attacker")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "REJECT" in r.stdout
    assert "carries neither fidelity" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


def test_cli_rejects_unpublishable_paired_block(tmp_path):
    """ValueError path: a block reporting fidelity without detectability is not
    publishable (§4 both-or-neither) and the CLI prints REJECT."""
    payload = {"validation": {"paired_methods": {"algo": {
        "psnr_db": 18.0, "ssim": 0.91}}}}
    r = _cli_submit(tmp_path, payload, "Attacker")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "REJECT" in r.stdout
    assert "not publishable" in r.stdout
    assert not (tmp_path / "board.json").exists(), "a rejected submission was written to the board"


# --------------------------------------------------------------------------- #
# submission gate: validate every block before appending any
# --------------------------------------------------------------------------- #

def test_add_submission_validates_every_block_before_appending():
    """'先全量校验再写板': one invalid paired block must reject the whole
    submission without leaving earlier valid blocks on the caller's board."""
    from scoring import add_submission, new_leaderboard

    board = new_leaderboard()
    n0 = len(board["entries"])
    result = {"validation": {"paired_methods": {
        "algo_ok": {"psnr_db": 18.0, "ssim": 0.91,
                    "detectability": {"bander_roi": 0.63, "cnr_mean": 6.0,
                                      "cho_auc_mean": 0.99,
                                      "task": "SKE-Gaussian20HU-s2px"}},
        "algo_bad": {"psnr_db": 18.0, "ssim": 0.91},  # fidelity only, §4 violation
    }}}
    with pytest.raises(ValueError, match="algo_bad"):
        add_submission(board, result, method="Mixed")
    assert len(board["entries"]) == n0, (
        "a partially validated submission was appended to the board")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
