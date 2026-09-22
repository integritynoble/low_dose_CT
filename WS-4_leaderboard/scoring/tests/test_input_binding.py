"""Task 4 -- input-bound provenance tests (2026-09-21).

Coverage (task book 4, "bind provenance to the evaluated inputs"):

* changed model bytes are rejected (the checkpoint file is re-hashed at runtime,
  a JSON self-report is never trusted on its own);
* changed manifest membership is rejected (a model not listed in
  ASSET_MANIFEST / hashes listing is NOT_IN_MANIFEST);
* placeholder/empty manifest hashes are UNVERIFIED, never invented or filled in;
* wrong method/task/dose binding is rejected;
* a claimed patient bootstrap with no fixed source is NO_BINDING / UNVERIFIED;
* a patient_id absent from the fixed split source is inconsistent / rejected;
* a self-reported patient map that contradicts the fixed source is rejected;
* a result that declares no patient bootstrap is NO_BINDING_DECLARED / UNVERIFIED
  (never certified);
* a direct-save bypass (hand-edited self-certified provenance snapshot) is
  refused by ``leaderboard.save``, which recomputes the binding from the runtime
  filesystem instead of trusting the snapshot;
* a valid evaluator-produced fixture passes the full add_submission + save path.

All fixtures are self-contained tmp directories (manifest / checkpoints /
splits); no repository asset is touched. GPU is not required (hashlib byte
reads only).
"""
from __future__ import annotations

import json
import shutil

import pytest

from scoring import (add_submission, check_input_bound_provenance,
                     new_leaderboard, save)
from scoring.binding import check_input_binding, sha256_file
from scoring.task_spec import TASK_LABEL
from scoring.verify import PROTOCOL_ID, provenance_sha256

VALID_METHOD = "red_cnn"
VALID_VENDOR = "Siemens"
VALID_DOSE = "r025"
EV_VERSION = "ws4-eval/v1"


# ---------------------------------------------------------------------------
# Fixtures (all self-contained under tmp_path)
# ---------------------------------------------------------------------------

def _make_sources(root):
    """Create checkpoints / ASSET_MANIFEST.md / splits under ``root``.

    Returns the binding_context dict pointing at them and the checkpoint path.
    """
    ckpt_dir = root / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt = ckpt_dir / "red_cnn.pt"
    ckpt.write_bytes(b"fake-ckpt-bytes-v1" * 64)
    manifest = root / "ASSET_MANIFEST.md"
    manifest.write_text(
        "# ASSET MANIFEST\n\n"
        "| file | size | source | SHA256 |\n"
        "| --- | --- | --- | --- |\n"
        "| `red_cnn.pt` | 1.2G | checkpoints/ | `%s` |\n"
        % sha256_file(ckpt), encoding="utf-8")
    splits = root / "splits"
    splits.mkdir(parents=True, exist_ok=True)
    (splits / "split_assignment.csv").write_text(
        "patient_id,native_id,split,source,seed,canonical_key,series_id\n"
        "P01,n01,test,aapm,42,canon_p1,s1\n"
        "P02,n02,test,aapm,42,canon_p2,s2\n", encoding="utf-8")
    (splits / "aapm_test.txt").write_text("P01\nP02\n", encoding="utf-8")
    return {"checkpoint_dir": str(ckpt_dir),
            "manifest_path": str(manifest),
            "splits_dir": str(splits)}, ckpt


def _make_result(*, model_file="red_cnn.pt",
                 method_name=VALID_METHOD, vendor=VALID_VENDOR,
                 dose=VALID_DOSE, evaluator_version=EV_VERSION,
                 bootstrap=False, patient_source=True, patient_ids=None,
                 patient_map=None, data_manifest=None, weights_extra=None):
    """A valid paired result with an internally consistent claim/evidence."""
    weights = {"checkpoint": model_file, "framework": "torch", "sha": "abc123"}
    if weights_extra:
        weights.update(weights_extra)
    manifest = data_manifest if data_manifest is not None else {
        "patients": ["P01", "P02"], "dose_grid": ["r025"]}
    claim = {
        "task_id": TASK_LABEL,
        "protocol_id": PROTOCOL_ID,
        "data_manifest_sha256": provenance_sha256(manifest),
        "model_sha256": provenance_sha256(weights),
        "evaluator_version": evaluator_version,
        "method_name": method_name,
        "vendor": vendor,
        "dose": dose,
    }
    if bootstrap:
        claim["bootstrap_level"] = "patient"
    if patient_source:
        claim["patient_source"] = "split_assignment.csv"
    if patient_map is not None:
        claim["patient_map"] = patient_map
    result = {
        "validation": {
            "paired_methods": {
                method_name: {
                    "name": method_name,
                    "psnr_db": 32.1,
                    "ssim": 0.91,
                    "detectability": {
                        "task": TASK_LABEL,
                        "bander_roi": 0.72,
                        "cnr_mean": 1.2,
                        "cho_auc_mean": 0.85,
                        "npwe_mean": 5.0,
                        "bander_full": 0.70,
                        "roi_tm_auc": 0.80,
                    },
                }
            }
        },
        "claim": claim,
        "evidence": {"data_manifest": manifest, "model_weights": weights,
                     "evaluator_version": evaluator_version},
        "patient_ids": patient_ids if patient_ids is not None else ["P01", "P02"],
    }
    return result


