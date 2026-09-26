"""Link-safety tests for the WS-4 audit adapter (LDCT-03 revision, 210-013).

Stdlib-only (unittest), black-box: drives ``audit_adapter.py`` as a
subprocess for each case, the same way the acceptance checks do. Every case
plants a symlink or a hard link as a receipt file, or a symlinked parent
directory for ``--output-root``, and asserts that the adapter refuses with
exit 2 and leaves all source evidence -- bytes and names, both in the input
root and in the "evidence" directory a symlinked parent could otherwise
reach -- byte-for-byte unchanged. A final control case checks that the
guards do not disable the normal read -> verify -> report path.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WS4_ROOT = os.path.dirname(HERE)
ADAPTER = os.path.join(HERE, "audit_adapter.py")
SCORING_ROOT = os.path.join(WS4_ROOT, "scoring")
FIXTURES = os.path.join(SCORING_ROOT, "tests", "fixtures", "s2_gates")


def _tree_sha(root):
    h = hashlib.sha256()
    for d, dn, fn in sorted(os.walk(root)):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(d, f)
            h.update(os.path.relpath(p, root).encode() + b"\0" +
                      open(p, "rb").read() + b"\0")
    return h.hexdigest()


def _run(op, input_root, input_path, output_root, timeout_s="60"):
    cmd = [sys.executable, "-B", ADAPTER, op,
           "--input-root", input_root, "--input", input_path,
           "--output-root", output_root, "--timeout-s", timeout_s]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


class AuditAdapterLinkSafetyTestCase(unittest.TestCase):
    def setUp(self):
        # realpath: the workspace root itself must be symlink-free, so a
        # quirk of the platform's tempdir (e.g. /tmp being a symlink) is
        # never mistaken for the attack under test.
        self.top = os.path.realpath(tempfile.mkdtemp(prefix="audit_adapter_links_test-"))
        self.addCleanup(shutil.rmtree, self.top, ignore_errors=True)

    def _workspace(self, name):
        w = os.path.join(self.top, name)
        os.mkdir(w)
        input_root = os.path.join(w, "in")
        os.mkdir(input_root)
        shutil.copy(os.path.join(FIXTURES, "provenance_valid.json"),
                    os.path.join(input_root, "valid.json"))
        with open(os.path.join(input_root, "evidence.json"), "w", encoding="utf-8") as f:
            f.write('{"synthetic_source_evidence": "%s"}\n' % name)

        # A pre-existing "evidence dir" that a symlinked --output-root
        # parent could reach; it already holds one receipt per op so the
        # parent-symlink case has something real to (not) disturb.
        evidence_dir = os.path.join(w, "evidence", "run")
        os.makedirs(evidence_dir)
        for op in ("read", "verify", "report"):
            with open(os.path.join(evidence_dir, op + ".json"), "w", encoding="utf-8") as f:
                f.write('{"synthetic_evidence_dir_file": "%s/%s", "verdict": "PASS"}\n' % (name, op))

        out = os.path.join(w, "out")
        os.mkdir(out)
        return w, input_root, out

    def _assert_refused_and_unchanged(self, name, op, plant):
        w, input_root, out = self._workspace(name)
        output_root = plant(w, input_root, out)
        before = (_tree_sha(input_root), _tree_sha(os.path.join(w, "evidence")))
        proc = _run(op, input_root, os.path.join(input_root, "valid.json"), output_root)
        after = (_tree_sha(input_root), _tree_sha(os.path.join(w, "evidence")))
        self.assertEqual(
            proc.returncode, 2,
            f"{name}: expected exit 2, got {proc.returncode}\nstderr:\n{proc.stderr}")
        self.assertEqual(before, after, f"{name}: source evidence changed")

    @staticmethod
    def _symlink_receipt(target_file):
        def plant(w, input_root, out):
            os.symlink(os.path.join(input_root, "evidence.json"),
                       os.path.join(out, target_file))
            return out
        return plant

    @staticmethod
    def _hardlink_receipt(target_file):
        def plant(w, input_root, out):
            os.link(os.path.join(input_root, "evidence.json"),
                     os.path.join(out, target_file))
            return out
        return plant

    @staticmethod
    def _parent_dir_symlink(w, input_root, out):
        os.symlink(os.path.join(w, "evidence"), os.path.join(out, "plink"))
        return os.path.join(out, "plink", "run")

    # -- read -----------------------------------------------------------

    def test_read_output_receipt_symlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "read_symlink", "read", self._symlink_receipt("read.json"))

    def test_read_output_receipt_hardlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "read_hardlink", "read", self._hardlink_receipt("read.json"))

    def test_read_output_root_parent_dir_symlink_exit2(self):
        self._assert_refused_and_unchanged(
            "read_parent", "read", self._parent_dir_symlink)

    # -- verify -----------------------------------------------------------

    def test_verify_output_receipt_symlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "verify_symlink", "verify", self._symlink_receipt("verify.json"))

    def test_verify_output_receipt_hardlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "verify_hardlink", "verify", self._hardlink_receipt("verify.json"))

    def test_verify_output_root_parent_dir_symlink_exit2(self):
        self._assert_refused_and_unchanged(
            "verify_parent", "verify", self._parent_dir_symlink)

    # -- report -----------------------------------------------------------

    def test_report_output_receipt_symlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "report_symlink", "report", self._symlink_receipt("report.json"))

    def test_report_output_receipt_hardlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "report_hardlink", "report", self._hardlink_receipt("report.json"))

    def test_report_output_root_parent_dir_symlink_exit2(self):
        self._assert_refused_and_unchanged(
            "report_parent", "report", self._parent_dir_symlink)

    def test_report_input_verify_json_symlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "report_in_symlink", "report", self._symlink_receipt("verify.json"))

    def test_report_input_verify_json_hardlink_to_source_exit2(self):
        self._assert_refused_and_unchanged(
            "report_in_hardlink", "report", self._hardlink_receipt("verify.json"))

    # -- control: guards must not disable the normal path ------------------

    def test_positive_read_verify_report_still_pass_after_link_guards(self):
        w, input_root, out = self._workspace("positive_ops")
        valid = os.path.join(input_root, "valid.json")
        rc_read = _run("read", input_root, valid, out).returncode
        rc_verify = _run("verify", input_root, valid, out).returncode
        rc_report = _run("report", input_root, valid, out).returncode
        self.assertEqual([rc_read, rc_verify, rc_report], [0, 0, 0])
        with open(os.path.join(out, "report.json"), encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
