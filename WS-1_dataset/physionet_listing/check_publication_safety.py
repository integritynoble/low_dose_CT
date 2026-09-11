#!/usr/bin/env python3
"""Refuse to publish this repository while DUA-restricted data is reachable.

Gates Step 6 of ``deposit_procedure.md`` (make the repository public). The
deposit excludes the AAPM/Mayo DICOM and their DUA-restricted pixel derivatives;
publishing the repository would release them just as effectively as depositing
them would, and Step 3 forbids an embargo, so this has to hold at the moment the
repository goes public.

    python3 check_publication_safety.py              # tracked files (fast)
    python3 check_publication_safety.py --history    # every commit, every ref
    python3 check_publication_safety.py --json       # machine-readable

Exit 0 = safe to publish. Exit 1 = restricted paths found. Exit 2 = could not
check (not a git repository, git unavailable).

Why ``--history`` exists
------------------------
On 2026-09-05 eight Mayo-derived ``L506_*.npy`` files were removed from the
working tree of this repository, and were still fully reachable in every clone
and on the hosting side, because deleting a file in a new commit does not remove
it from the commits that already contain it. It took a ``git filter-repo``
rewrite to actually remove them. A tree-only check would have reported "clean"
the entire time and been wrong in the way that matters.

So the tree scan is the fast gate for everyday use, and ``--history`` is the one
that must pass before the repository is made public. They answer different
questions and only the second one is about publication.

What this does not check
------------------------
Third-party licensing (a vendored dependency shipping no LICENSE, or
redistributed pretrained weights) is the other half of the publication decision
and is not automated here; see ``DIRECTOR_DECISIONS.md`` 2.3.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
# Default to the repository this script lives in; --repo overrides so the gate
# can be pointed at any checkout (and so it is testable against a fixture).
DEFAULT_REPO = os.path.dirname(os.path.dirname(HERE))

# The restricted patterns live in stage_deposit.py so the deposit gate and the
# publication gate cannot drift apart.
sys.path.insert(0, HERE)
try:
    from stage_deposit import RESTRICTED, restricted_reason  # noqa: E402
except ImportError as exc:  # pragma: no cover
    print(f"error: cannot import the restricted-path rules from stage_deposit.py: {exc}",
          file=sys.stderr)
    sys.exit(2)


REPO = DEFAULT_REPO  # rebound from --repo in main()


def git(*args: str) -> str:
    return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                          text=True, check=True).stdout


def scan_tracked() -> List[Tuple[str, str]]:
    """Restricted paths among files tracked at HEAD."""
    out = []
    for rel in git("ls-files").splitlines():
        why = restricted_reason(rel)
        if why:
            out.append((rel, why))
    return out


def scan_history() -> List[Tuple[str, str]]:
    """Restricted paths reachable from ANY ref, in any commit.

    This is the check that matters before publication: a path removed from the
    tree is still served to anyone who clones, until history is rewritten.
    """
    seen: Dict[str, str] = {}
    # --all covers every local and remote-tracking ref; --objects lists the path
    # each blob was stored under.
    for line in git("rev-list", "--all", "--objects").splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        rel = parts[1]
        if rel in seen:
            continue
        why = restricted_reason(rel)
        if why:
            seen[rel] = why
    return sorted(seen.items())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", action="store_true",
                    help="scan every commit on every ref, not just tracked files "
                         "(required before making the repository public)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--repo", default=DEFAULT_REPO,
                    help="repository to check (default: the one this script lives in)")
    args = ap.parse_args()

    global REPO
    REPO = os.path.abspath(args.repo)

    try:
        git("rev-parse", "--git-dir")
    except Exception as exc:
        print(f"error: not a git repository or git unavailable: {exc}", file=sys.stderr)
        return 2

    mode = "history" if args.history else "tracked"
    findings = scan_history() if args.history else scan_tracked()

    if args.json:
        print(json.dumps({
            "mode": mode,
            "safe_to_publish": not findings,
            "n_findings": len(findings),
            "findings": [{"path": p, "reason": w} for p, w in findings],
            "patterns_checked": [p.pattern for p, _ in RESTRICTED],
        }, indent=2))
        return 1 if findings else 0

    if findings:
        print(f"NOT SAFE TO PUBLISH — {len(findings)} DUA-restricted path(s) "
              f"reachable ({mode} scan):\n", file=sys.stderr)
        for rel, why in findings:
            print(f"  {rel}\n      -> {why}", file=sys.stderr)
        if mode == "history":
            print("\nThese are reachable in history. Removing them in a new commit is "
                  "NOT enough -- every clone still serves them. Removing them for real "
                  "means a git filter-repo rewrite and a force push, after which every "
                  "collaborator must re-clone. See HEYANG_RECLONE_2026-09-05.md.",
                  file=sys.stderr)
        else:
            print("\nThis was a tracked-files scan only. Re-run with --history before "
                  "publishing: a path deleted from the tree is still served from "
                  "history.", file=sys.stderr)
        return 1

    if mode == "tracked":
        print("tracked files: clean. Run --history before publishing.")
    else:
        print("history: clean on every ref. No DUA-restricted path is reachable.")
        print("\nNote: this repository's own history is clean, but two things live "
              "outside it --\n"
              "  - the hosting side may retain unreachable objects until its own GC;\n"
              "  - any clone taken before a rewrite still holds them until re-cloned.\n"
              "Neither is visible from here. See DIRECTOR_DECISIONS.md 2.3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