def _binding_of(result, ctx, *, method=VALID_METHOD, vendor=VALID_VENDOR,
                dose=VALID_DOSE):
    return check_input_binding(result, method=method, vendor=vendor, dose=dose,
                               **ctx).to_dict()


def _entry_snapshot(entry):
    return entry["provenance"]["input_binding"]


# ---------------------------------------------------------------------------
# 1) Valid evaluator-produced fixture
# ---------------------------------------------------------------------------

def test_valid_fixture_passes_all_binding_classes(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True,
                          data_manifest={"patients": ["P01", "P02"],
                                         "dose_grid": ["r025"]})
    b = _binding_of(result, ctx)
    assert b["status"] == "PASS", b
    assert b["ok"] is True
    assert b["checks"]["model_bytes"] == "PASS"
    assert b["checks"]["asset_manifest"] == "PASS"
    assert b["checks"]["patient_mapping"] == "PASS"
    assert b["checks"]["identity"] == "PASS"
    assert b["violations"] == []


def test_valid_fixture_passes_through_add_and_save(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    board = new_leaderboard()
    entries = add_submission(board, result, method=VALID_METHOD,
                             vendor=VALID_VENDOR, dose=VALID_DOSE,
                             binding_context=ctx)
    assert len(entries) == 1
    assert _entry_snapshot(entries[0])["status"] == "PASS"
    out = tmp_path / "board.json"
    save(board, out, binding_context=ctx)   # save-time recompute keeps PASS
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["receipt"]["input_binding"]["pass"] >= 1
    assert saved["receipt"]["gate"]["check_submission_result"] == "ok"


# ---------------------------------------------------------------------------
# 2) Changed model bytes (attack: JSON claims model A, file is model B)
# ---------------------------------------------------------------------------

def test_changed_model_bytes_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    assert _binding_of(result, ctx)["status"] == "PASS"
    # The adversary rewrites the checkpoint bytes after the result was made.
    ckpt.write_bytes(b"TAMPERED-BYTES-DO-NOT-MATCH-MANIFEST")
    b = _binding_of(result, ctx)
    assert b["status"] == "FAIL", b
    assert b["checks"]["model_bytes"] == "FAIL"
    assert any("hash" in v.lower() or "mismatch" in v.lower()
               or "changed" in v.lower() or "bytes" in v.lower()
               for v in b["violations"]), b["violations"]


def test_changed_model_bytes_blocks_verify_path(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    ckpt.write_bytes(b"TAMPERED-BYTES-DO-NOT-MATCH-MANIFEST")
    bound = check_input_bound_provenance(result, method=VALID_METHOD,
                                         vendor=VALID_VENDOR, dose=VALID_DOSE,
                                         **ctx)
    assert bound["binding"]["status"] == "FAIL"
    assert bound["binding"]["violations"]


# ---------------------------------------------------------------------------
# 3) Changed manifest membership (attack: model not in ASSET_MANIFEST)
# ---------------------------------------------------------------------------

def test_changed_manifest_membership_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # Claim names a checkpoint that is not a member of the manifest.
    result = _make_result(model_file="ctformer.pt", bootstrap=True,
                          patient_source=True)
    b = _binding_of(result, ctx)
    assert b["status"] == "FAIL", b
    assert b["checks"]["model_bytes"] == "FAIL"
    assert any("not" in v.lower() and "manifest" in v.lower()
               for v in b["violations"]), b["violations"]


# ---------------------------------------------------------------------------
# 4) Placeholder manifest hash -> UNVERIFIED, never invented
# ---------------------------------------------------------------------------

def test_placeholder_manifest_hash_is_unverified_not_faked(tmp_path):
    root = tmp_path
    ckpt_dir = root / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt = ckpt_dir / "red_cnn.pt"
    ckpt.write_bytes(b"fake-ckpt-bytes-v1" * 64)
    manifest = root / "ASSET_MANIFEST.md"
    # ASSET_MANIFEST.SHA256 is the known empty placeholder ("-").
    manifest.write_text(
        "# ASSET MANIFEST\n\n"
        "| file | size | source | SHA256 |\n"
        "| --- | --- | --- | --- |\n"
        "| `red_cnn.pt` | 1.2G | checkpoints/ | - |\n", encoding="utf-8")
    splits = root / "splits"
    splits.mkdir(parents=True, exist_ok=True)
    (splits / "split_assignment.csv").write_text(
        "patient_id,native_id,split,source,seed,canonical_key,series_id\n"
        "P01,n01,test,aapm,42,canon_p1,s1\n"
        "P02,n02,test,aapm,42,canon_p2,s2\n", encoding="utf-8")
    (splits / "aapm_test.txt").write_text("P01\nP02\n", encoding="utf-8")
    ctx = {"checkpoint_dir": str(ckpt_dir), "manifest_path": str(manifest),
           "splits_dir": str(splits)}
    result = _make_result(bootstrap=True, patient_source=True)
    b = _binding_of(result, ctx)
    assert b["status"] == "UNVERIFIED", b
    assert b["ok"] is True          # not a hard rejection
    assert b["checks"]["asset_manifest"] == "UNVERIFIED"
    assert any("placeholder" in v.lower() or "unverified" in v.lower()
               for v in b["unverified"]), b["unverified"]
    # No hash value is invented: the manifest table cell was "-" and stays None.
    assert not any(b["checks"][k] == "PASS" and "fake" in b["details"].get(k, "")
                   for k in b["checks"])


# ---------------------------------------------------------------------------
# 5) Wrong method / task / dose identity binding
# ---------------------------------------------------------------------------

def test_wrong_method_binding_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    b = _binding_of(result, ctx, method="learn")     # context disagrees
    assert b["checks"]["identity"] == "FAIL"
    assert any("method" in v.lower() for v in b["violations"]), b["violations"]


def test_wrong_dose_binding_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    b = _binding_of(result, ctx, dose="r050")        # context disagrees
    assert b["checks"]["identity"] == "FAIL"
    assert any("dose" in v.lower() for v in b["violations"]), b["violations"]


def test_wrong_vendor_binding_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    b = _binding_of(result, ctx, vendor="GE")        # context disagrees
    assert b["checks"]["identity"] == "FAIL"
    assert any("vendor" in v.lower() for v in b["violations"]), b["violations"]


def test_mismatched_evaluator_version_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    result["evidence"]["evaluator_version"] = "ws4-eval/v999"
    b = _binding_of(result, ctx)
    assert b["checks"]["identity"] == "FAIL"
    assert any("evaluator" in v.lower() for v in b["violations"]), b["violations"]


# ---------------------------------------------------------------------------
# 6) Patient mapping binding
# ---------------------------------------------------------------------------

def test_patient_bootstrap_without_fixed_source_unverified(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=False)
    b = _binding_of(result, ctx)
    assert b["status"] == "UNVERIFIED", b
    assert b["checks"]["patient_mapping"] == "UNVERIFIED"
    assert any("no" in v.lower() and "source" in v.lower()
               for v in b["unverified"]), b["unverified"]


def test_patient_not_in_fixed_split_source_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True,
                          patient_ids=["P01", "P99"])   # P99 is not in the CSV
    b = _binding_of(result, ctx)
    assert b["status"] == "FAIL", b
    assert b["checks"]["patient_mapping"] == "FAIL"
    assert any("P99" in v or "not in" in v.lower()
               for v in b["violations"]), b["violations"]


def test_self_reported_patient_map_contradicts_fixed_source_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # CSV says canonical_key canon_p1 for P01; the JSON map claims patient_1.
    result = _make_result(bootstrap=True, patient_source=True,
                          patient_map={"P01": "patient_1", "P02": "patient_2"})
    b = _binding_of(result, ctx)
    assert b["checks"]["patient_mapping"] == "FAIL"
    assert any("source" in v.lower() or "contradict" in v.lower()
               for v in b["violations"]), b["violations"]


def test_no_bootstrap_declared_is_no_binding_unverified(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=False, patient_source=False)
    b = _binding_of(result, ctx)
    assert b["checks"]["patient_mapping"] == "UNVERIFIED"
    assert any("no_binding" in v.lower() or "no binding" in v.lower()
               for v in b["unverified"]), b["unverified"]


def test_patient_map_without_bootstrap_declared_is_no_binding(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # A self-reported map alone never establishes slice-to-patient binding.
    result = _make_result(bootstrap=False, patient_source=False,
                          patient_map={"P01": "patient_1"})
    b = _binding_of(result, ctx)
    assert b["checks"]["patient_mapping"] == "UNVERIFIED"


# ---------------------------------------------------------------------------
# 7) Direct-save bypass (hand-edited self-certified provenance snapshot)
# ---------------------------------------------------------------------------

def _board_with_forged_snapshot(ctx, *, status="PASS", ok=True):
    """Build a board whose entry provenance was NOT produced by add_submission:
    a forged, internally consistent claim plus a self-certified input_binding.
    """
    result = _make_result(bootstrap=True, patient_source=True)
    # Internally consistent claim/evidence snapshot.
    claim = result["claim"]
    evidence = result["evidence"]
    forged = {
        "id": "my-method",
        "method": VALID_METHOD,
        "vendor": VALID_VENDOR,
        "dose": VALID_DOSE,
        "metrics": {"psnr_db": 32.1, "ssim": 0.91, "cnr_mean": 1.2,
                    "cho_auc_mean": 0.85, "npwe_mean": 5.0,
                    "bander_roi": 0.72, "task": TASK_LABEL},
        "provenance": {
            "schema": "ws4-provenance-binding/v1",
            "claim": claim,
            "evidence": evidence,
            "claim_bound_sha256": provenance_sha256(claim),
            "patient_ids": ["P01", "P02"],
            "input_binding": {"status": status, "ok": ok,
                              "checks": {"model_bytes": "PASS",
                                         "asset_manifest": "PASS",
                                         "patient_mapping": "PASS",
                                         "identity": "PASS"},
                              "details": {}, "violations": [],
                              "unverified": []},
        },
    }
    board = new_leaderboard()
    board["entries"].insert(-1, forged)   # keep blur trap present
    return board


def test_direct_save_with_self_certified_snapshot_rejected(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # Tamper the file bytes so the forged "PASS" snapshot is contradicted.
    ckpt.write_bytes(b"TAMPERED-BYTES-DO-NOT-MATCH-MANIFEST")
    board = _board_with_forged_snapshot(ctx)
    out = tmp_path / "board.json"
    with pytest.raises(ValueError) as exc:
        save(board, out, binding_context=ctx)
    assert "runtime input binding contradicts" in str(exc.value)
    assert (tmp_path / "board.json.failed.json").is_file()


def test_direct_save_with_unverifiable_snapshot_downgraded(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # Bytes unchanged but the forged snapshot self-certifies a PASS that the
    # runtime can only recompute as PASS here; use a placeholder-manifest
    # variant so the recompute is UNVERIFIED (never certified).
    root = tmp_path / "placeholder"
    pctx, pckpt = _make_sources(root)
    # Replace the manifest hash cell with a placeholder.
    (root / "ASSET_MANIFEST.md").write_text(
        "# ASSET MANIFEST\n\n"
        "| file | size | source | SHA256 |\n"
        "| --- | --- | --- | --- |\n"
        "| `red_cnn.pt` | 1.2G | checkpoints/ | - |\n", encoding="utf-8")
    board = _board_with_forged_snapshot(pctx)
    out = tmp_path / "board.json"
    save(board, out, binding_context=pctx)   # recompute: UNVERIFIED, not certified
    saved = json.loads(out.read_text(encoding="utf-8"))
    forged_entry = [e for e in saved["entries"] if e["id"] == "my-method"][0]
    rb = forged_entry["provenance"]["input_binding"]
    assert rb["status"] == "UNVERIFIED", rb
    assert rb["checks"]["asset_manifest"] == "UNVERIFIED"
    assert rb["ok"] is True
    assert saved["receipt"]["input_binding"]["unverified"] >= 1


def test_direct_save_recomputes_after_submission_byte_change(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    result = _make_result(bootstrap=True, patient_source=True)
    board = new_leaderboard()
    add_submission(board, result, method=VALID_METHOD, vendor=VALID_VENDOR,
                   dose=VALID_DOSE, binding_context=ctx)
    # Bytes change between submission and save.
    ckpt.write_bytes(b"TAMPERED-AFTER-SUBMISSION")
    out = tmp_path / "board.json"
    with pytest.raises(ValueError) as exc:
        save(board, out, binding_context=ctx)
    assert "runtime input binding contradicts" in str(exc.value)


def test_save_without_binding_context_keeps_historical_entries(tmp_path):
    ctx, ckpt = _make_sources(tmp_path)
    # Seed-only board has no claim snapshots; save must not touch them.
    board = new_leaderboard()
    out = tmp_path / "board.json"
    save(board, out)                       # no binding_context, no claims
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["receipt"]["input_binding"]["entries"] == 0
