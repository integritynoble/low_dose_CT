"""Capture expected ``pwm-audit`` output for every example credential.

Runs ``pwm-audit`` (via the in-process :func:`pwm_dose_equivalence.cli.main`
function so output is deterministic) on each JSON file under
``examples/`` and writes the concatenated human-readable output to
``examples/expected_audit_output.txt``.

A reviewer can confirm bit-identical behaviour by re-running this script
and diffing the result against the committed file. The companion test
``tests/test_examples.py::test_expected_audit_output_matches_snapshot``
runs the same comparison automatically.

Run::

    python3 examples/regenerate_expected_outputs.py
"""

from __future__ import annotations

import io
from pathlib import Path

from pwm_dose_equivalence.cli import main

HERE = Path(__file__).parent
SNAPSHOT = HERE / "expected_audit_output.txt"

#: Order in which examples are concatenated into the snapshot. Stable so
#: the file diffs cleanly when an example is edited; new examples should
#: be appended to the end.
EXAMPLE_ORDER: tuple[Path, ...] = (
    HERE / "valid_ct_lung_nodule.json",
    HERE / "failures" / "tampered_verdict.json",
    HERE / "failures" / "inverted_ci.json",
    HERE / "failures" / "missing_field.json",
    HERE / "failures" / "unknown_framework_hash.json",
    HERE / "failures" / "undersized_pass.json",
    HERE / "failures" / "bca_headline.json",
)


def _run_audit(path: Path) -> tuple[int, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main([str(path)], stdin=io.StringIO(""), stdout=stdout, stderr=stderr)
    return code, stdout.getvalue()


def regenerate() -> str:
    parts: list[str] = [
        "# Expected pwm-audit output on every example credential.",
        "#",
        "# Regenerate with: python3 examples/regenerate_expected_outputs.py",
        "# Drift detected by: tests/test_examples.py",
        "",
    ]
    for path in EXAMPLE_ORDER:
        rel = path.relative_to(HERE)
        code, out = _run_audit(path)
        parts.append(f"=== {rel} (exit={code}) ===")
        parts.append(out.rstrip())
        parts.append("")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":  # pragma: no cover
    SNAPSHOT.write_text(regenerate(), encoding="utf-8")
    print(f"Wrote {SNAPSHOT} ({len(EXAMPLE_ORDER)} examples).")
