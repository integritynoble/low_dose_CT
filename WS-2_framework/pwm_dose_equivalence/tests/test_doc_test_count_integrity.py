"""Drift guard for test-count claims in the developer / reviewer docs.

Issue #21 (2026-09-08 review round): CONTRIBUTING.md and
reproduction_guide.md both document the result of ``pytest`` in this
repository, but the two printed numbers (139 and 81) disagreed with each
other and neither matched a fresh run.  This guard re-collects the suite
(collect-only, no execution) and asserts that every ``expect: N passed``
comment on a ``pytest`` command line equals the collected count.

If you deliberately add or remove tests, update those doc strings first so
this test passes again.  Do not delete the assertion: that is the exact
regression the reviewer complained about.

CHANGELOG.md in ../paper_draft is a per-commit historical log (its
"140 / 140 passed" line records the state at that commit, not the current
suite), so it is intentionally not covered by this guard.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]          # pwm_dose_equivalence
PAPER_DRAFT_DIR = PACKAGE_DIR.parent / "paper_draft"      # reproduction_guide.md
SRC_DIR = PACKAGE_DIR / "src"

EXPECT_RE = re.compile(r"pytest\s+# expect:\s*(\d+)\s+passed")
PER_FILE_RE = re.compile(r"^.*:\s*(\d+)\s*$")

# Documents whose "expect: N passed" lines are covered by this guard.
DOCUMENTS = [
    PACKAGE_DIR / "CONTRIBUTING.md",
    PAPER_DRAFT_DIR / "reproduction_guide.md",
]


def _collect_count() -> int:
    """Return the number of tests pytest collects for this suite (no run)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_DIR)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "--no-header", "-p", "no:cacheprovider"],
        cwd=str(PACKAGE_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"collect-only failed (rc={proc.returncode}):\n{proc.stderr}"
        )
    total = 0
    for line in (proc.stdout or "").splitlines():
        m = PER_FILE_RE.match(line.strip())
        if m:
            total += int(m.group(1))
    if total == 0:
        raise AssertionError(
            f"could not parse any collected count from:\n{proc.stdout}"
        )
    return total


def _documented_expectations() -> dict[Path, list[int]]:
    found: dict[Path, list[int]] = {}
    for doc in DOCUMENTS:
        text = doc.read_text(encoding="utf-8")
        found[doc] = [int(n) for n in EXPECT_RE.findall(text)]
    return found


def test_documented_pytest_counts_match_fresh_collection() -> None:
    collected = _collect_count()
    for doc, expectations in _documented_expectations().items():
        rel = doc.relative_to(PACKAGE_DIR.parent)
        assert expectations, f"{rel}: no 'pytest  # expect: N passed' line found"
        for n in expectations:
            assert n == collected, (
                f"{rel} claims {n} passed but a fresh collection yields "
                f"{collected}. If this is deliberate, update the doc string "
                "before committing; otherwise fix the drift."
            )


def test_documented_pytest_counts_are_consistent_across_docs() -> None:
    values = {tuple(v) for v in _documented_expectations().values()}
    assert len(values) == 1, (
        "docs disagree on the expected pytest count: "
        f"{ {str(k.relative_to(PACKAGE_DIR.parent)): v for k, v in _documented_expectations().items()} }"
    )
