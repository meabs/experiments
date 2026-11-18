"""Tests for tasks.py - Feature F11: stats command."""
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


class TestF11Stats(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_stats_fresh_store(self):
        """Fresh store prints zeros."""
        stdout, _, _ = run_task(["stats"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "open: 0")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 0")

    def test_stats_with_tasks(self):
        """Counts correct after adds and done."""
        run_task(["add", "A"], self.tmpdir)
        run_task(["add", "B"], self.tmpdir)
        run_task(["done", "1"], self.tmpdir)
        stdout, _, _ = run_task(["stats"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "open: 1")
        self.assertEqual(lines[1], "done: 1")
        self.assertEqual(lines[2], "total: 2")

    def test_stats_excludes_deleted(self):
        """Deleted tasks are not counted."""
        run_task(["add", "A"], self.tmpdir)
        run_task(["add", "B"], self.tmpdir)
        run_task(["delete", "1"], self.tmpdir)
        stdout, _, _ = run_task(["stats"], self.tmpdir)
        lines = stdout.split("\n")
        self.assertEqual(lines[0], "open: 1")
        self.assertEqual(lines[1], "done: 0")
        self.assertEqual(lines[2], "total: 1")


if __name__ == "__main__":
    unittest.main()
