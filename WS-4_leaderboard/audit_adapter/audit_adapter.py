#!/usr/bin/env python3
"""Narrow audit adapter around the existing WS-4 evaluator (``scoring.cli``).

Usage::

    audit_adapter.py {read,verify,report} --input-root D --input F \\
        --output-root O [--timeout-s N]

``read`` hashes the input and records a receipt. ``verify`` runs the
existing ``scoring.cli validate --result F`` evaluator in a subprocess and
records its verdict. ``report`` re-reads the last recorded verdict. Every op
shares the same path-containment checks: ``F`` must resolve (with no
symlinks) to a regular file strictly inside ``D``, and ``O`` must not be a
symlink and must not resolve inside ``D`` or inside the evaluator's own tree
(``scoring/``). Operations accumulate their JSON receipts in ``O``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS4_ROOT = os.path.dirname(HERE)
SCORING_ROOT = os.path.join(WS4_ROOT, "scoring")

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_REFUSE = 2
EXIT_UNVERIFIED = 3


class Refuse(Exception):
    """Raised when the input/output paths fail a containment or symlink check."""


def _real(path: str) -> str:
    return os.path.realpath(path)


def _is_under_or_equal(path: str, root: str) -> bool:
    path = os.path.normpath(path)
    root = os.path.normpath(root)
    return path == root or path.startswith(root + os.sep)


def _is_strictly_under(path: str, root: str) -> bool:
    path = os.path.normpath(path)
    root = os.path.normpath(root)
    return path.startswith(root + os.sep)


def _validate_paths(input_root: str, input_path: str, output_root: str):
    """Refuse (raise ``Refuse``) before anything is written to ``output_root``."""
    if os.path.islink(input_path):
        raise Refuse("--input is a symlink")

    real_root = _real(input_root)
    real_input = _real(input_path)
    if not os.path.isfile(real_input):
        raise Refuse("--input does not resolve to a regular file")
    if not _is_strictly_under(real_input, real_root):
        raise Refuse("--input resolves outside --input-root")

    if os.path.islink(output_root):
        raise Refuse("--output-root is a symlink")

    real_output = _real(output_root)
    if _is_under_or_equal(real_output, real_root):
        raise Refuse("--output-root is inside --input-root")
    if _is_under_or_equal(real_output, _real(SCORING_ROOT)):
        raise Refuse("--output-root is inside the evaluator tree (scoring/)")

    return real_input, real_output


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(output_root: str, name: str, payload: dict) -> None:
    path = os.path.join(output_root, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def _op_read(real_input: str, real_output: str) -> int:
    digest = _sha256_file(real_input)
    _write_json(real_output, "read.json", {
        "op": "read",
        "verdict": "READ",
        "input_sha256": digest,
    })
    return EXIT_OK


def _evaluator_cmd(real_input: str):
    """Build the evaluator subprocess argv.

    Uses ``python -I -c '...'`` (never ``-m scoring.cli`` with cwd=output_root)
    so that ``output_root`` -- the evaluator's cwd -- never lands on
    ``sys.path``. ``-I`` (isolated mode) implies ``-P``, which stops Python
    from prepending cwd/'' to ``sys.path`` for ``-c`` code; only the real WS-4
    root (containing the real ``scoring`` package) is added, and only
    explicitly, at index 0.
    """
    code = (
        "import sys\n"
        f"sys.path.insert(0, {WS4_ROOT!r})\n"
        "from scoring.cli import main\n"
        f"sys.exit(main(['validate', '--result', {real_input!r}]))\n"
    )
    return [sys.executable, "-I", "-c", code]


class _EvalResult:
    def __init__(self, returncode, stdout, stderr, timed_out):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out


def _run_subprocess_with_timeout(cmd, cwd, timeout_s):
    """Run ``cmd`` with ``cwd``; on timeout, kill the whole process group.

    ``start_new_session=True`` makes the child the leader of a new process
    group, so a timeout can be enforced on the whole subtree it spawns (not
    just the direct child) via ``os.killpg``.
    """
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True)
    except OSError:
        return _EvalResult(None, "", "", False)

    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        return _EvalResult(proc.returncode, stdout, stderr, False)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate()
        return _EvalResult(proc.returncode, stdout, stderr, True)


def _has_reject_line(stdout: str) -> bool:
    return any(line.startswith("REJECT") for line in stdout.splitlines())


def _op_verify(real_input: str, real_output: str, timeout_s) -> int:
    digest = _sha256_file(real_input)
    cmd = _evaluator_cmd(real_input)
    result = _run_subprocess_with_timeout(cmd, real_output, timeout_s)

    if result.timed_out:
        verdict, exit_code = "UNVERIFIED", EXIT_UNVERIFIED
    elif result.returncode == 0:
        verdict, exit_code = "PASS", EXIT_OK
    elif result.returncode == 1 and _has_reject_line(result.stdout):
        verdict, exit_code = "FAIL", EXIT_FAIL
    else:
        verdict, exit_code = "UNVERIFIED", EXIT_UNVERIFIED

    _write_json(real_output, "verify.json", {
        "op": "verify",
        "verdict": verdict,
        "input_sha256": digest,
        "evaluator_exit": result.returncode,
    })
    return exit_code


def _op_report(real_output: str) -> int:
    verify_path = os.path.join(real_output, "verify.json")
    try:
        with open(verify_path, encoding="utf-8") as f:
            verify_payload = json.load(f)
    except (OSError, ValueError):
        verify_payload = {}

    _write_json(real_output, "report.json", {
        "op": "report",
        "verdict": verify_payload.get("verdict"),
        "input_sha256": verify_payload.get("input_sha256"),
    })
    return EXIT_OK


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="audit_adapter.py")
    p.add_argument("op", choices=("read", "verify", "report"))
    p.add_argument("--input-root", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--timeout-s", type=float, default=None)
    return p


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        real_input, real_output = _validate_paths(
            args.input_root, args.input, args.output_root)
    except Refuse:
        return EXIT_REFUSE

    # Created up front: `verify` needs it to exist before it can be the
    # evaluator subprocess's cwd.
    os.makedirs(real_output, exist_ok=True)

    if args.op == "read":
        return _op_read(real_input, real_output)
    if args.op == "verify":
        return _op_verify(real_input, real_output, args.timeout_s)
    return _op_report(real_output)


if __name__ == "__main__":
    sys.exit(main())
