"""The publication gate must catch the case that actually happened.

On 2026-09-05 eight Mayo-derived ``L506_*.npy`` files were deleted from this
repository's working tree and remained fully reachable in history, in every
clone and on the hosting side, until a ``git filter-repo`` rewrite removed them.
A tree-only check reports "clean" throughout that window.

These tests pin both halves: the gate must pass on a clean repository (or it is
useless), and it must fail on a repository where a restricted path survives only
in history (or it is worse than useless, because it certifies the exact state
that was wrong).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_publication_safety.py")
REPO = os.path.dirname(os.path.dirname(HERE))


def run(*args, repo=None):
    """Invoke the gate against *repo* (default: this repository).

    The gate takes --repo rather than inferring the repository from the working
    directory; passing cwd alone would silently scan the wrong tree.
    """
    return subprocess.run([sys.executable, CHECK, "--repo", repo or REPO, *args],
                          capture_output=True, text=True)


# --------------------------------------------------------------- this repo
def test_this_repository_is_clean_tracked():
    """The gate opens: this repository passes the tracked scan."""
    r = run()
    assert r.returncode == 0, f"tracked scan failed unexpectedly:\n{r.stderr}"


def test_this_repository_is_clean_in_history():
    """The 2026-09-05 rewrite held: no restricted path is reachable on any ref."""
    r = run("--history")
    assert r.returncode == 0, (
        "a DUA-restricted path is reachable in history -- publication is unsafe:\n"
        + r.stderr)


def test_json_mode_is_machine_readable():
    r = run("--json")
    payload = json.loads(r.stdout)
    assert payload["safe_to_publish"] is True
    assert payload["n_findings"] == 0
    assert payload["patterns_checked"], "no restricted patterns are being applied"


# ------------------------------------------------- the case that happened
@pytest.fixture
def repo_with_restricted_file_in_history(tmp_path):
    """A repo where a restricted file was added, then deleted from the tree.

    This is the 2026-09-05 shape exactly: HEAD is clean, history is not.
    """
    root = tmp_path / "repo"
    (root / "data").mkdir(parents=True)
    listing = root / "WS-1_dataset" / "physionet_listing"
    listing.mkdir(parents=True)
    for fn in ("stage_deposit.py", "check_publication_safety.py"):
        (listing / fn).write_bytes((open(os.path.join(HERE, fn), "rb")).read())

    def g(*a):
        subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)

    g("init", "-q", ".")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (root / "data" / "L506_167_input.npy").write_text("pixel")
    g("add", "-A")
    g("commit", "-qm", "introduces the restricted file")
    g("rm", "-q", "data/L506_167_input.npy")
    g("commit", "-qm", "remove it from the tree")
    return root


def test_tracked_scan_alone_would_have_missed_it(repo_with_restricted_file_in_history):
    """Documents the trap: the fast scan calls the bad state clean.

    This is not a defect in the tracked scan -- it answers a different question.
    It is why --history is mandatory before publishing, and why this test exists
    beside the next one rather than instead of it.
    """
    r = run(repo=str(repo_with_restricted_file_in_history))
    assert r.returncode == 0, "expected the tracked scan to see a clean HEAD"


def test_history_scan_catches_it(repo_with_restricted_file_in_history):
    """The gate closes: a path surviving only in history is refused."""
    r = run("--history", repo=str(repo_with_restricted_file_in_history))
    assert r.returncode == 1, (
        "the history scan passed a repository that still serves a restricted "
        "file -- this is the 2026-09-05 failure, uncaught")
    assert "L506_167_input.npy" in r.stderr
    assert "filter-repo" in r.stderr, "should say what actually removes it"


def test_history_scan_json_reports_the_finding(repo_with_restricted_file_in_history):
    r = run("--history", "--json", repo=str(repo_with_restricted_file_in_history))
    payload = json.loads(r.stdout)
    assert payload["safe_to_publish"] is False
    assert payload["n_findings"] == 1
    assert payload["findings"][0]["path"].endswith("L506_167_input.npy")
