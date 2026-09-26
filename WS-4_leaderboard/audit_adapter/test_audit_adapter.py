"""Unit tests for the WS-4 audit adapter (LDCT-03: rebuild of 90-069 + 90-081 fix).

Stdlib-only (unittest). A mix of black-box tests (drive ``audit_adapter.py``
as a subprocess, exactly as the acceptance check does) and a couple of
white-box tests (import the module directly to exercise the timeout/kill
path without waiting on the real evaluator, and to patch the evaluator
command deterministically).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
WS4_ROOT = os.path.dirname(HERE)
ADAPTER = os.path.join(HERE, "audit_adapter.py")
SCORING_ROOT = os.path.join(WS4_ROOT, "scoring")
FIXTURES = os.path.join(SCORING_ROOT, "tests", "fixtures", "s2_gates")

sys.path.insert(0, HERE)
import audit_adapter  # noqa: E402  (whitebox import, after sys.path setup)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _run(op, input_root, input_path, output_root, timeout_s="60"):
    cmd = [sys.executable, "-B", ADAPTER, op,
           "--input-root", input_root, "--input", input_path,
           "--output-root", output_root]
    if timeout_s is not None:
        cmd += ["--timeout-s", str(timeout_s)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def _read_json(output_root, op):
    with open(os.path.join(output_root, op + ".json"), encoding="utf-8") as f:
        return json.load(f)


class AuditAdapterTestCase(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="audit_adapter_test-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

        self.input_root = os.path.join(self.base, "in")
        os.mkdir(self.input_root)
        self.outside = os.path.join(self.base, "outside")
        os.mkdir(self.outside)

        self.valid = os.path.join(self.input_root, "valid.json")
        shutil.copy(os.path.join(FIXTURES, "provenance_valid.json"), self.valid)
        self.invalid = os.path.join(self.input_root, "invalid.json")
        shutil.copy(os.path.join(FIXTURES, "strata_empty.json"), self.invalid)
        self.broken = os.path.join(self.input_root, "broken.json")
        with open(self.broken, "w", encoding="utf-8") as f:
            f.write("{not json")

        self.out_valid = os.path.join(self.outside, "valid.json")
        shutil.copy(self.valid, self.out_valid)

    def _out(self, name):
        return os.path.join(self.base, "out_" + name)

    # -- read ---------------------------------------------------------

    def test_read_writes_receipt_with_sha256_and_verdict(self):
        o = self._out("read")
        proc = _run("read", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 0)
        payload = _read_json(o, "read")
        self.assertEqual(payload["op"], "read")
        self.assertEqual(payload["verdict"], "READ")
        self.assertEqual(payload["input_sha256"], _sha256(self.valid))

    # -- verify ---------------------------------------------------------

    def test_verify_valid_input_is_pass_exit0(self):
        o = self._out("pass")
        proc = _run("verify", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 0)
        payload = _read_json(o, "verify")
        self.assertEqual(payload["verdict"], "PASS")
        self.assertEqual(payload["input_sha256"], _sha256(self.valid))
        self.assertEqual(payload["evaluator_exit"], 0)

    def test_verify_gate_failure_is_fail_exit1_with_reject(self):
        o = self._out("fail")
        proc = _run("verify", self.input_root, self.invalid, o)
        self.assertEqual(proc.returncode, 1)
        payload = _read_json(o, "verify")
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertEqual(payload["evaluator_exit"], 1)

    def test_verify_malformed_json_is_unverified_not_fail_exit3(self):
        o = self._out("unver")
        proc = _run("verify", self.input_root, self.broken, o)
        self.assertEqual(proc.returncode, 3)
        payload = _read_json(o, "verify")
        self.assertEqual(payload["verdict"], "UNVERIFIED")
        self.assertNotEqual(payload["evaluator_exit"], 0)

    def test_evaluator_exit_code_recorded_in_verify_json(self):
        o_pass = self._out("exit_pass")
        _run("verify", self.input_root, self.valid, o_pass)
        self.assertEqual(_read_json(o_pass, "verify")["evaluator_exit"], 0)

        o_fail = self._out("exit_fail")
        _run("verify", self.input_root, self.invalid, o_fail)
        self.assertEqual(_read_json(o_fail, "verify")["evaluator_exit"], 1)

    # -- report ---------------------------------------------------------

    def test_report_reflects_prior_verify_verdict(self):
        o = self._out("report_after_pass")
        _run("verify", self.input_root, self.valid, o)
        proc = _run("report", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 0)
        payload = _read_json(o, "report")
        self.assertEqual(payload["op"], "report")
        self.assertEqual(payload["verdict"], "PASS")
        self.assertEqual(payload["input_sha256"], _sha256(self.valid))

    def test_report_always_exits_0_even_without_prior_verify(self):
        o = self._out("report_first")
        proc = _run("report", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 0)
        payload = _read_json(o, "report")
        self.assertEqual(payload["op"], "report")
        self.assertIsNone(payload["verdict"])

    def test_output_root_accumulates_receipts_across_ops(self):
        o = self._out("accumulate")
        _run("read", self.input_root, self.valid, o)
        _run("verify", self.input_root, self.valid, o)
        _run("report", self.input_root, self.valid, o)
        self.assertTrue(os.path.isfile(os.path.join(o, "read.json")))
        self.assertTrue(os.path.isfile(os.path.join(o, "verify.json")))
        self.assertTrue(os.path.isfile(os.path.join(o, "report.json")))

    # -- refusals (exit 2, nothing written) ------------------------------

    def _assert_refused(self, o):
        self.assertFalse(os.path.isdir(o) and os.listdir(o))

    def test_refuse_input_outside_input_root_exit2_writes_nothing(self):
        o = self._out("outside_root")
        proc = _run("verify", self.input_root, self.out_valid, o)
        self.assertEqual(proc.returncode, 2)
        self._assert_refused(o)

    def test_refuse_dotdot_escape_outside_input_root_exit2(self):
        o = self._out("dotdot")
        escaped = os.path.join(self.input_root, "..", "outside", "valid.json")
        proc = _run("verify", self.input_root, escaped, o)
        self.assertEqual(proc.returncode, 2)
        self._assert_refused(o)

    def test_refuse_symlink_input_pointing_outside_root_exit2(self):
        link = os.path.join(self.input_root, "link_outside.json")
        os.symlink(self.out_valid, link)
        o = self._out("symlink_outside")
        proc = _run("verify", self.input_root, link, o)
        self.assertEqual(proc.returncode, 2)
        self._assert_refused(o)

    def test_refuse_symlink_input_even_when_target_is_inside_root(self):
        target = os.path.join(self.input_root, "real_target.json")
        shutil.copy(self.valid, target)
        link = os.path.join(self.input_root, "symlink_inside.json")
        os.symlink(target, link)
        o = self._out("symlink_inside")
        proc = _run("verify", self.input_root, link, o)
        self.assertEqual(proc.returncode, 2)
        self._assert_refused(o)

    def test_refuse_output_root_nested_inside_input_root_exit2(self):
        o = os.path.join(self.input_root, "nested_out")
        proc = _run("verify", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(os.path.exists(o))

    def test_refuse_output_root_is_symlink_exit2(self):
        real_dir = os.path.join(self.base, "real_output_dir")
        os.mkdir(real_dir)
        o = os.path.join(self.base, "symlinked_output")
        os.symlink(real_dir, o)
        proc = _run("verify", self.input_root, self.valid, o)
        self.assertEqual(proc.returncode, 2)
        # Nothing new written through the symlink into the real target dir.
        self.assertEqual(os.listdir(real_dir), [])

    def test_refuse_output_root_inside_scoring_tree_exit2(self):
        o = os.path.join(SCORING_ROOT, "audit_adapter_test_scratch")
        self.assertFalse(os.path.exists(o))
        try:
            proc = _run("verify", self.input_root, self.valid, o)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(os.path.exists(o))
        finally:
            shutil.rmtree(o, ignore_errors=True)

    # -- 90-081: evaluator cwd must never be importable -----------------

    def test_sys_path_output_root_is_not_shadowed_by_planted_scoring_package(self):
        o = self._out("shadow")
        os.makedirs(os.path.join(o, "scoring"))
        sentinel = os.path.join(self.base, "SHADOW_RAN")
        with open(os.path.join(o, "scoring", "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(o, "scoring", "cli.py"), "w") as f:
            f.write(
                "import sys\n"
                f"open({sentinel!r}, 'w').write('x')\n"
                "print('OK: every method block carries paired fidelity+detectability')\n"
                "def main(argv=None):\n"
                "    return 0\n"
            )
        with open(os.path.join(o, "verify.py"), "w") as f:
            f.write(f"open({sentinel!r}, 'w').write('x')\n")

        proc = _run("verify", self.input_root, self.invalid, o)

        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(sentinel),
                          "evaluator imported the fake scoring/ planted in "
                          "output_root -- cwd must never be on sys.path")
        payload = _read_json(o, "verify")
        self.assertEqual(payload["verdict"], "FAIL")

    # -- timeout ---------------------------------------------------------

    def test_timeout_kills_whole_evaluator_process_group_unverified_exit3(self):
        sentinel = os.path.join(self.base, "grandchild_ran")
        grandchild_code = (
            f"import time; time.sleep(1.0); open({sentinel!r}, 'w').close()"
        )
        parent_code = (
            "import subprocess, sys, time\n"
            f"subprocess.Popen([sys.executable, '-c', {grandchild_code!r}])\n"
            "time.sleep(5)\n"
        )
        fake_cmd = [sys.executable, "-c", parent_code]

        o = self._out("timeout")
        os.makedirs(o, exist_ok=True)

        with mock.patch.object(audit_adapter, "_evaluator_cmd",
                                lambda real_input: fake_cmd):
            rc = audit_adapter.main([
                "verify", "--input-root", self.input_root,
                "--input", self.valid, "--output-root", o,
                "--timeout-s", "0.2",
            ])

        self.assertEqual(rc, 3)
        payload = _read_json(o, "verify")
        self.assertEqual(payload["verdict"], "UNVERIFIED")

        # Give the grandchild the time it would have needed to run to
        # completion if only the direct child (and not the whole process
        # group) had been killed.
        time.sleep(1.3)
        self.assertFalse(
            os.path.exists(sentinel),
            "timeout must kill the evaluator's whole process group "
            "(killpg on a start_new_session group), not just the direct child")

    def test_timeout_not_reached_lets_fast_evaluator_pass(self):
        o = self._out("timeout_not_hit")
        proc = _run("verify", self.input_root, self.valid, o, timeout_s="60")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(_read_json(o, "verify")["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
