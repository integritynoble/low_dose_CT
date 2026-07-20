"""``pwm-audit`` — shell entry point for :func:`audit_credential`.

A reviewer / regulator with the credential JSON file and Python installed can
run the internal-consistency audit from the shell without writing any code::

    pwm-audit credential.json            # human-readable summary
    pwm-audit credential.json --json     # machine-readable JSON report
    cat credential.json | pwm-audit -    # read from stdin

Exit codes::

    0   audit ok (CredentialAudit.ok is True)
    1   audit found hard issues (schema/verdict/CI problem)
    2   I/O or argument error

The CLI does not re-run the bootstrap. Full reproduction is the job of
``paper_draft/reproduction_guide.md``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import IO

from pwm_dose_equivalence import __version__
from pwm_dose_equivalence.audit import CredentialAudit, audit_credential


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pwm-audit",
        description=(
            "Audit a published signal-equivalence credential's internal "
            "consistency. Does not re-run the bootstrap; for full reproduction "
            "see paper_draft/reproduction_guide.md."
        ),
    )
    parser.add_argument(
        "credential",
        help="Path to a credential JSON file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the CredentialAudit report as JSON to stdout.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pwm-audit (pwm_dose_equivalence {__version__})",
    )
    return parser


def _read_input(path: str, stdin: IO[str]) -> str:
    if path == "-":
        return stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _format_human(report: CredentialAudit) -> str:
    lines: list[str] = []
    status = "OK" if report.ok else "FAIL"
    lines.append(f"pwm-audit: {status}")
    lines.append("")
    lines.append("Hard checks:")
    lines.append(f"  schema_valid             = {report.schema_valid}")
    lines.append(f"  verdict_self_consistent  = {report.verdict_self_consistent}")
    lines.append("Soft signals:")
    lines.append(f"  framework_hash_known     = {report.framework_hash_known}")
    lines.append(f"  sample_size_check_ok     = {report.sample_size_check_ok}")
    lines.append("")
    if report.issues:
        lines.append(f"Issues ({len(report.issues)}):")
        for issue in report.issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("Issues: none")
    lines.append("")
    if report.warnings:
        lines.append(f"Warnings ({len(report.warnings)}):")
        for warning in report.warnings:
            lines.append(f"  - {warning}")
    else:
        lines.append("Warnings: none")
    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
    *,
    stdin: IO[str] | None = None,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
) -> int:
    """Console entry point. Returns an exit code (0 ok / 1 fail / 2 error)."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        raw = _read_input(args.credential, stdin)
    except OSError as exc:
        print(f"pwm-audit: cannot read {args.credential}: {exc}", file=stderr)
        return 2

    report = audit_credential(raw)

    if args.json:
        print(json.dumps(dataclasses.asdict(report), indent=2), file=stdout)
    else:
        print(_format_human(report), file=stdout)

    return 0 if report.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
