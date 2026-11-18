"""Tests for tasks.py - Feature F08: edit command."""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(_SCRIPT_DIR, "..", "tasks.py")


def run_task(args, cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    cmd = ["python3", SCRIPT_PATH] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF08Edit(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_edit_replaces_title(self):
        """edit ID --title NEW TITLE replaces the title."""
        run_task(["add", "Old title"], self.tmpdir)
        stdout, _, _ = run_task(["edit", "1", "--title", "New title"], self.tmpdir)
        self.assertEqual(stdout, "Edited 1")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] New title")

    def test_edit_unknown_id_exits_1(self):
        """edit unknown id -> 'No such task: <id>' exit 1."""
        run_task(["add", "Task"], self.tmpdir)
        stdout, stderr, rc = run_task(["edit", "9", "--title", "New"], self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertIn("No such task: 9", stderr)

    def test_edit_multi_word_title(self):
        """edit handles multi-word titles."""
        run_task(["add", "Single word"], self.tmpdir)
        stdout, _, _ = run_task(["edit", "1", "--title", "Multiple words here"], self.tmpdir)
        self.assertEqual(stdout, "Edited 1")
        stdout, _, _ = run_task(["list"], self.tmpdir)
        self.assertEqual(stdout, "1 [ ] Multiple words here")


if __name__ == "__main__":
    unittest.main()
