"""Task 3 (2026-09-21): publication-state visibility.

Fixtures live in ``tests/fixtures/publication/`` and cover the six acceptance
cases from HEYANG_NEXT_2026-09-20.md task 3:

  * missing status            -> no_status.json            (NO_CLAIM)
  * pending                   -> pending.json              (INCOMPLETE)
  * missing strata            -> missing_strata.json       (MISSING_LAYER)
  * failed gates              -> failed_gate.json          (REJECTED via .failed.json)
  * skipped live execution    -> runbundle_skipped_live/   (INCOMPLETE, S3 SKIPPED)
  * valid publication         -> published.json            (PUBLISHED, referee-verified)

Hard constraint under test: no pending / skipped / BLOCKED / submitter-flagged
item may ever be labeled verified or published; ``published`` is only True for
a referee-verified PUBLISHED state (``unverified_flag.json`` is the adverse
case: status says "published" but no referee evidence is attached).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scoring.cli import main as cli_main  # noqa: E402
from scoring.verifier import (  # noqa: E402
    PUBLISH_INCOMPLETE, PUBLISH_MISSING_LAYER, PUBLISH_NO_CLAIM,
    PUBLISH_PUBLISHED, PUBLISH_REJECTED,
    board_publication_status, entry_publication_status,
    verdict_publication_status, verify_runbundle)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "publication"
BOARD_FIXTURES = [
    "no_status.json", "pending.json", "missing_strata.json", "rejected.json",
    "failed_gate.json", "published.json", "unverified_flag.json",
]


def _board(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Board-level five-state classification
# ---------------------------------------------------------------------------

def test_missing_status_is_no_claim():
    st = board_publication_status(_board("no_status.json"))
    assert st.state == PUBLISH_NO_CLAIM
    assert st.published is False and st.verified is False


def test_pending_is_incomplete_not_published():
    st = board_publication_status(_board("pending.json"))
    assert st.state == PUBLISH_INCOMPLETE
    assert "pending" in st.detail.lower()
    assert st.published is False and st.verified is False


def test_missing_strata_is_missing_layer():
    st = board_publication_status(_board("missing_strata.json"))
    assert st.state == PUBLISH_MISSING_LAYER
    assert st.published is False and st.verified is False


def test_rejected_is_rejected():
    st = board_publication_status(_board("rejected.json"))
    assert st.state == PUBLISH_REJECTED
    assert st.published is False and st.verified is False


def test_failed_gate_diagnostic_is_rejected():
    # save() refused the board and wrote <path>.failed.json beside it.
    st = board_publication_status(_board("failed_gate.json"),
                                  board_path=FIXTURES / "failed_gate.json")
    assert st.state == PUBLISH_REJECTED
    assert st.published is False and st.verified is False


def test_receipt_gate_failure_is_rejected():
    board = _board("pending.json")
    board["receipt"]["gate"]["trap_rank"] = "FAIL"
    st = board_publication_status(board)
    assert st.state == PUBLISH_REJECTED
    assert st.published is False


def test_valid_publication_is_published_with_referee_evidence():
    st = board_publication_status(_board("published.json"))
    assert st.state == PUBLISH_PUBLISHED
    assert st.published is True and st.verified is True
    assert st.evidence is not None and st.evidence.get("referee")


def test_submitter_flag_without_referee_evidence_is_not_published():
    # Adverse case: status says "published" but the flag is submitter-controlled.
    st = board_publication_status(_board("unverified_flag.json"))
    assert st.state == PUBLISH_INCOMPLETE
    assert st.published is False and st.verified is False
    assert "not" in st.detail.lower()


def test_hard_constraint_nothing_nonpublished_is_published_or_verified():
    for name in BOARD_FIXTURES:
        board = _board(name)
        st = board_publication_status(board, board_path=FIXTURES / name)
        if st.state != PUBLISH_PUBLISHED:
            assert st.published is False, name
            assert st.verified is False, name


# ---------------------------------------------------------------------------
# Entry-level states
# ---------------------------------------------------------------------------

def test_entry_states_follow_board():
    board = _board("pending.json")
    st = board_publication_status(board)
    trap = entry_publication_status(
        next(e for e in board["entries"] if e.get("trap")), board_state=st)
    assert trap.state == PUBLISH_NO_CLAIM and trap.published is False
    placeholder = entry_publication_status(
        next(e for e in board["entries"] if e.get("placeholder")), board_state=st)
    assert placeholder.state == PUBLISH_NO_CLAIM and placeholder.published is False
    submission = entry_publication_status(
        {"id": "sub-1-x", "method": "x", "kind": "submission"}, board_state=st)
    assert submission.state == st.state
    assert submission.published is False  # board is pending


def test_entry_requires_board_state():
    st = entry_publication_status({"id": "sub-1-x", "kind": "submission"})
    assert st.state == PUBLISH_NO_CLAIM and st.published is False


# ---------------------------------------------------------------------------
# RunBundle verdict states (S1-S4 pipeline)
# ---------------------------------------------------------------------------

def test_skipped_live_execution_is_incomplete_not_verified():
    verdict = verify_runbundle(FIXTURES / "runbundle_skipped_live",
                               live_result=None, run_ws1_gates=False)
    assert "S3" in verdict.skipped
    st = verdict_publication_status(verdict)
    assert st.state == PUBLISH_INCOMPLETE
    assert st.published is False and st.verified is False
    assert "skipped" in st.detail.lower()


def test_verdict_violation_is_rejected():
    bad = FIXTURES / "runbundle_bad_structure"
    bad.mkdir(exist_ok=True)
    (bad / "method.json").write_text("not json", encoding="utf-8")
    (bad / "results.json").write_text("{}", encoding="utf-8")
    verdict = verify_runbundle(bad, run_ws1_gates=False)
    st = verdict_publication_status(verdict)
    assert st.state == PUBLISH_REJECTED
    assert st.published is False and st.verified is False


def test_passing_verdict_is_not_published():
    # S1-S4 pass means *publishable*, never published without a board save +
    # referee evidence.
    with (FIXTURES / "runbundle_skipped_live" / "results.json").open(encoding="utf-8") as f:
        live = json.load(f)
    verdict = verify_runbundle(FIXTURES / "runbundle_skipped_live",
                               live_result=live, run_ws1_gates=False)
    assert "S3" not in verdict.skipped
    assert not any(verdict.violations.values())
    st = verdict_publication_status(verdict)
    assert st.state == PUBLISH_INCOMPLETE
    assert st.published is False and st.verified is False


# ---------------------------------------------------------------------------
# CLI integration: `python -m scoring.cli publication-status`
# ---------------------------------------------------------------------------

def _cli_publication_status(*argv):
    out, err, rc = [], [], None
    import io
    from contextlib import redirect_stdout, redirect_stderr
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli_main(["publication-status", *argv])
    return rc, buf_out.getvalue(), buf_err.getvalue()


@pytest.mark.parametrize("name,expected", [
    ("no_status.json", PUBLISH_NO_CLAIM),
    ("pending.json", PUBLISH_INCOMPLETE),
    ("missing_strata.json", PUBLISH_MISSING_LAYER),
    ("rejected.json", PUBLISH_REJECTED),
    ("failed_gate.json", PUBLISH_REJECTED),
    ("published.json", PUBLISH_PUBLISHED),
    ("unverified_flag.json", PUBLISH_INCOMPLETE),
])
def test_cli_board_states(name, expected):
    rc, out, err = _cli_publication_status("--leaderboard", str(FIXTURES / name),
                                           "--json")
    assert rc == 0, (out, err)
    payload = json.loads(out)
    assert payload["state"] == expected, name
    assert payload["kind"] == "leaderboard"


def test_cli_board_hard_constraint():
    for name in BOARD_FIXTURES:
        rc, out, err = _cli_publication_status(
            "--leaderboard", str(FIXTURES / name), "--json")
        assert rc == 0, name
        payload = json.loads(out)
        if payload["state"] != PUBLISH_PUBLISHED:
            assert payload["published"] is False, name
            assert payload["verified"] is False, name
            for e in payload["entries"]:
                assert e["published"] is False, (name, e)


def test_cli_bundle_skipped_live():
    rc, out, err = _cli_publication_status(
        "--bundle", str(FIXTURES / "runbundle_skipped_live"),
        "--skip-ws1-gates", "--json")
    assert rc == 0, (out, err)
    payload = json.loads(out)
    assert payload["state"] == PUBLISH_INCOMPLETE
    assert payload["published"] is False and payload["verified"] is False
    assert payload["stages"]["S3"] == "SKIPPED"
